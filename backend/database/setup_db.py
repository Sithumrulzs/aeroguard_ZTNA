from passlib.context import CryptContext
from database.db_core import SessionLocal, engine, Base
from database.models import Admin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

print("[*] Verifying database tables...")
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# 2. Define your Network Admin Team
# IMPORTANT: The MAC addresses below must belong to the Laptops/Workstations, NOT the phones.
admin_team = [
    {
        "name": "KSS Jayamanna",
        "username": "sithum.it",
        "password": "It@kss69",
        "device_id": "admin_kss_jayamanna",
        "laptop_mac": "AA:11:22:33:44:01" 
    },
    {
        "name": "DS Kalansooriya",
        "username": "dulshi.it",
        "password": "It@ds69",
        "device_id": "admin_ds_kalansooriya",
        "laptop_mac": "AA:11:22:33:44:02"
    },
    {
        "name": "SYL Geeganage",
        "username": "yasas.it",
        "password": "It@syl69",
        "device_id": "admin_syl_geeganage",
        "laptop_mac": "AA:11:22:33:44:03"
    },
    {
        "name": "ADS Abayarathna",
        "username": "dulen.it",
        "password": "It@ads69",
        "device_id": "admin_ads_abayarathna",
        "laptop_mac": "AA:11:22:33:44:04"
    }
]

dummy_public_key = "dummy_key_until_flutter_is_connected"

print("[*] Injecting Network Admin Identities with Laptop Bindings...")

for admin in admin_team:
    existing = db.query(Admin).filter(Admin.username == admin["username"]).first()
    
    if not existing:
        hashed_pw = pwd_context.hash(admin["password"])
        
        new_admin = Admin(
            username=admin["username"],
            password_hash=hashed_pw,
            device_id=admin["device_id"],
            public_key_pem=dummy_public_key,
            mac_address=admin["laptop_mac"], # Injecting the Laptop MAC here
            is_active=True
        )
        db.add(new_admin)
        print(f"[+] Provisioned: {admin['name']} | Bound MAC: {admin['laptop_mac']}")
    else:
        print(f"[!] Skipped: {admin['name']} already exists.")

db.commit()
db.close()
print("[*] Database setup complete. Identities and network hardware are locked.")