"""
AeroGuard ZTNA — SPA Knock Sniffer
Listens on UDP 7777 via Scapy raw socket (AF_PACKET / libpcap).
Packets are seen even though iptables DROPs them for the normal UDP stack —
this is the core SPA mechanism that makes the gateway invisible to nmap.

Two knock types (distinguished by 'type' field in JSON payload):
  admin_knock  — ECDSA P-256 signature verified against public_key_pem in DB
  vendor_knock — QR token hash validated against vendor_sessions table

On success:
  1. iptables INPUT ACCEPT injected for client_ip → tcp/GATEWAY_PORT
  2. iptables PREROUTING DNAT injected: external tcp/GATEWAY_PORT → 127.0.0.1:GATEWAY_PORT
  3. threading.Timer scheduled to delete both rules on session expiry
"""

import json
import hashlib
import subprocess
import threading
import os
from datetime import datetime, timezone
from contextlib import contextmanager
from dotenv import load_dotenv

import psycopg2
import psycopg2.extras
import ecdsa
from scapy.all import sniff, UDP, IP, Raw

# ── Environment ───────────────────────────────────────────────────────────────
load_dotenv()
DATABASE_URL    = os.getenv("DATABASE_URL")
UDP_KNOCK_PORT  = int(os.getenv("UDP_KNOCK_PORT",       "7777"))
GATEWAY_PORT    = int(os.getenv("PORT",                 "8000"))
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT_SECONDS", "3600"))
IFACE           = os.getenv("GATEWAY_INTERFACE",        "wlan0")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")

# Active sessions: ip → threading.Timer
_timers: dict[str, threading.Timer] = {}
_lock   = threading.Lock()


# ── Database ──────────────────────────────────────────────────────────────────
@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _log(event_type, username, status, ip, details):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO public.audit_logs
                       (event_type, username, client_ip, status, details, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (event_type, username, ip, status,
                     json.dumps(details), datetime.now(timezone.utc).isoformat())
                )
    except Exception as e:
        print(f"[-] Audit log failed: {e}")


# ── Firewall helpers ──────────────────────────────────────────────────────────
def _inject(client_ip: str):
    """Open GATEWAY_PORT for client_ip: INPUT ACCEPT + PREROUTING DNAT to loopback."""
    subprocess.run(
        ["iptables", "-I", "INPUT", "1",
         "-s", client_ip, "-p", "tcp", "--dport", str(GATEWAY_PORT), "-j", "ACCEPT"],
        capture_output=True,
    )
    subprocess.run(
        ["iptables", "-t", "nat", "-I", "PREROUTING", "1",
         "-s", client_ip, "-p", "tcp", "--dport", str(GATEWAY_PORT),
         "-j", "DNAT", "--to-destination", f"127.0.0.1:{GATEWAY_PORT}"],
        capture_output=True,
    )
    print(f"[+] RULES INJECTED  {client_ip} → tcp/{GATEWAY_PORT}")


def _remove(client_ip: str):
    """Delete the INPUT ACCEPT and PREROUTING DNAT rules for client_ip."""
    subprocess.run(
        ["iptables", "-D", "INPUT",
         "-s", client_ip, "-p", "tcp", "--dport", str(GATEWAY_PORT), "-j", "ACCEPT"],
        capture_output=True,
    )
    subprocess.run(
        ["iptables", "-t", "nat", "-D", "PREROUTING",
         "-s", client_ip, "-p", "tcp", "--dport", str(GATEWAY_PORT),
         "-j", "DNAT", "--to-destination", f"127.0.0.1:{GATEWAY_PORT}"],
        capture_output=True,
    )
    print(f"[!] RULES REMOVED   {client_ip} session expired")


def _schedule(client_ip: str, timeout: int, username: str):
    """Cancel any existing timer for this IP and start a fresh expiry timer."""
    with _lock:
        existing = _timers.pop(client_ip, None)
        if existing:
            existing.cancel()

        def _expire():
            _remove(client_ip)
            _log("SESSION_EXPIRED", username, "EXPIRED", client_ip,
                 {"timeout_seconds": timeout})
            with _lock:
                _timers.pop(client_ip, None)

        t = threading.Timer(timeout, _expire)
        t.daemon = True
        t.start()
        _timers[client_ip] = t


# ── ECDSA verification ────────────────────────────────────────────────────────
def _verify_ecdsa(public_key_hex: str, raw_payload: str, signature_hex: str) -> bool:
    try:
        key = bytes.fromhex(public_key_hex)
        # Dart's elliptic package produces 65-byte uncompressed point (04 || X || Y).
        # Python ecdsa wants 64-byte X+Y body only.
        if len(key) == 65 and key[0] == 0x04:
            key = key[1:]
        vk = ecdsa.VerifyingKey.from_string(key, curve=ecdsa.NIST256p)
        h  = hashlib.sha256(raw_payload.encode()).digest()
        try:
            return vk.verify_digest(bytes.fromhex(signature_hex), h)
        except Exception:
            return vk.verify_digest(bytes.fromhex(signature_hex), h,
                                    sigdecode=ecdsa.util.sigdecode_der)
    except Exception as e:
        print(f"[-] ECDSA error: {e}")
        return False


# ── Knock handlers ────────────────────────────────────────────────────────────
def _admin_knock(ip: str, d: dict):
    username  = d.get("username",  "").strip()
    device_id = d.get("device_id", "")
    ts        = d.get("timestamp", "")
    sig       = d.get("signature", "")

    print(f"[*] ADMIN KNOCK   {username} @ {ip}")

    # Anti-replay: reject packets older than 60 seconds
    try:
        age = abs((datetime.now(timezone.utc) -
                   datetime.fromisoformat(ts.replace("Z", "+00:00"))
                   ).total_seconds())
        if age > 60:
            print(f"[-] REPLAY        {username} — {age:.0f}s old")
            _log("ZTNA_KNOCK", username, "DENIED - REPLAY", ip, {"age_seconds": age})
            return
    except Exception:
        print(f"[-] BAD TIMESTAMP {username}")
        return

    # DB lookup
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT public_key_pem, is_active "
                    "FROM public.users WHERE username = %s",
                    (username,)
                )
                user = cur.fetchone()
    except Exception as e:
        print(f"[-] DB error: {e}")
        return

    if not user:
        _log("ZTNA_KNOCK", username, "DENIED - NOT FOUND", ip, {})
        return
    if not user["is_active"]:
        _log("ZTNA_KNOCK", username, "DENIED - INACTIVE", ip, {})
        return

    pub = (user["public_key_pem"] or "").strip()
    if pub in {"dummy_key_until_flutter_is_connected", "dummy_key_until_scanned",
               "manual_admin_provision", "pending", ""}:
        _log("ZTNA_KNOCK", username, "DENIED - NO KEY", ip,
             {"reason": "Device not registered"})
        return

    # ECDSA verification
    if not _verify_ecdsa(pub, f"{device_id}:{username}:{ts}", sig):
        print(f"[-] BAD SIGNATURE {username}")
        _log("ZTNA_KNOCK", username, "DENIED - BAD SIGNATURE", ip,
             {"device_id": device_id})
        return

    _inject(ip)
    _schedule(ip, SESSION_TIMEOUT, username)
    _log("ZTNA_KNOCK", username, "GRANTED", ip,
         {"device_id": device_id, "session_seconds": SESSION_TIMEOUT})
    print(f"[+] GRANTED       {username} — {SESSION_TIMEOUT}s session open")


def _vendor_knock(ip: str, d: dict):
    token_hash  = d.get("token_hash",  "")
    vendor_name = d.get("vendor_name", "")

    print(f"[*] VENDOR KNOCK  {vendor_name} @ {ip}")

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM public.vendor_sessions "
                    "WHERE qr_token = %s AND status NOT IN ('expired', 'revoked')",
                    (token_hash,)
                )
                session = cur.fetchone()
    except Exception as e:
        print(f"[-] DB error: {e}")
        return

    if not session:
        _log("VENDOR_KNOCK", vendor_name, "DENIED - INVALID TOKEN", ip,
             {"hash": token_hash[:16] + "..."})
        return

    try:
        expiry  = datetime.fromisoformat(
            str(session["valid_until"]).replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expiry:
            _log("VENDOR_KNOCK", vendor_name, "DENIED - EXPIRED", ip, {})
            return
        timeout = max(int((expiry - datetime.now(timezone.utc)).total_seconds()), 0)
    except Exception:
        return

    _inject(ip)
    _schedule(ip, timeout, vendor_name)
    _log("VENDOR_KNOCK_SPA", vendor_name, "GRANTED", ip,
         {"company": session["company_name"], "session_seconds": timeout})
    print(f"[+] GRANTED       {vendor_name} — {timeout}s session open")


# ── Scapy packet handler ──────────────────────────────────────────────────────
def _on_packet(pkt):
    if not (IP in pkt and UDP in pkt and Raw in pkt):
        return
    if pkt[UDP].dport != UDP_KNOCK_PORT:
        return

    client_ip = pkt[IP].src
    try:
        data = json.loads(pkt[Raw].load.decode("utf-8", errors="ignore").strip())
    except Exception:
        print(f"[-] Malformed packet from {client_ip}")
        return

    if data.get("type") == "vendor_knock":
        _vendor_knock(client_ip, data)
    else:
        _admin_knock(client_ip, data)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(f"AeroGuard SPA Sniffer  —  UDP {UDP_KNOCK_PORT} on {IFACE}")
    print(f"Gateway port : {GATEWAY_PORT}  |  Session TTL : {SESSION_TIMEOUT}s")
    print("=" * 60 + "\n")
    sniff(
        iface=IFACE,
        filter=f"udp port {UDP_KNOCK_PORT}",
        prn=_on_packet,
        store=False,
    )
