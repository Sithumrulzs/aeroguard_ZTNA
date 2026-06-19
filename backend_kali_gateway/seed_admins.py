"""
One-time script: creates all tables and seeds the 4 network admin accounts.
Run once, then delete.
"""
import sqlite3
import os
from passlib.context import CryptContext

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
DB  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aeroguard_offline.db")

conn = sqlite3.connect(DB)
conn.executescript("""
    CREATE TABLE IF NOT EXISTS admins (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        username       TEXT UNIQUE NOT NULL,
        password_hash  TEXT NOT NULL,
        device_id      TEXT UNIQUE NOT NULL,
        public_key_pem TEXT,
        mac_address    TEXT,
        is_active      INTEGER DEFAULT 1
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

admins = [
    ("KSS Jayamanna",   "sithum.it",  "It@kss69", "admin_kss_jayamanna"),
    ("DS Kalansooriya", "dulshi.it",  "It@ds69",  "admin_ds_kalansooriya"),
    ("SYL Geeganage",   "yasas.it",   "It@syl69", "admin_syl_geeganage"),
    ("ADS Abayarathna", "dulen.it",   "It@ads69", "admin_ads_abayarathna"),
]

for name, username, password, device_id in admins:
    existing = conn.execute(
        "SELECT id FROM admins WHERE username = ?", (username,)
    ).fetchone()
    if existing:
        print(f"[!] Already exists — skipping: {username}")
        continue
    conn.execute(
        "INSERT INTO admins (username, password_hash, device_id, is_active) VALUES (?, ?, ?, 1)",
        (username, pwd.hash(password), device_id),
    )
    print(f"[+] Seeded: {name:20s}  user={username:12s}  device={device_id}")

conn.commit()
conn.close()
print("\n[+] Done. Database ready at:", DB)
