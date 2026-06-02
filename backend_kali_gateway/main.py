from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
import bcrypt
import sqlite3
import ecdsa
import hashlib
import json
import os
import subprocess
import uvicorn

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

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

        CREATE TABLE IF NOT EXISTS vendor_sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            token_hash      TEXT UNIQUE NOT NULL,
            vendor_name     TEXT NOT NULL,
            company         TEXT NOT NULL,
            clearance_level TEXT DEFAULT 'standard',
            target_device   TEXT DEFAULT '',
            valid_until     TEXT NOT NULL,
            bound_ip        TEXT DEFAULT '',
            is_active       INTEGER DEFAULT 1,
            created_at      TEXT DEFAULT (datetime('now'))
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

class VendorProvisionPayload(BaseModel):
    token_hash:      str
    vendor_name:     str
    company:         str
    clearance_level: str = "standard"
    target_device:   str = ""
    valid_until:     str  # ISO 8601 UTC e.g. "2026-06-02T18:00:00Z"

class VendorKnockPayload(BaseModel):
    token_hash:  str
    vendor_name: str


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

    # 2. DEVICE LOOKUP (ALIGNED WITH PRODUCTION SCHEMA)
    user_record = execute_db(
        "SELECT public_key_pem, is_active, mac_address FROM admins "
        "WHERE device_id = ? AND username = ?",
        (payload.device_id, payload.username)
    )

    if not user_record:
        log_audit("ADMIN_KNOCK", payload.device_id, "DENIED - UNREGISTERED", client_ip, "No record found")
        raise HTTPException(status_code=403, detail="Device or user not found in Zero Trust vault.")

    # Extract dynamic parameters from the production database row
    db_public_key = user_record[0]["public_key_pem"]
    laptop_mac    = user_record[0]["mac_address"]
    is_active     = user_record[0]["is_active"]

    if not is_active:
        raise HTTPException(status_code=403, detail="Device has been revoked.")

    # 3. CRYPTOGRAPHIC VERIFICATION (WITH DUMMY-KEY FALLBACK FOR DEMO)
    if db_public_key == "dummy_key_until_flutter_is_connected" or not db_public_key:
        print(f"⚠️ [PROVISIONING WARNING] Using initial dummy key for {payload.username}. Verification skipped.")
    else:
        raw_payload_str = f"{payload.device_id}:{payload.username}:{payload.timestamp}"
        is_valid = verify_ecdsa_signature(db_public_key, raw_payload_str, payload.signature)
        if not is_valid:
            log_audit("ADMIN_KNOCK", payload.device_id, "DENIED - SIGNATURE FAILED", client_ip, payload.telemetry)
            raise HTTPException(status_code=403, detail="Cryptographic signature verification failed.")
        print(f"[+] Cryptographic Signature: VALIDATED for {payload.username}")

    # 4. FIREWALL EXECUTION WITH GUEST LAPTOP MAC FALLBACK
    if not laptop_mac or laptop_mac.strip() == "" or "AA:11:22:33:44" in laptop_mac:
        print(f"⚠️ [ZTNA FALLBACK] Laptop MAC not seen. Unblocking via current client IP: {client_ip}")
        subprocess.run(["sudo", "iptables", "-I", "INPUT", "1", "-s", client_ip, "-j", "ACCEPT"],
                       check=False, capture_output=True)
    else:
        print(f"🔒 [ZTNA STRAT] Hardware identity verified. Unblocking laptop MAC: {laptop_mac}")
        subprocess.run(["sudo", "iptables", "-I", "INPUT", "1", "-i", "eth0",
                        "-m", "mac", "--mac-source", laptop_mac, "-j", "ACCEPT"],
                       check=False, capture_output=True)

    log_audit("ADMIN_KNOCK", payload.device_id, "GRANTED", client_ip, payload.telemetry)
    return {"status": "success", "message": "Access granted. Port knocked successfully."}


@app.post("/api/v1/provision-vendor")
async def provision_vendor(payload: VendorProvisionPayload, request: Request):
    """
    Admin endpoint — creates a vendor session with no hardware binding yet.
    The MAC/IP slot is left empty; it gets locked on the vendor's first knock.
    """
    # Validate valid_until is a future timestamp
    try:
        expiry = datetime.fromisoformat(payload.valid_until.replace("Z", "+00:00"))
        if expiry <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="valid_until must be a future timestamp.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid valid_until format. Use ISO 8601 UTC.")

    existing = execute_db(
        "SELECT id FROM vendor_sessions WHERE token_hash = ?",
        (payload.token_hash,)
    )
    if existing:
        raise HTTPException(status_code=409, detail="Token hash already provisioned.")

    execute_db(
        "INSERT INTO vendor_sessions "
        "(token_hash, vendor_name, company, clearance_level, target_device, valid_until, bound_ip, is_active) "
        "VALUES (?, ?, ?, ?, ?, ?, '', 1)",
        (payload.token_hash, payload.vendor_name, payload.company,
         payload.clearance_level, payload.target_device, payload.valid_until)
    )

    log_audit("VENDOR_PROVISION", payload.token_hash, "PROVISIONED",
              request.client.host,
              {"vendor": payload.vendor_name, "company": payload.company,
               "valid_until": payload.valid_until})

    print(f"[+] VENDOR PROVISIONED: {payload.vendor_name} | {payload.company} | expires {payload.valid_until}")
    return {
        "status":  "success",
        "message": f"Vendor session provisioned for {payload.vendor_name}.",
        "valid_until": payload.valid_until,
    }


@app.post("/api/v1/vendor_knock")
async def vendor_knock(payload: VendorKnockPayload, request: Request):
    """
    Trust-on-First-Knock vendor gateway.
    First knock  → binds the client IP to the session and opens the firewall.
    Repeat knock → enforces IP match; rejects any other machine.
    Firewall rule uses iptables -m time --datestop for automatic kernel-level expiry.
    """
    client_ip = request.client.host

    # 1. SESSION LOOKUP
    session = execute_db(
        "SELECT id, vendor_name, company, clearance_level, target_device, "
        "valid_until, bound_ip, is_active "
        "FROM vendor_sessions WHERE token_hash = ? AND is_active = 1",
        (payload.token_hash,)
    )

    if not session:
        log_audit("VENDOR_KNOCK", payload.vendor_name,
                  "DENIED - INVALID TOKEN", client_ip, {"hash": payload.token_hash})
        raise HTTPException(status_code=403, detail="Invalid or inactive vendor token.")

    row         = session[0]
    valid_until = row["valid_until"]
    bound_ip    = row["bound_ip"]

    # 2. SESSION WINDOW CHECK
    try:
        expiry = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expiry:
            execute_db("UPDATE vendor_sessions SET is_active = 0 WHERE token_hash = ?",
                       (payload.token_hash,))
            log_audit("VENDOR_KNOCK", payload.vendor_name,
                      "DENIED - SESSION EXPIRED", client_ip, {"valid_until": valid_until})
            raise HTTPException(status_code=403, detail="Vendor session has expired.")
    except ValueError:
        raise HTTPException(status_code=500, detail="Corrupt session timestamp.")

    # 3. TRUST-ON-FIRST-KNOCK — bind IP on first contact
    if not bound_ip:
        execute_db(
            "UPDATE vendor_sessions SET bound_ip = ? WHERE token_hash = ?",
            (client_ip, payload.token_hash)
        )
        bound_ip = client_ip
        print(f"[+] VENDOR FIRST KNOCK: IP {client_ip} permanently bound to session for {row['vendor_name']}")
    else:
        # 4. HARDWARE ENFORCEMENT — reject any other machine
        if client_ip != bound_ip:
            log_audit("VENDOR_KNOCK", payload.vendor_name,
                      "DENIED - DEVICE MISMATCH", client_ip,
                      {"bound_ip": bound_ip, "attempted_ip": client_ip})
            raise HTTPException(
                status_code=403,
                detail=f"Device mismatch. This session is locked to a different machine."
            )

    # 5. IPTABLES — open firewall with kernel-level time expiry
    datestop = expiry.strftime("%Y-%m-%dT%H:%M:%S")
    subprocess.run(
        ["sudo", "iptables", "-I", "INPUT", "1",
         "-s", client_ip,
         "-m", "time", "--datestop", datestop, "--utc",
         "-j", "ACCEPT"],
        check=False, capture_output=True
    )
    print(f"🔒 [VENDOR TUNNEL] {client_ip} → firewall open until {datestop} UTC")

    log_audit("VENDOR_KNOCK", payload.vendor_name, "GRANTED", client_ip,
              {"company": row["company"], "clearance": row["clearance_level"],
               "bound_ip": client_ip, "valid_until": valid_until})

    return {
        "status":      "success",
        "message":     "Vendor tunnel authorised.",
        "role":        "vendor",
        "vendor_name": row["vendor_name"],
        "company":     row["company"],
        "valid_until": valid_until,
        "bound_ip":    client_ip,
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
        if not verify_password(payload.password, stored_hash):
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
