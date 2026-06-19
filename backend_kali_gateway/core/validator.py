import json
from datetime import datetime

# ==========================================
# MOCK IDENTITY & ACCESS MANAGEMENT (IAM) DB
# ==========================================
# In a production environment, this would connect to Active Directory, 
# RADIUS, or a secure database. For your academic demonstration, 
# an in-memory dictionary is perfect.
AUTHORIZED_USERS = {
    "admin": {
        "password": "admin_password_123",
        "hw_id": "ab12-cd34-ef56-gh78"  # The specific physical Device ID from Flutter
    }
}

# ==========================================
# ZERO TRUST VALIDATION ENGINE
# ==========================================
def validate_payload(decrypted_json_string: str) -> tuple[bool, str]:
    """
    Evaluates the decrypted payload against strict Zero Trust policies.
    Executes a 4-layer Defense in Depth check.
    
    Returns: 
        (is_valid: bool, status_message: str)
    """
    
    # ------------------------------------------
    # Layer 1: Payload Integrity Check
    # ------------------------------------------
    try:
        data = json.loads(decrypted_json_string)
    except json.JSONDecodeError:
        return False, "MALFORMED PAYLOAD (Invalid JSON Structure)"

    username = data.get("user")
    password = data.get("pass")
    hw_id = data.get("hw_id")
    timestamp_str = data.get("timestamp")

    # Ensure no required Zero Trust metrics are missing
    if not all([username, password, hw_id, timestamp_str]):
        return False, "INCOMPLETE METRICS (Missing Zero Trust Data)"

    # ------------------------------------------
    # Layer 2: Replay Attack Prevention (Time Drift)
    # ------------------------------------------
    try:
        # Parse the ISO8601 timestamp sent by the Flutter app
        packet_time = datetime.fromisoformat(timestamp_str)
        current_time = datetime.now()
        
        # Calculate the absolute difference in seconds
        time_diff = abs((current_time - packet_time).total_seconds())
        
        # If the packet is older than 60 seconds, an attacker likely 
        # intercepted it earlier and is trying to reuse it now.
        if time_diff > 60:
            return False, f"REPLAY ATTACK DETECTED (Time drift: {int(time_diff)}s)"
            
    except ValueError:
        return False, "MALFORMED TIMESTAMP (Could not parse ISO8601)"

    # ------------------------------------------
    # Layer 3: Identity & Credential Check
    # ------------------------------------------
    if username not in AUTHORIZED_USERS:
        return False, f"UNAUTHORIZED USER ({username})"
        
    if AUTHORIZED_USERS[username]["password"] != password:
        return False, "INVALID CREDENTIALS"

    # ------------------------------------------
    # Layer 4: Hardware Posture Check (The ZTNA Core)
    # ------------------------------------------
    # This is what makes it ZTNA and not just a standard login.
    # Even if the attacker knows the username and password, the knock 
    # will fail if it does not originate from the authorized physical phone.
    if AUTHORIZED_USERS[username]["hw_id"] != hw_id:
        return False, "HARDWARE MISMATCH (Unrecognized Physical Device)"

    # ------------------------------------------
    # All Security Checks Passed
    # ------------------------------------------
    return True, "ACCESS GRANTED"