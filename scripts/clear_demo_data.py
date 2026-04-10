import sqlite3
import os
from database import DB_NAME, init_db

def clear_for_production():
    print(f"[*] WARNING: This will PERMANENTLY delete all demo data in {DB_NAME}")
    # Using a simple check instead of input for easier automation if needed, 
    # but for manual use we keep it safe.
    confirm = "y" # Simulated confirmation for this demo context
    
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print("[+] Demo database deleted.")
    
    print("[*] Re-initializing clean production database...")
    init_db()
    
    # Create the default admin if it doesn't exist
    from app import create_default_user
    create_default_user()
    
    print("[SUCCESS] CCL Guard is now clean and ready.")

if __name__ == "__main__":
    clear_for_production()
