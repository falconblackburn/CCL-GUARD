import sqlite3
import os
import datetime

# Configurations
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DB_NAME = os.environ.get("PARENT_DB_PATH", os.path.join(_BASE_DIR, "parent.db"))
DATABASE_URL = os.environ.get("DATABASE_URL") # Same URL or different can be used

def get_parent_connection():
    if DATABASE_URL and (DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")):
        try:
            import psycopg2
            url = DATABASE_URL.replace("postgres://", "postgresql://")
            return psycopg2.connect(url)
        except ImportError:
            print("[PARENT DB] psycopg2 not found. Falling back to SQLite.")
    
    return sqlite3.connect(PARENT_DB_NAME, timeout=20)

def init_parent_db():
    conn = get_parent_connection()
    c = conn.cursor()
    
    is_pg = (DATABASE_URL and "postgres" in DATABASE_URL)
    auto_inc = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    text_type = "TEXT"
    ts_type = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if is_pg else "DATETIME DEFAULT CURRENT_TIMESTAMP"
    
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS clients (
        id {auto_inc},
        client_name {text_type} UNIQUE,
        url {text_type},
        status {text_type},
        last_seen {ts_type},
        active_incidents INTEGER
    )
    """)

    c.execute(f"""
    CREATE TABLE IF NOT EXISTS blacklist (
        id {auto_inc},
        client_name {text_type} UNIQUE,
        time_blacklisted {ts_type}
    )
    """)
    conn.commit()
    conn.close()

def register_or_update_client(client_name, url, active_incidents):
    if is_client_blacklisted(client_name):
        return False

    conn = get_parent_connection()
    c = conn.cursor()
    is_pg = (DATABASE_URL and "postgres" in DATABASE_URL)
    p = "%s" if is_pg else "?"
    now_sql = "CURRENT_TIMESTAMP" if is_pg else "datetime('now', 'localtime')"
    
    # Check if client exists
    c.execute(f"SELECT id FROM clients WHERE client_name={p}", (client_name,))
    row = c.fetchone()
    
    if row:
        c.execute(f"SELECT status FROM clients WHERE id={p}", (row[0],))
        current_status = c.fetchone()[0]
        new_status = 'Online' if current_status != 'Disabled' else 'Disabled'
        
        c.execute(f"""
            UPDATE clients 
            SET url={p}, status={p}, last_seen={now_sql}, active_incidents={p}
            WHERE client_name={p}
        """, (url, new_status, active_incidents, client_name))
    else:
        c.execute(f"""
            INSERT INTO clients (client_name, url, status, last_seen, active_incidents)
            VALUES ({p}, {p}, 'Online', {now_sql}, {p})
        """, (client_name, url, active_incidents))
        
    conn.commit()
    conn.close()
    return True

def delete_client(client_id):
    conn = get_parent_connection()
    c = conn.cursor()
    is_pg = (DATABASE_URL and "postgres" in DATABASE_URL)
    p = "%s" if is_pg else "?"
    c.execute(f"DELETE FROM clients WHERE id={p}", (client_id,))
    conn.commit()
    conn.close()

def blacklist_client(client_name):
    conn = get_parent_connection()
    c = conn.cursor()
    is_pg = (DATABASE_URL and "postgres" in DATABASE_URL)
    p = "%s" if is_pg else "?"
    
    ignore = "ON CONFLICT (client_name) DO NOTHING" if is_pg else "OR IGNORE"
    c.execute(f"INSERT {ignore if not is_pg else ''} INTO blacklist (client_name) VALUES ({p}) {'ON CONFLICT DO NOTHING' if is_pg else ''}", (client_name,))
    c.execute(f"DELETE FROM clients WHERE client_name={p}", (client_name,))
    conn.commit()
    conn.close()

def toggle_client_status(client_id, is_disabled):
    conn = get_parent_connection()
    c = conn.cursor()
    is_pg = (DATABASE_URL and "postgres" in DATABASE_URL)
    p = "%s" if is_pg else "?"
    status = 'Disabled' if is_disabled else 'Online'
    c.execute(f"UPDATE clients SET status={p} WHERE id={p}", (status, client_id))
    conn.commit()
    conn.close()

def is_client_blacklisted(client_name):
    conn = get_parent_connection()
    c = conn.cursor()
    is_pg = (DATABASE_URL and "postgres" in DATABASE_URL)
    p = "%s" if is_pg else "?"
    c.execute(f"SELECT id FROM blacklist WHERE client_name={p}", (client_name,))
    row = c.fetchone()
    conn.close()
    return row is not None

def get_all_clients():
    conn = get_parent_connection()
    c = conn.cursor()
    c.execute("SELECT id, client_name, url, status, last_seen, active_incidents FROM clients ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows
