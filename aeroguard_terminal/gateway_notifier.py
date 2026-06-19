"""
gateway_notifier.py
====================
Add ONE call to this file inside your existing backend (main.py)
after a successful knock is verified.

WHERE to add it in your main.py:
---------------------------------
Find the section that logs:
    [+] SIGNATURE VERIFIED. TUNNEL OPEN FOR <phone_ip>.

Right after that, add:
    from gateway_notifier import notify_terminal
    notify_terminal(client_ip=request_ip, username=username)

That's it. The terminal on the operator machine will pop up automatically.
"""

import socket

TERMINAL_PORT = 7000          # Must match TERMINAL_LISTEN_PORT in aeroguard_terminal.py
KNOCK_TOKEN   = "AEROGUARD_VERIFIED"  # Must match KNOCK_TOKEN in aeroguard_terminal.py


def notify_terminal(client_ip: str, username: str = "Verified Operator") -> bool:
    """
    Call this from your gateway after a successful knock verification.
    Sends the signal to the terminal listener on the operator's machine.

    Args:
        client_ip : IP address of the verified operator's workstation
        username  : username from your admins table (e.g. 'sithum.it')

    Returns:
        True if signal sent successfully, False on error.

    Example usage in your main.py:
        from gateway_notifier import notify_terminal
        notify_terminal(client_ip="192.168.1.55", username="sithum.it")
    """
    payload = f"{KNOCK_TOKEN}|{username}"
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((client_ip, TERMINAL_PORT))
        sock.sendall(payload.encode())
        sock.close()
        print(f"[AeroGuard] ✓ Terminal signal sent → {client_ip} | user: {username}")
        return True
    except ConnectionRefusedError:
        print(f"[AeroGuard] Terminal not running on {client_ip}:{TERMINAL_PORT}")
        return False
    except Exception as e:
        print(f"[AeroGuard] Failed to notify terminal: {e}")
        return False


# ── Quick test ──────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    ip   = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    user = sys.argv[2] if len(sys.argv) > 2 else "sithum.it"
    print(f"Sending test signal to {ip} for user '{user}' ...")
    ok = notify_terminal(ip, user)
    print("Sent OK" if ok else "Failed")
