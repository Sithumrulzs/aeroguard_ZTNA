import subprocess

# Define your WireGuard interface (usually wg0 on Ubuntu)
WG_INTERFACE = "wg0"

def add_vpn_peer(public_key: str, allowed_ip: str):
    """Adds a Vendor/Admin to the active WireGuard interface."""
    cmd = f"sudo wg set {WG_INTERFACE} peer {public_key} allowed-ips {allowed_ip}"
    try:
        subprocess.run(cmd.split(), check=True, capture_output=True)
        print(f"[+] WireGuard: Peer {public_key[:8]}... added.")
    except subprocess.CalledProcessError as e:
        print(f"[-] WireGuard Error: {e.stderr}")

def remove_vpn_peer(public_key: str):
    """Removes a peer when their timer expires."""
    cmd = f"sudo wg set {WG_INTERFACE} peer {public_key} remove"
    subprocess.run(cmd.split(), capture_output=True)
    print(f"[!] WireGuard: Peer {public_key[:8]}... removed.")