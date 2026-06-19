import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature

def verify_signature(public_key_pem: str, signature_b64: str, timestamp: int, device_id: str) -> bool:
    """
    Verifies that the incoming signature was created by the Private Key 
    stored inside the mobile device's Secure Enclave.
    """
    try:
        # 1. Reconstruct the raw payload string that the phone signed
        # (Must exactly match the string format constructed in the Flutter app)
        payload_str = f"{device_id}:{timestamp}"
        
        # 2. Load the Public Key sent in the knock (or fetched from DB)
        public_key = load_pem_public_key(public_key_pem.encode('utf-8'))
        
        # 3. Decode the base64 signature back to bytes
        signature_bytes = base64.b64decode(signature_b64)
        
        # 4. Mathematically verify
        public_key.verify(
            signature_bytes,
            payload_str.encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )
        return True
        
    except InvalidSignature:
        print("[-] Crypto Warning: Signature verification failed. Possible forgery.")
        return False
    except Exception as e:
        print(f"[-] Crypto Error: Malformed key or payload. Details: {e}")
        return False