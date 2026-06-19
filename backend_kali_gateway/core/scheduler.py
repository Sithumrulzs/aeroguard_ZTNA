import asyncio
from datetime import datetime
from database.db_core import SessionLocal
from database.models import VendorSession
from core.firewall import close_mac_access

async def auto_kill_monitor():
    """
    Runs continuously in the background. 
    Hunts for expired JIT sessions and executes the network self-destruct.
    """
    print("[*] Auto-Kill Scheduler Initialized...")
    
    while True:
        try:
            db = SessionLocal()
            now = datetime.utcnow()
            
            # Find all sessions that have expired but haven't been revoked yet
            expired_sessions = db.query(VendorSession).filter(
                VendorSession.expires_at <= now,
                VendorSession.is_revoked == False
            ).all()

            for session in expired_sessions:
                # 1. Execute the Linux kernel drop command
                print(f"[!] JIT TIMER EXPIRED: Executing Auto-Kill for MAC {session.mac_address}")
                close_mac_access(session.mac_address)
                
                # 2. Update the database to reflect the termination
                session.is_revoked = True
                db.commit()
                print(f"[-] Session {session.jit_token} securely terminated.")

        except Exception as e:
            print(f"[-] Scheduler Error: {e}")
        finally:
            db.close()
        
        # Pause for 10 seconds before checking again to save CPU
        await asyncio.sleep(10)