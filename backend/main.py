from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from passlib.context import CryptContext
import sqlite3
import ecdsa
import hashlib
import json
import os
import uvicorn

# Password hashing context (matches setup_db.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="AeroGuard ZTNA Gateway")

# Enable CORS for mobile and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = os.path.join(os.path.dirname(__file__), "aeroguard_offline.db")

# ──────────────────────────────────────────────────────────────────────────────
# STARTUP — create all tables if they don't exist yet
# ──────────────────────────────────────────────────────────────────────────────
@app.on_event("startup")
def initialise_database():
    conn = sqlite3.connect(DB_FILE)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS admins (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            device_id     TEXT UNIQUE NOT NULL,
            public_key_pem TEXT,
            mac_address   TEXT,
            is_active     INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS authorized_devices (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id  TEXT UNIQUE NOT NULL,
            username   TEXT NOT NULL,
            public_key TEXT NOT NULL,
            is_active  INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type  TEXT,
            device_id   TEXT,
            status      TEXT,
            ip_address  TEXT,
            details     TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS vendor_jit_tokens (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            token_hash TEXT UNIQUE NOT NULL,
            is_used    INTEGER DEFAULT 0,
            expires_at TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()
    print("[+] Database tables verified / created.")


# ──────────────────────────────────────────────────────────────────────────────
# PYDANTIC MODELS
# ──────────────────────────────────────────────────────────────────────────────
class LoginPayload(BaseModel):
    username: str
    password: str

class TelemetryPayload(BaseModel):
    device_id: str
    username:  str
    timestamp: str
    signature: str
    telemetry: dict

class VendorPayload(BaseModel):
    qr_hash:   str
    vendor_id: str


# ──────────────────────────────────────────────────────────────────────────────
# DATABASE HELPER
# ──────────────────────────────────────────────────────────────────────────────
def execute_db(query: str, params: tuple = ()):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)

    if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
        conn.commit()
        result = cursor.lastrowid
    else:
        result = cursor.fetchall()

    conn.close()
    return result


# ──────────────────────────────────────────────────────────────────────────────
# CORE ZERO TRUST LOGIC
# ──────────────────────────────────────────────────────────────────────────────
def verify_ecdsa_signature(public_key_hex: str, raw_payload: str,
                            signature_hex: str) -> bool:
    """
    Verifies the payload was signed by the device's Secure Enclave key.
    Flutter signs:  sha256(device_id:username:timestamp)  via toCompactHex()
    """
    try:
        vk = ecdsa.VerifyingKey.from_string(
            bytes.fromhex(public_key_hex), curve=ecdsa.NIST256p
        )
        message_hash = hashlib.sha256(raw_payload.encode("utf-8")).digest()

        # Try compact (r||s) format first — matches Flutter's toCompactHex()
        try:
            return vk.verify_digest(bytes.fromhex(signature_hex), message_hash)
        except Exception:
            # Fallback: DER/ASN.1 format
            return vk.verify_digest(
                bytes.fromhex(signature_hex),
                message_hash,
                sigdecode=ecdsa.util.sigdecode_der,
            )
    except Exception as e:
        print(f"[-] Cryptographic validation failed: {e}")
        return False


def log_audit(event_type: str, device_id: str, status: str,
              ip: str, details: dict):
    execute_db(
        "INSERT INTO audit_logs (event_type, device_id, status, ip_address, details) "
        "VALUES (?, ?, ?, ?, ?)",
        (event_type, device_id, status, ip, json.dumps(details)),
    )


# ──────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/api/v1/knock")
async def admin_knock(payload: TelemetryPayload, request: Request):
    print(f"\n[*] INCOMING ADMIN KNOCK FROM: {payload.username}")
    client_ip = request.client.host

    # 1. ANTI-REPLAY — check timestamp freshness (30-second window)
    # HTTPException must be caught separately so it isn't swallowed by the
    # broad except block.
    try:
        client_time = datetime.fromisoformat(
            payload.timestamp.replace("Z", "+00:00")
        )
        time_diff = abs(
            (datetime.now(timezone.utc) - client_time).total_seconds()
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format.")

    if time_diff > 30:
        log_audit("ADMIN_KNOCK", payload.device_id,
                  "DENIED - REPLAY ATTACK", client_ip, {"time_diff": time_diff})
        raise HTTPException(
            status_code=403, detail="Payload expired — replay attack suspected."
        )

    # 2. DEVICE LOOKUP
    user_record = execute_db(
        "SELECT public_key, is_active FROM authorized_devices "
        "WHERE device_id = ? AND username = ?",
        (payload.device_id, payload.username),
    )

    if not user_record:
        log_audit("ADMIN_KNOCK", payload.device_id,
                  "DENIED - UNREGISTERED", client_ip, payload.telemetry)
        raise HTTPException(
            status_code=403,
            detail="Device or user not found in Zero Trust vault. Register the device public key first.",
        )

    if not user_record[0]["is_active"]:
        log_audit("ADMIN_KNOCK", payload.device_id,
                  "DENIED - REVOKED", client_ip, payload.telemetry)
        raise HTTPException(status_code=403, detail="Device has been revoked.")

    public_key = user_record[0]["public_key"]

    # 3. CRYPTOGRAPHIC VALIDATION
    # Raw string must match exactly what Flutter signed in enclave_service.dart:
    #   '$deviceId:$username:$timestamp'
    raw_payload_str = f"{payload.device_id}:{payload.username}:{payload.timestamp}"
    is_valid = verify_ecdsa_signature(public_key, raw_payload_str, payload.signature)

    if not is_valid:
        log_audit("ADMIN_KNOCK", payload.device_id,
                  "DENIED - SIGNATURE FAILED", client_ip, payload.telemetry)
        raise HTTPException(
            status_code=403, detail="Cryptographic signature verification failed."
        )

    # 4. GRANTED
    log_audit("ADMIN_KNOCK", payload.device_id,
              "GRANTED", client_ip, payload.telemetry)
    print(f"[+] SIGNATURE VERIFIED. TUNNEL OPEN FOR {client_ip}.")

    return {
        "status":     "success",
        "message":    "Gateway secured. Secure tunnel authorised.",
        "session_ip": client_ip,
        "role":       "admin",
    }


@app.post("/api/v1/vendor_knock")
async def vendor_knock(payload: VendorPayload, request: Request):
    client_ip = request.client.host

    token_record = execute_db(
        "SELECT * FROM vendor_jit_tokens "
        "WHERE token_hash = ? AND is_used = 0 AND expires_at > datetime('now')",
        (payload.qr_hash,),
    )

    if not token_record:
        log_audit("VENDOR_KNOCK", payload.vendor_id,
                  "DENIED - INVALID TOKEN", client_ip, {"hash": payload.qr_hash})
        raise HTTPException(
            status_code=403,
            detail="Invalid, expired, or already-used JIT token.",
        )

    execute_db(
        "UPDATE vendor_jit_tokens SET is_used = 1 WHERE token_hash = ?",
        (payload.qr_hash,),
    )
    log_audit("VENDOR_KNOCK", payload.vendor_id,
              "GRANTED", client_ip, {"hash": payload.qr_hash})

    return {
        "status":  "success",
        "message": "Temporary vendor tunnel authorised.",
        "role":    "vendor",
    }


@app.post("/api/v1/login")
async def admin_login(payload: LoginPayload):
    """
    Authenticates an admin user using credentials from the admins table.
    Returns username and device_id on successful authentication.
    """
    try:
        # Query admins table for the user
        admin_record = execute_db(
            "SELECT username, password_hash, device_id FROM admins "
            "WHERE username = ? AND is_active = 1",
            (payload.username,),
        )
        
        if not admin_record:
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password.",
            )
        
        # Verify password hash
        stored_hash = admin_record[0]["password_hash"]
        if not pwd_context.verify(payload.password, stored_hash):
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password.",
            )
        
        # Authentication successful
        print(f"[+] LOGIN SUCCESSFUL: {payload.username}")
        return {
            "status": "success",
            "message": "Authentication successful.",
            "username": admin_record[0]["username"],
            "device_id": admin_record[0]["device_id"],
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[-] Login error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during authentication.",
        )


# ──────────────────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "AeroGuard ZTNA Gateway"}


if __name__ == "__main__":
    print("\n" + "="*70)
    print("AeroGuard ZTNA Gateway Starting")
    print("="*70)
    print(f"Database: {DB_FILE}")
    print("Listen: 0.0.0.0:8000")
    print("CORS: Enabled for all origins (development mode)")
    print("="*70 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
