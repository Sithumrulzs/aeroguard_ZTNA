#!/usr/bin/env python3
"""
Device Registration Helper
Quickly register a mobile device's public key to the authorization database.
"""

import sqlite3
import os
import sys

DB_FILE = os.path.join(os.path.dirname(__file__), "aeroguard_offline.db")

def register_device(device_id: str, username: str, public_key: str):
    """Register a device in the authorized_devices table."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT OR REPLACE INTO authorized_devices "
            "(device_id, username, public_key, is_active) "
            "VALUES (?, ?, ?, 1)",
            (device_id, username, public_key),
        )
        conn.commit()
        conn.close()
        
        print(f"[+] Device registered successfully!")
        print(f"    Device ID: {device_id}")
        print(f"    Username:  {username}")
        print(f"    Public Key (first 32 chars): {public_key[:32]}...")
        return True
    except Exception as e:
        print(f"[-] Registration failed: {e}")
        return False

def list_devices():
    """List all registered devices."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM authorized_devices")
        devices = cursor.fetchall()
        conn.close()
        
        if not devices:
            print("[!] No devices registered yet.")
            return
        
        print(f"\n[+] Registered Devices ({len(devices)}):")
        print("-" * 80)
        for device in devices:
            status = "ACTIVE" if device["is_active"] else "REVOKED"
            print(f"  Device: {device['device_id']}")
            print(f"  User:   {device['username']}")
            print(f"  Status: {status}")
            print(f"  Key:    {device['public_key'][:32]}...")
            print()
    except Exception as e:
        print(f"[-] Error listing devices: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python register_device.py register <device_id> <username> <public_key>")
        print("  python register_device.py list")
        print("\nExample:")
        print("  python register_device.py register admin_sithum_it sithum.it 04a1b2c3d4e5f6...")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "register" and len(sys.argv) >= 5:
        device_id = sys.argv[2]
        username = sys.argv[3]
        public_key = sys.argv[4]
        register_device(device_id, username, public_key)
    elif command == "list":
        list_devices()
    else:
        print("[-] Invalid command or missing arguments")
        sys.exit(1)
