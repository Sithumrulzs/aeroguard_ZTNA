import subprocess
import os

# Network interface the gateway listens on.
# Override with the WIFI_INTERFACE env var on the Kali machine if needed.
WIFI_INTERFACE: str = os.environ.get("WIFI_INTERFACE", "wlan0")


def _run(args: list[str]) -> bool:
    """Execute an iptables command safely using a pre-split argument list."""
    try:
        subprocess.run(args, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] Firewall error: {' '.join(args)}\n    {e.stderr.strip()}")
        return False


def open_admin_tunnel(mac_address: str) -> None:
    """
    Admin workflow — opens the firewall for the admin's laptop MAC address,
    granting full access to the gateway and internal datacenter.
    """
    _run(["sudo", "iptables", "-I", "INPUT",   "1",
          "-i", WIFI_INTERFACE, "-m", "mac", "--mac-source", mac_address, "-j", "ACCEPT"])
    _run(["sudo", "iptables", "-I", "FORWARD", "1",
          "-i", WIFI_INTERFACE, "-m", "mac", "--mac-source", mac_address, "-j", "ACCEPT"])
    print(f"[+] Firewall: Admin tunnel opened for MAC {mac_address}")


def open_vendor_micro_segment(mac_address: str, target_ip: str,
                               target_port: str = "443") -> None:
    """
    Vendor JIT workflow — strict micro-segmentation.
    Only allows the vendor MAC to reach a single IP:Port.
    """
    # Allow WireGuard handshake (UDP 51820)
    _run(["sudo", "iptables", "-I", "INPUT", "1",
          "-i", WIFI_INTERFACE, "-m", "mac", "--mac-source", mac_address,
          "-p", "udp", "--dport", "51820", "-j", "ACCEPT"])

    # Restrict forwarding exclusively to the target resource
    _run(["sudo", "iptables", "-I", "FORWARD", "1",
          "-i", WIFI_INTERFACE, "-m", "mac", "--mac-source", mac_address,
          "-d", target_ip, "-p", "tcp", "--dport", target_port, "-j", "ACCEPT"])

    print(f"[+] Firewall: Vendor micro-segment opened — {mac_address} → {target_ip}:{target_port}")


def close_mac_access(mac_address: str) -> None:
    """
    Tear down all INPUT and FORWARD rules that reference the given MAC address.
    Handles admin tunnels, vendor micro-segments, and any future rule shapes.
    """
    chains  = ["INPUT", "FORWARD"]
    deleted = 0

    for chain in chains:
        try:
            result = subprocess.run(
                ["sudo", "iptables", "-S", chain],
                capture_output=True, text=True, check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"[-] Firewall: Could not list {chain} chain: {e.stderr.strip()}")
            continue

        for rule_line in result.stdout.splitlines():
            if mac_address.upper() not in rule_line.upper():
                continue
            if not rule_line.startswith("-A"):
                continue

            # Swap -A for -D to build the deletion command
            delete_args = ["sudo", "iptables"] + rule_line.replace("-A", "-D", 1).split()
            try:
                subprocess.run(delete_args, capture_output=True, check=True)
                deleted += 1
            except subprocess.CalledProcessError as e:
                print(f"[-] Firewall: Could not delete rule: {e.stderr.strip()}")

    if deleted:
        print(f"[!] Firewall: {deleted} rule(s) revoked for {mac_address}. Device in blackhole.")
    else:
        print(f"[!] Firewall: No active rules found for {mac_address} — already clean.")
