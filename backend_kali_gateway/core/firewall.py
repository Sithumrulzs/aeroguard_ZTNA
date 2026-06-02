import subprocess
from config import WIFI_INTERFACE

def execute_cmd(command: str):
    """Helper to run shell commands safely."""
    try:
        # Use sudo. Note: The Python script running this must have sudo privileges without password,
        # or be run directly as root on the Ubuntu VM.
        subprocess.run(command.split(), check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] Firewall Error executing '{command}': {e.stderr}")
        return False

def open_admin_tunnel(mac_address: str):
    """
    PHASE 2: Admin Workflow
    Opens the firewall completely for the Admin's laptop MAC address, 
    allowing them to reach the WireGuard port and the internal datacenter.
    """
    # 1. Allow this MAC address to reach the Gateway itself (INPUT)
    cmd_input = f"sudo iptables -I INPUT 1 -i {WIFI_INTERFACE} -m mac --mac-source {mac_address} -j ACCEPT"
    execute_cmd(cmd_input)
    
    # 2. Allow this MAC address to route traffic into the core network (FORWARD)
    cmd_forward = f"sudo iptables -I FORWARD 1 -i {WIFI_INTERFACE} -m mac --mac-source {mac_address} -j ACCEPT"
    execute_cmd(cmd_forward)
    
    print(f"[+] Firewall: Full tunnel opened for Admin MAC {mac_address}")

def open_vendor_micro_segment(mac_address: str, target_ip: str, target_port: str = "443"):
    """
    PHASE 3: Vendor Workflow (JIT)
    Strict Micro-segmentation. Only allows the Vendor MAC to hit a single IP/Port.
    """
    # 1. Allow them to reach the Gateway to establish WireGuard (UDP 51820)
    cmd_vpn = f"sudo iptables -I INPUT 1 -i {WIFI_INTERFACE} -m mac --mac-source {mac_address} -p udp --dport 51820 -j ACCEPT"
    execute_cmd(cmd_vpn)
    
    # 2. Restrict their forwarding EXCLUSIVELY to the target server
    cmd_forward = f"sudo iptables -I FORWARD 1 -i {WIFI_INTERFACE} -m mac --mac-source {mac_address} -d {target_ip} -p tcp --dport {target_port} -j ACCEPT"
    execute_cmd(cmd_forward)
    
    print(f"[+] Firewall: JIT Micro-segment opened for Vendor MAC {mac_address} -> {target_ip}:{target_port}")

def close_mac_access(mac_address: str):
    """
    Dynamic teardown. Lists all INPUT and FORWARD rules, finds every rule
    that references the target MAC (regardless of ports or target IPs), converts
    the -A flag to -D, and executes each deletion.
    Handles admin tunnels, JIT vendor micro-segments, and any future rule shapes.
    """
    chains  = ["INPUT", "FORWARD"]
    deleted = 0

    for chain in chains:
        try:
            result = subprocess.run(
                ["sudo", "iptables", "-S", chain],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"[-] Firewall: Could not list {chain} chain: {e.stderr.strip()}")
            continue

        for rule_line in result.stdout.splitlines():
            # Only process lines that reference this MAC
            if mac_address.upper() not in rule_line.upper():
                continue
            # iptables -S output uses -A; swap to -D to build the delete command
            if not rule_line.startswith("-A"):
                continue

            delete_rule = rule_line.replace("-A", "-D", 1)
            try:
                subprocess.run(
                    ["sudo", "iptables"] + delete_rule.split(),
                    capture_output=True,
                    check=True,
                )
                deleted += 1
            except subprocess.CalledProcessError as e:
                # Rule may have already expired — safe to skip
                print(f"[-] Firewall: Could not delete '{delete_rule}': {e.stderr.strip()}")

    if deleted:
        print(f"[!] Firewall: {deleted} rule(s) revoked for MAC {mac_address}. Device in blackhole.")
    else:
        print(f"[!] Firewall: No active rules found for MAC {mac_address} — already clean.")