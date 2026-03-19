import sqlite3
import datetime
import os

PARENT_DB_NAME = os.environ.get("DB_PATH", "parent.db")

def init_parent_db():
    conn = sqlite3.connect(PARENT_DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT UNIQUE,
        url TEXT,
        status TEXT,
        last_seen DATETIME,
        active_incidents INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS blacklist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT UNIQUE,
        time_blacklisted DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()
    print(f"[{PARENT_DB_NAME}] Initialization Complete.")

def register_or_update_client(client_name, url, active_incidents):
    if is_client_blacklisted(client_name):
        return False

    conn = sqlite3.connect(PARENT_DB_NAME)
    cursor = conn.cursor()
    
    # Check if client exists
    cursor.execute("SELECT id FROM clients WHERE client_name=?", (client_name,))
    row = cursor.fetchone()
    
    if row:
        # Check current status
        cursor.execute("SELECT status FROM clients WHERE id=?", (row[0],))
        current_status = cursor.fetchone()[0]
        
        new_status = 'Online' if current_status != 'Disabled' else 'Disabled'
        
        # Update existing
        cursor.execute("""
            UPDATE clients 
            SET url=?, status=?, last_seen=datetime('now', 'localtime'), active_incidents=?
            WHERE client_name=?
        """, (url, new_status, active_incidents, client_name))
    else:
        # Insert new
        cursor.execute("""
            INSERT INTO clients (client_name, url, status, last_seen, active_incidents)
            VALUES (?, ?, 'Online', datetime('now', 'localtime'), ?)
        """, (client_name, url, active_incidents))
        
    conn.commit()
    conn.close()
    return True

def delete_client(client_id):
    conn = sqlite3.connect(PARENT_DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clients WHERE id=?", (client_id,))
    conn.commit()
    conn.close()

def blacklist_client(client_name):
    conn = sqlite3.connect(PARENT_DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO blacklist (client_name) VALUES (?)", (client_name,))
    # Also delete from active clients
    cursor.execute("DELETE FROM clients WHERE client_name=?", (client_name,))
    conn.commit()
    conn.close()

def toggle_client_status(client_id, is_disabled):
    conn = sqlite3.connect(PARENT_DB_NAME)
    cursor = conn.cursor()
    status = 'Disabled' if is_disabled else 'Online'
    cursor.execute("UPDATE clients SET status=? WHERE id=?", (status, client_id))
    conn.commit()
    conn.close()

def is_client_blacklisted(client_name):
    conn = sqlite3.connect(PARENT_DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM blacklist WHERE client_name=?", (client_name,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def unblacklist_client(client_name):
    conn = sqlite3.connect(PARENT_DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM blacklist WHERE client_name=?", (client_name,))
    conn.commit()
    conn.close()

def get_all_clients():
    conn = sqlite3.connect(PARENT_DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, client_name, url, status, last_seen, active_incidents FROM clients ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_parent_db()
