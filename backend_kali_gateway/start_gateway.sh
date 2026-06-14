#!/bin/bash
# =============================================================================
#  AeroGuard ZTNA — Gateway Launcher
#  Run this instead of calling main.py directly. It sets dark mode first,
#  then starts the FastAPI gateway so the machine is never exposed without
#  the firewall in place.
#
#      sudo bash start_gateway.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$EUID" -ne 0 ]; then
    echo "[!] Run as root so iptables and the gateway start together:"
    echo "    sudo bash start_gateway.sh"
    exit 1
fi

# Step 1: Lock the network down first — machine is dark before gateway opens
echo "[*] Step 1 — Activating dark mode firewall..."
bash "$SCRIPT_DIR/setup_darkmode.sh"

# Step 2: Start the FastAPI gateway (port 8000 is now the only open port)
echo ""
echo "[*] Step 2 — Starting AeroGuard ZTNA Gateway..."
echo ""
cd "$SCRIPT_DIR"
python main.py
