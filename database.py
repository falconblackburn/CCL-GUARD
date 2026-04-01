import sqlite3
import datetime
import os
import json
import time

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.environ.get("DB_PATH", os.path.join(_BASE_DIR, "soc.db"))

# ---------------- INIT DATABASE ----------------

def connect_with_retry(timeout=10):
    """Retries connection if database is locked."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10)
            return conn
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                time.sleep(0.5)
                continue
            raise e
    return sqlite3.connect(DB_NAME, timeout=10)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # USERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        role TEXT
    )
    """)

    # LOGS (Enhanced for V2)
    c.execute("""
    CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        ip TEXT,
        country TEXT,
        raw_data TEXT,
        attack TEXT,
        severity TEXT,
        risk INTEGER,
        mitre TEXT,
        ai_analysis TEXT,
        remediation TEXT,
        attack_prob INTEGER,
        phase TEXT,
        time TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # INCIDENTS
    c.execute("""
    CREATE TABLE IF NOT EXISTS incidents(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attack TEXT,
        severity TEXT,
        risk INTEGER,
        phase TEXT,
        status TEXT DEFAULT 'Open',
        source TEXT,
        analyst TEXT,
        comment TEXT,
        ai_summary TEXT,
        remediation_steps TEXT,
        approved_action INTEGER DEFAULT 0,
        feedback TEXT,
        report_path TEXT,
        time TEXT,
        processed_time TEXT,
        closed_time TEXT
    )
    """)

    # FEEDBACK
    c.execute("""
    CREATE TABLE IF NOT EXISTS feedback_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id INTEGER,
        analyst TEXT,
        original_analysis TEXT,
        corrections TEXT,
        time TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # THREAT FEEDS
    c.execute("""
    CREATE TABLE IF NOT EXISTS threat_feeds(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        indicator TEXT,
        type TEXT,
        description TEXT,
        time TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # AUDIT LOG
    c.execute("""
    CREATE TABLE IF NOT EXISTS audit(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        action TEXT,
        time TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Performance Indexes for High Volume (5M+ records)
    c.execute("CREATE INDEX IF NOT EXISTS idx_logs_ip ON logs(ip)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_logs_severity ON logs(severity)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_logs_time ON logs(time)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_logs_country ON logs(country)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_logs_risk ON logs(risk)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity)")

    conn.commit()
    conn.close()

# ---------------- INSERT LOG ----------------

def insert_log(source, ip, country, raw_data, attack, severity, risk, mitre, ai_analysis, remediation, attack_prob, phase):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO logs(
        source, ip, country, raw_data, attack, severity, risk, mitre, ai_analysis, remediation, attack_prob, phase
    )
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
    """, (source, ip, country, raw_data, attack, severity, risk, mitre, ai_analysis, remediation, attack_prob, phase))
    conn.commit()
    conn.close()

def insert_logs_batch(logs_list):
    """Inserts multiple logs in a single transaction for massive performance gain."""
    if not logs_list:
        return
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN")
        cursor.executemany("""
        INSERT INTO logs(
            source, ip, country, raw_data, attack, severity, risk, mitre, ai_analysis, remediation, attack_prob, phase
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """, logs_list)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[DB ERROR] Batch insert failed: {e}")
    finally:
        conn.close()

# ---------------- CREATE INCIDENT ----------------

def create_incident(attack, severity, risk, phase, ai_summary, remediation_steps, source="Unknown"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    INSERT INTO incidents(attack, severity, risk, phase, status, ai_summary, remediation_steps, source, time, processed_time)
    VALUES(?,?,?,?, 'Open', ?, ?, ?, datetime('now'), NULL)
    """, (attack, severity, risk, phase, ai_summary, remediation_steps, source))
    conn.commit()
    conn.close()
    try:
        from notifications import send_incident_alert
        send_incident_alert(attack, severity, source, ai_summary)
    except Exception as e:
        print(f"[DB ERROR] Failed to trigger notification: {e}")

def mark_incident_processed(incident_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE incidents SET processed_time=datetime('now') WHERE id=? AND processed_time IS NULL", (incident_id,))
    conn.commit()
    conn.close()

def close_incident(incident_id, analyst_name, feedback):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        UPDATE incidents 
        SET status='Closed', analyst=?, feedback=?, closed_time=datetime('now')
        WHERE id=?
    """, (analyst_name, feedback, incident_id))
    conn.commit()
    conn.close()

def get_incident_stats():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status='Open' THEN 1 ELSE 0 END) as open_count,
            SUM(CASE WHEN status='Open' AND severity='Critical' THEN 1 ELSE 0 END) as critical_count
        FROM incidents
    """)
    res = c.fetchone()
    conn.close()
    return {
        "total": res[0] or 0,
        "open": res[1] or 0,
        "critical": res[2] or 0
    }

# ---------------- THREAT FEEDS ----------------

def insert_threat_intel(source, indicator, intel_type, description):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO threat_feeds(source, indicator, type, description) VALUES(?,?,?,?)",
              (source, indicator, intel_type, description))
    conn.commit()
    conn.close()

# ---------------- FETCHING ----------------

def fetch_logs(limit=50, offset=0):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
    rows = cursor.fetchall()
    conn.close()
    return rows

def fetch_incidents(limit=100, offset=0):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM incidents ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
    rows = c.fetchall()
    conn.close()
    return rows

def fetch_threat_feeds():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM threat_feeds ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    return rows
