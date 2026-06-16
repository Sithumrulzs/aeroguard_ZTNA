#!/bin/bash
# =============================================================================
#  AeroGuard ZTNA — Gateway Launcher
#  Starts firewall, SPA sniffer, then FastAPI in one command.
#
#      sudo bash start_gateway.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$EUID" -ne 0 ]; then
    echo "[!] Run as root: sudo bash start_gateway.sh"
    exit 1
fi

# Step 1: Apply SPA firewall (dark mode + DNAT support)
echo "[*] Step 1 — Applying SPA firewall..."
bash "$SCRIPT_DIR/setup_darkmode.sh"

# Step 2: Kill any leftover sniffer from a previous run, then start fresh
echo ""
echo "[*] Step 2 — Starting SPA knock sniffer (UDP 7777)..."
pkill -f "spa_sniffer.py" 2>/dev/null && sleep 0.5
"$SCRIPT_DIR/venv/bin/python3" -u "$SCRIPT_DIR/spa_sniffer.py" &
SNIFFER_PID=$!
echo "    sniffer PID: $SNIFFER_PID"

# Brief pause to let the sniffer bind before the gateway starts
sleep 1

# Step 3: Start FastAPI gateway on loopback (reachable only after a verified knock)
echo ""
echo "[*] Step 3 — Starting AeroGuard Gateway (127.0.0.1:8000)..."
echo ""
cd "$SCRIPT_DIR"
"$SCRIPT_DIR/venv/bin/python3" main.py

# If FastAPI exits, kill the sniffer too
kill "$SNIFFER_PID" 2>/dev/null
