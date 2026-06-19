"""
One-time script: seeds the 4 network admin identities into the
Supabase PostgreSQL users table.
Run once from backend_kali_gateway/:  python -m database.setup_db
"""
import bcrypt

try:
    from database.db_core import SessionLocal, engine, Base   # run from backend_kali_gateway/
    from database.models import Admin
except ImportError:
    from .db_core import SessionLocal, engine, Base           # imported as a package
    from .models import Admin

print("[*] Verifying database tables...")
Base.metadata.create_all(bind=engine)
db = SessionLocal()

admin_team = [
    {
        "name":       "KSS Jayamanna",
        "username":   "sithum.it",
        "password":   "It@kss69",
        "device_id":  "admin_kss_jayamanna",
        "laptop_mac": "AA:11:22:33:44:01",
    },
    {
        "name":       "DS Kalansooriya",
        "username":   "dulshi.it",
        "password":   "It@ds69",
        "device_id":  "admin_ds_kalansooriya",
        "laptop_mac": "AA:11:22:33:44:02",
    },
    {
        "name":       "SYL Geeganage",
        "username":   "yasas.it",
        "password":   "It@syl69",
        "device_id":  "admin_syl_geeganage",
        "laptop_mac": "AA:11:22:33:44:03",
    },
    {
        "name":       "ADS Abayarathna",
        "username":   "dulen.it",
        "password":   "It@ads69",
        "device_id":  "admin_ads_abayarathna",
        "laptop_mac": "AA:11:22:33:44:04",
    },
]

dummy_public_key = "dummy_key_until_flutter_is_connected"

print("[*] Injecting Network Admin Identities...")

for admin in admin_team:
    existing = db.query(Admin).filter(Admin.username == admin["username"]).first()

    if not existing:
        hashed_pw = bcrypt.hashpw(
            admin["password"].encode(), bcrypt.gensalt()
        ).decode()

        new_admin = Admin(
            username       = admin["username"],
            password_hash  = hashed_pw,
            role           = "admin",
            device_id      = admin["device_id"],
            public_key_pem = dummy_public_key,
            locked_mac     = admin["laptop_mac"],
        )
        db.add(new_admin)
        print(f"[+] Provisioned: {admin['name']} | MAC: {admin['laptop_mac']}")
    else:
        print(f"[!] Skipped: {admin['name']} already exists.")

db.commit()
db.close()
print("[*] Database seeding complete.")
