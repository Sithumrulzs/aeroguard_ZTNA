"""
AeroGuard ZTNA — Central Authentication Server
Handles identity management, device registration, audit queries,
and vendor session provisioning. The Kali gateway defers all
identity decisions to this service.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
import sqlite3
import hashlib
import json
import os
import uvicorn

app = FastAPI(title="AeroGuard Central Auth Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared database — same file as the gateway
DB_FILE = os.path.join(os.path.dirname(__file__), "..", "backend_kali_gateway", "aeroguard_offline.db")


# ──────────────────────────────────────────────────────────────────────────────
# DB HELPER
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
# PYDANTIC MODELS
# ──────────────────────────────────────────────────────────────────────────────
class DeviceRegisterPayload(BaseModel):
    device_id:  str
    username:   str
    public_key: str

class DeviceRevokePayload(BaseModel):
    device_id: str

class VendorProvisionPayload(BaseModel):
    token_hash:      str
    vendor_name:     str
    company:         str
    clearance_level: str = "standard"
    target_device:   str = ""
    valid_until:     str  # ISO 8601 UTC


# ──────────────────────────────────────────────────────────────────────────────
# IDENTITY MANAGEMENT
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/auth/register-device")
async def register_device(payload: DeviceRegisterPayload):
    """Register an admin phone's ECDSA public key."""
    existing = execute_db(
        "SELECT id FROM authorized_devices WHERE device_id = ?",
        (payload.device_id,)
    )
    if existing:
        execute_db(
            "UPDATE authorized_devices SET public_key = ?, is_active = 1 WHERE device_id = ?",
            (payload.public_key, payload.device_id)
        )
        return {"status": "updated", "device_id": payload.device_id}

    execute_db(
        "INSERT INTO authorized_devices (device_id, username, public_key, is_active) VALUES (?, ?, ?, 1)",
        (payload.device_id, payload.username, payload.public_key)
    )
    return {"status": "registered", "device_id": payload.device_id}


@app.post("/auth/revoke-device")
async def revoke_device(payload: DeviceRevokePayload):
    """Revoke an admin device — all future knocks will be denied."""
    execute_db(
        "UPDATE authorized_devices SET is_active = 0 WHERE device_id = ?",
        (payload.device_id,)
    )
    return {"status": "revoked", "device_id": payload.device_id}


@app.get("/auth/devices")
async def list_devices():
    """List all registered devices."""
    rows = execute_db("SELECT device_id, username, is_active FROM authorized_devices")
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────────────────────────────────────
# VENDOR SESSION PROVISIONING
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/auth/provision-vendor")
async def provision_vendor(payload: VendorProvisionPayload):
    """Admin provisions a vendor JIT session."""
    try:
        expiry = datetime.fromisoformat(payload.valid_until.replace("Z", "+00:00"))
        if expiry <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="valid_until must be a future timestamp.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid valid_until format.")

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
    return {
        "status": "provisioned",
        "vendor_name": payload.vendor_name,
        "valid_until": payload.valid_until,
    }


@app.get("/auth/vendor-sessions")
async def list_vendor_sessions():
    """List all vendor sessions."""
    rows = execute_db(
        "SELECT vendor_name, company, clearance_level, valid_until, bound_ip, is_active FROM vendor_sessions"
    )
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────────────────────────────────────
# AUDIT LOG QUERIES
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/auth/audit-logs")
async def get_audit_logs(limit: int = 50):
    """Return the latest audit log entries."""
    rows = execute_db(
        "SELECT event_type, device_id, status, ip_address, details, created_at "
        "FROM audit_logs ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    return [dict(r) for r in rows]


@app.get("/auth/audit-logs/{event_type}")
async def get_audit_logs_by_type(event_type: str, limit: int = 50):
    """Filter audit logs by event type (ADMIN_KNOCK, VENDOR_KNOCK, etc.)."""
    rows = execute_db(
        "SELECT event_type, device_id, status, ip_address, details, created_at "
        "FROM audit_logs WHERE event_type = ? ORDER BY id DESC LIMIT ?",
        (event_type.upper(), limit)
    )
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────────────────────────────────────
# HEALTH
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "AeroGuard Central Auth Server"}


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("AeroGuard Central Auth Server Starting")
    print("=" * 70)
    print(f"Shared DB : {os.path.abspath(DB_FILE)}")
    print("Listen    : 0.0.0.0:8001")
    print("=" * 70 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
