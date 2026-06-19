from scapy.all import sniff, IP, UDP
from config import KNOCK_PORT

def start_gateway_listener(packet_callback):
    """
    Listens silently for incoming UDP packets on the designated knock port.
    Runs continuously in a blocking loop (Headless Mode).
    """
    print(f"[*] AERO-GUARD STEALTH GATEWAY ACTIVE.")
    print(f"[*] Silently monitoring UDP port {KNOCK_PORT}...")
    print("[*] Waiting for encrypted Out-of-Band (OOB) knocks. Press Ctrl+C to exit.\n")
    
    def internal_callback(packet):
        # Double-check that it is a UDP packet aimed at our secret port
        if packet.haslayer(UDP) and packet.haslayer(IP):
            if packet[UDP].dport == KNOCK_PORT:
                
                sender_ip = packet[IP].src
                raw_data = bytes(packet[UDP].payload)
                
                # If the packet contains data, pass it to main.py for decryption
                if raw_data:
                    packet_callback(sender_ip, raw_data)

    # store=0 is critical! It forces Scapy to discard packets from RAM 
    # immediately after processing, preventing your laptop from crashing.
    sniff(filter=f"udp port {KNOCK_PORT}", prn=internal_callback, store=0) 