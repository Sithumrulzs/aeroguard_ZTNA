#!/bin/bash
# =============================================================================
#  AeroGuard ZTNA — Dual-Port SPA Firewall Setup
#
#  Run ONCE as root before starting the gateway:
#      sudo bash setup_darkmode.sh
#
#  Optional overrides:
#      GATEWAY_INTERFACE=eth0  POCKET_SUBNET=10.0.0.0/24  sudo bash setup_darkmode.sh
#
#  What this does:
#    - Drops ALL inbound traffic by default (ping, nmap, SSH — everything)
#    - UDP 7777 and TCP 8000 explicitly dropped (invisible to scanners)
#    - Scapy sniffer still sees UDP 7777 via raw AF_PACKET socket (bypasses netfilter)
#    - Enables route_localnet + MASQUERADE so DNAT → 127.0.0.1:8000 works
#    - After a verified SPA knock, spa_sniffer.py injects per-IP ACCEPT + DNAT rules
# =============================================================================

POCKET_SUBNET="${POCKET_SUBNET:-192.168.100.0/24}"
GATEWAY_IFACE="${GATEWAY_INTERFACE:-wlan0}"
KNOCK_PORT=8000
UDP_PORT=7777

if [ "$EUID" -ne 0 ]; then
    echo "[!] Run as root: sudo bash setup_darkmode.sh"
    exit 1
fi

echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║   AeroGuard ZTNA — SPA Firewall Setup           ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""
echo "  Interface     : $GATEWAY_IFACE"
echo "  Pocket subnet : $POCKET_SUBNET"
echo "  SPA UDP port  : $UDP_PORT"
echo "  Gateway port  : $KNOCK_PORT"
echo ""

# ── 0. Disable ufw — conflicts with manual iptables rules ─────────────────────
if command -v ufw &>/dev/null; then
    if ufw status 2>/dev/null | grep -q "active"; then
        echo "[0/8] Disabling ufw..."
        ufw disable
    else
        echo "[0/8] ufw not active — skipping."
    fi
fi

# ── 1. Flush all tables cleanly ───────────────────────────────────────────────
echo "[1/8] Flushing all iptables rules..."
iptables -F INPUT
iptables -F OUTPUT
iptables -F FORWARD
iptables -t nat    -F 2>/dev/null || true
iptables -t mangle -F 2>/dev/null || true
iptables -t raw    -F 2>/dev/null || true
iptables -X           2>/dev/null || true

# ── 2. Default DROP policy ────────────────────────────────────────────────────
echo "[2/8] Setting default DROP policy..."
iptables -P INPUT   DROP
iptables -P FORWARD DROP
iptables -P OUTPUT  ACCEPT

# ── 3. Loopback — always allow ────────────────────────────────────────────────
echo "[3/8] Allowing loopback..."
iptables -A INPUT -i lo -j ACCEPT

# ── 4. Established/related return traffic ────────────────────────────────────
echo "[4/8] Allowing established/related return packets..."
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# ── 5. Explicit DROP for SPA ports (makes intent visible in iptables -L) ──────
# UDP 7777: Scapy sniffer reads it via raw socket BEFORE netfilter drops it.
# TCP 8000: blocked until spa_sniffer.py injects a per-IP ACCEPT + DNAT rule.
echo "[5/8] Explicitly dropping UDP $UDP_PORT and TCP $KNOCK_PORT..."
iptables -A INPUT -p udp --dport "$UDP_PORT"   -j DROP
iptables -A INPUT -p tcp --dport "$KNOCK_PORT" -j DROP

# ── 6. Enable DNAT → loopback (FastAPI bound to 127.0.0.1) ───────────────────
# route_localnet allows the kernel to route packets destined for 127.x from outside.
# MASQUERADE on lo rewrites source so FastAPI replies are routed back correctly.
echo "[6/8] Enabling DNAT support for loopback (route_localnet + MASQUERADE)..."
sysctl -w net.ipv4.conf.all.route_localnet=1 > /dev/null
iptables -t nat -A POSTROUTING \
    -d 127.0.0.1 -p tcp --dport "$KNOCK_PORT" -j MASQUERADE

# ── 7. Persist route_localnet across reboots ──────────────────────────────────
echo "[7/8] Persisting route_localnet..."
if ! grep -q "net.ipv4.conf.all.route_localnet" /etc/sysctl.conf 2>/dev/null; then
    echo "net.ipv4.conf.all.route_localnet = 1" >> /etc/sysctl.conf
fi

# ── 8. Verify ─────────────────────────────────────────────────────────────────
echo "[8/8] Active INPUT chain:"
iptables -L INPUT -n --line-numbers
echo ""
echo "Active NAT PREROUTING chain:"
iptables -t nat -L PREROUTING -n --line-numbers

echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║   BLACKHOLE ACTIVE — Dual-Port SPA Ready        ║"
echo "  ╠══════════════════════════════════════════════════╣"
echo "  ║  nmap 192.168.100.130  → all ports filtered     ║"
echo "  ║  ping 192.168.100.130  → no reply (DROPPED)     ║"
echo "  ║  UDP 7777              → dropped (sniffer sees) ║"
echo "  ║  TCP 8000              → dropped until knock     ║"
echo "  ║  verified SPA knock    → ACCEPT + DNAT injected  ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""
echo "[*] Ready. Start the gateway:"
echo "    sudo bash start_gateway.sh"
