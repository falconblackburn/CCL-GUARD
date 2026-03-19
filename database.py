import sqlite3
import datetime
import os
import json

DB_NAME = os.environ.get("DB_PATH", "soc.db")

# ---------------- INIT DATABASE ----------------

import time

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
        source TEXT, -- SIEM, AWS, Windows, etc.
        ip TEXT,
        country TEXT,
        raw_data TEXT, -- Full original log entry
        attack TEXT,
        severity TEXT,
        risk INTEGER,
        mitre TEXT,
        ai_analysis TEXT, -- Deep AI analysis result
        remediation TEXT, -- Step-by-step remediation plan
        attack_prob INTEGER,
        phase TEXT,
        time TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # INCIDENTS (Enhanced for V2)
    c.execute("""
    CREATE TABLE IF NOT EXISTS incidents(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attack TEXT,
        severity TEXT,
        risk INTEGER,
        phase TEXT,
        status TEXT DEFAULT 'Open',
        source TEXT, -- Source of the incident (e.g. Cloudflare, AWS)
        analyst TEXT,
        comment TEXT,
        ai_summary TEXT, -- Concise AI summary
        remediation_steps TEXT, -- Remediation steps for the incident
        approved_action INTEGER DEFAULT 0, -- 0: Pending, 1: Approved, -1: Rejected
        feedback TEXT, -- Analyst feedback/corrections
        report_path TEXT, -- Path to forensic report
        time TEXT,
        processed_time TEXT, -- Time investigation started (for MTTI)
        closed_time TEXT
    )
    """)

    # ANALYST FEEDBACK LOOP (Learning)
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
    """Marks the start of investigation."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE incidents SET processed_time=datetime('now') WHERE id=? AND processed_time IS NULL", (incident_id,))
    conn.commit()
    conn.close()

def close_incident(incident_id, analyst_name, feedback):
    """Closes the incident and sets final timestamps."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        UPDATE incidents 
        SET status='Closed', analyst=?, feedback=?, closed_time=datetime('now')
        WHERE id=?
    """, (analyst_name, feedback, incident_id))
    conn.commit()
    conn.close()




# ---------------- THREAT FEEDS ----------------

def insert_threat_intel(source, indicator, intel_type, description):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO threat_feeds(source, indicator, type, description) VALUES(?,?,?,?)",
              (source, indicator, intel_type, description))
    conn.commit()
    conn.close()


# ---------------- FETCHING ----------------

def fetch_logs(limit=50):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def fetch_incidents():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM incidents ORDER BY id DESC")
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
