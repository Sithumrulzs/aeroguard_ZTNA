#!/bin/bash
# =============================================================================
#  AeroGuard ZTNA — Dark Mode Network Setup
#  Run ONCE as root before starting the gateway:
#
#      sudo bash setup_darkmode.sh
#
#  Optional: override the pocket router subnet or interface:
#      POCKET_SUBNET=10.0.0.0/24 WIFI_INTERFACE=eth0 sudo bash setup_darkmode.sh
#
#  What this does:
#    - Drops ALL inbound traffic by default (ping, nmap, SSH — everything)
#    - Opens port 8000 only for devices on the pocket router subnet
#    - Allows Kali's own outbound traffic and return packets
#    - Every other port remains invisible (no response, not even RST)
#
#  After a verified ECDSA knock, main.py injects a timed ACCEPT rule for
#  the phone's IP with a 1-hour datestop. That rule is removed automatically
#  by the iptables time module — no daemon needed.
# =============================================================================

set -e

POCKET_SUBNET="${POCKET_SUBNET:-192.168.100.0/24}"
KNOCK_PORT=8000

# ── Root check ────────────────────────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    echo "[!] This script must be run as root."
    echo "    Usage: sudo bash setup_darkmode.sh"
    exit 1
fi

echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║   AeroGuard ZTNA — Dark Mode Network Setup      ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""
echo "  Pocket subnet : $POCKET_SUBNET"
echo "  Knock port    : $KNOCK_PORT"
echo ""

# ── 1. Flush all existing rules cleanly ───────────────────────────────────────
echo "[1/5] Flushing existing iptables rules..."
iptables -F INPUT
iptables -F OUTPUT
iptables -F FORWARD
iptables -t nat -F  2>/dev/null || true
iptables -X         2>/dev/null || true

# ── 2. Default DROP — the blackhole ───────────────────────────────────────────
echo "[2/5] Setting default DROP policy (blackhole)..."
iptables -P INPUT   DROP
iptables -P FORWARD DROP
iptables -P OUTPUT  ACCEPT    # Kali's own outbound is always allowed

# ── 3. Loopback — localhost must always work ───────────────────────────────────
echo "[3/5] Allowing loopback..."
iptables -A INPUT -i lo -j ACCEPT

# ── 4. Return traffic for Kali's own outbound connections ─────────────────────
echo "[4/5] Allowing established/related return packets..."
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# ── 5. Knock endpoint — subnet-restricted only ────────────────────────────────
# Devices outside the pocket router network cannot even reach this port.
# Devices on the pocket router WiFi can reach port 8000, but main.py
# will reject any request that does not carry a valid ECDSA signature.
echo "[5/5] Opening knock endpoint (port $KNOCK_PORT) for $POCKET_SUBNET..."
iptables -A INPUT -p tcp --dport "$KNOCK_PORT" -s "$POCKET_SUBNET" -j ACCEPT

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║   BLACKHOLE ACTIVE — Gateway is now invisible    ║"
echo "  ╠══════════════════════════════════════════════════╣"
echo "  ║  ping 192.168.100.130    → no reply (DROPPED)   ║"
echo "  ║  nmap 192.168.100.130    → all ports filtered    ║"
echo "  ║  port 8000 (inside WiFi) → open for knock only   ║"
echo "  ║  unsigned knock attempt  → 403 (ECDSA rejected)  ║"
echo "  ║  verified knock          → timed ACCEPT +1 hour  ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""
echo "Active INPUT rules:"
iptables -L INPUT -n --line-numbers
echo ""
echo "[*] Dark mode ready. Start the gateway:"
echo "    cd backend_kali_gateway && python main.py"
