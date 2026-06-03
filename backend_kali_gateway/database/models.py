from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
try:
    from database.db_core import Base       # when run from backend_kali_gateway/
except ImportError:
    from .db_core import Base               # when imported as a package

class Admin(Base):
    """Stores permanent, hardware-bound identities for Network Admins."""
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True) # e.g., sithum.it
    password_hash = Column(String) # Never store plain text passwords!
    
    device_id = Column(String, unique=True, index=True) # App-generated unique ID
    public_key_pem = Column(String) # The Secure Enclave "Hardware ID"
    mac_address = Column(String, unique=True) # The Admin's Laptop MAC
    is_active = Column(Boolean, default=True)

class VendorSession(Base):
    """Stores JIT rules and rich telemetry for third-party auditing."""
    __tablename__ = "vendor_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    jit_token = Column(String, unique=True, index=True)
    
    # Targeting
    mac_address = Column(String) # Vendor's Laptop MAC
    target_ip = Column(String) 
    
    # Rich Telemetry (Gathered from the mobile app)
    mobile_device_model = Column(String) # e.g., "iPhone 14 Pro" or "Samsung S23"
    connected_ssid = Column(String) # The Wi-Fi network they are knocking from
    knock_timestamp = Column(DateTime, default=func.now()) # Exact server time of knock
    
    # Lifecycle
    expires_at = Column(DateTime)
    is_revoked = Column(Boolean, default=False)