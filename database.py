import sqlite3
import os
import datetime
import time

# Configurations
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.environ.get("DB_PATH", os.path.join(_BASE_DIR, "soc.db"))
DATABASE_URL = os.environ.get("DATABASE_URL") # Postgres URL for Vercel/Cloud

def get_connection():
    """Returns a database connection (Postgres, SQLite, or Memory for Demo)."""
    if DATABASE_URL and (DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")):
        try:
            import psycopg2
            url = DATABASE_URL.replace("postgres://", "postgresql://")
            return psycopg2.connect(url)
        except ImportError:
            print("[DB ERROR] psycopg2 not found.")
    
    # Vercel Read-Only Protection: Use memory if no DB_URL is provided in serverless env
    if os.environ.get("VERCEL") == "1" and not DATABASE_URL:
        print("[SOC DEMO] Running in Vercel Memory Mode (Volatile).")
        return sqlite3.connect(":memory:", check_same_thread=False)

    return sqlite3.connect(DB_NAME, timeout=20)

def init_db():
    """Initializes the database schema for both SQLite and Postgres."""
    conn = get_connection()
    c = conn.cursor()
    
    is_pg = (DATABASE_URL and "postgres" in DATABASE_URL)
    auto_inc = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    text_type = "TEXT"
    ts_default = "CURRENT_TIMESTAMP"
    
    # 1. Logs Table
    c.execute(f'''CREATE TABLE IF NOT EXISTS logs (
        id {auto_inc},
        source {text_type},
        ip {text_type},
        country {text_type},
        raw_data {text_type},
        attack {text_type},
        severity {text_type},
        risk INTEGER,
        mitre {text_type},
        ai_analysis {text_type},
        remediation {text_type},
        attack_prob INTEGER,
        phase {text_type},
        time TIMESTAMP DEFAULT {ts_default}
    )''')
    
    # 2. Incidents Table
    c.execute(f'''CREATE TABLE IF NOT EXISTS incidents (
        id {auto_inc},
        attack {text_type},
        severity {text_type},
        risk INTEGER,
        phase {text_type},
        status {text_type} DEFAULT 'Open',
        ai_summary {text_type},
        remediation_steps {text_type},
        source {text_type},
        time TIMESTAMP DEFAULT {ts_default},
        processed_time {text_type},
        closed_time {text_type}
    )''')
    
    # 3. Users Table
    c.execute(f'''CREATE TABLE IF NOT EXISTS users (
        id {auto_inc},
        username {text_type} UNIQUE,
        password {text_type},
        role {text_type},
        is_first_login INTEGER DEFAULT 1
    )''')

    # 4. Indexes for 5M+ scale
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_logs_ip ON logs(ip)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_logs_severity ON logs(severity)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)")
    except Exception as e:
        print(f"[DB WARNING] Index creation skipped: {e}")

    conn.commit()
    conn.close()

# --- INSERT OPERATIONS ---

def insert_log(source, ip, country, raw_data, attack, severity, risk, mitre, ai_analysis, remediation, attack_prob, phase):
    conn = get_connection()
    c = conn.cursor()
    is_pg = (DATABASE_URL and "postgres" in DATABASE_URL)
    p = "%s" if is_pg else "?"
    
    c.execute(f'''INSERT INTO logs (source, ip, country, raw_data, attack, severity, risk, mitre, ai_analysis, remediation, attack_prob, phase)
                  VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})''',
              (source, ip, country, raw_data, attack, severity, risk, mitre, ai_analysis, remediation, attack_prob, phase))
    conn.commit()
    conn.close()

def insert_logs_batch(batch):
    if not batch: return
    conn = get_connection()
    c = conn.cursor()
    is_pg = (DATABASE_URL and "postgres" in DATABASE_URL)
    p = "%s" if is_pg else "?"
    
    c.executemany(f'''INSERT INTO logs (source, ip, country, raw_data, attack, severity, risk, mitre, ai_analysis, remediation, attack_prob, phase)
                  VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})''', batch)
    conn.commit()
    conn.close()

def create_incident(attack, severity, risk, phase, ai_summary, remediation_steps, source="Unknown"):
    conn = get_connection()
    c = conn.cursor()
    is_pg = (DATABASE_URL and "postgres" in DATABASE_URL)
    p = "%s" if is_pg else "?"
    
    c.execute(f'''INSERT INTO incidents (attack, severity, risk, phase, status, ai_summary, remediation_steps, source)
                  VALUES ({p}, {p}, {p}, {p}, 'Open', {p}, {p}, {p})''',
              (attack, severity, risk, phase, ai_summary, remediation_steps, source))
    conn.commit()
    conn.close()

# --- UPDATE OPERATIONS ---

def update_incident_status(incident_id, status):
    conn = get_connection()
    c = conn.cursor()
    is_pg = (DATABASE_URL and "postgres" in DATABASE_URL)
    p = "%s" if is_pg else "?"
    now = datetime.datetime.now().isoformat()
    
    if status == 'In Progress':
        c.execute(f"UPDATE incidents SET status={p}, processed_time={p} WHERE id={p}", (status, now, incident_id))
    elif status == 'Closed':
        c.execute(f"UPDATE incidents SET status={p}, closed_time={p} WHERE id={p}", (status, now, incident_id))
    else:
        c.execute(f"UPDATE incidents SET status={p} WHERE id={p}", (status, incident_id))
    conn.commit()
    conn.close()

# --- FETCH OPERATIONS ---

def get_logs(limit=100):
    conn = get_connection()
    c = conn.cursor()
    c.execute(f"SELECT * FROM logs ORDER BY id DESC LIMIT {limit}")
    rows = c.fetchall()
    colnames = [desc[0] for desc in c.description]
    conn.close()
    return [dict(zip(colnames, row)) for row in rows]

def fetch_incidents(limit=100):
    conn = get_connection()
    c = conn.cursor()
    c.execute(f"SELECT * FROM incidents ORDER BY id DESC LIMIT {limit}")
    rows = c.fetchall()
    colnames = [desc[0] for desc in c.description]
    conn.close()
    return [dict(zip(colnames, row)) for row in rows]

def get_total_logs_count():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM logs")
    count = c.fetchone()[0]
    conn.close()
    return count or 0

def get_incident_stats():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT status, COUNT(*) FROM incidents GROUP BY status")
    stats = dict(c.fetchall())
    conn.close()
    # Ensure keys exist
    return {
        "Open": stats.get("Open", 0),
        "In Progress": stats.get("In Progress", 0),
        "Closed": stats.get("Closed", 0),
        "total": sum(stats.values())
    }
