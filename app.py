from config import Config
from core.database import init_db, insert_log, fetch_logs, get_connection, create_incident, mark_incident_processed, close_incident, connect_with_retry
from core.metrics import calculate_metrics
from core.ai_engine import AIAnalysisEngine
import requests
import sqlite3
import datetime
import smtplib
import subprocess
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from email.mime.text import MIMEText
import os
import threading
import time
import zipfile
import io
import shutil
from collections import Counter
# Matplotlib moved to lazy loading inside functions

ABUSE_API_KEY = os.environ.get("ABUSE_API_KEY") # Keeping some direct lookups if they aren't in Config yet
attack_counter = 0

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Initialization logic
IS_VERCEL = os.environ.get("VERCEL") == "1"

# We use a lazy initialization pattern to replace before_first_request
_initialized = False

@app.before_request
def setup():
    global _initialized
    if not _initialized:
        print("[SOC] Initializing for first request...")
        init_db()
        if not IS_VERCEL:
            # Start remediation worker for local/VPS deployments only
            try:
                from remediation_worker import start_remediation_worker
                threading.Thread(target=start_remediation_worker, daemon=True).start()
            except ImportError:
                print("[WARNING] remediation_worker.py not found.")
        _initialized = True

# ================= EMAIL CONFIG =================
EMAIL_FROM = os.environ.get("EMAIL_FROM") # Optional, keep as environment for now
EMAIL_PASS = os.environ.get("EMAIL_PASS")
EMAIL_TO   = os.environ.get("EMAIL_TO")


def block_ip(ip):
    if ip == "127.0.0.1": return
    try:
        cmd = f'netsh advfirewall firewall add rule name="SOC_Block_{ip}" dir=in action=block remoteip={ip}'
        subprocess.run(cmd, shell=True)
    except: pass

def isolate_host(hostname):
    """Simulated host isolation."""
    print(f"🔒 [SOC CONTAINMENT] Isolating host: {hostname}")
    # In reality: netsh interface set interface "Ethernet" admin=disable
    return True

def suspend_user(username):
    """Simulated user suspension."""
    print(f"🚫 [SOC CONTAINMENT] Suspending user: {username}")
    # In reality: netsh user {username} /active:no
    return True

def block_domain(domain):
    """Simulated domain blocking."""
    print(f"🛡️ [SOC CONTAINMENT] Blocking domain: {domain}")
    # In reality: Update hosts file or DNS sinkhole
    return True



def send_email(subject, body):

    try:
        print("[SOC] Sending email alert...")

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()

        server.login(EMAIL_FROM, EMAIL_PASS)

        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        server.quit()

        print("[SOC] Email sent successfully")

    except Exception as e:
        print("🔥 SOC EMAIL ERROR:", e)


# ================= AI SOC ENGINE V2 =================



def fetch_live_threat_intel():
    """Pulls live indicators from URLHaus (Free Feed)"""
    try:
        print("[SOC] Pulling live threat intelligence...")
        headers = {"User-Agent": "CCL-Guard-SOC-Platform/1.0"}
        r = requests.get("https://urlhaus.abuse.ch/api/v1/urls/recent/", headers=headers, timeout=10)
        
        if r.status_code != 200:
            print(f"[SOC ERROR] URLHaus returned status code {r.status_code}")
            return

        data = r.json()
        if data.get("status") == "ok":
            from core.database import insert_threat_intel
            for item in data.get("urls", [])[:10]:
                source = "URLHaus"
                indicator = item.get("url")
                intel_type = "Malicious URL"
                description = f"Status: {item.get('url_status')}, Tags: {', '.join(item.get('tags', []))}"
                insert_threat_intel(source, indicator, intel_type, description)
            print(f"[SOC] Successfully ingested {len(data.get('urls', []))} live indicators.")
    except Exception as e:
        print(f"[SOC ERROR] Live Intel Pull Failed: {e}")

def generate_mock_intel():
    # Attempt to pull live data
    fetch_live_threat_intel()
    
    from core.database import insert_brand_alert, insert_threat_intel
    
    # Brand Protection Alerts (Keep some mock for demo)
    insert_brand_alert("Domain Squatting", "ccl-agentic-msoc.co", "High-confidence spoofing domain detected.", "High")
    insert_brand_alert("Data Leak", "Internal Registry", "Found exposure on public cloud bucket.", "Critical")

def severity_risk_mitre(attack):
    if "DDoS" in attack: return "Critical", 98, "T1499"
    if "SQL Injection" in attack: return "Critical", 95, "T1190"
    if "Brute Force" in attack: return "High", 85, "T1110"
    if "PortScan" in attack: return "Medium", 60, "T1046"
    return "Low", 10, "N/A"

def attack_phase(attack):
    if "DDoS" in attack: return "Impact"
    if "SQL Injection" in attack: return "Execution"
    if "Brute Force" in attack: return "Initial Access"
    if "PortScan" in attack: return "Recon"
    return "Monitoring"

def geo_lookup(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}").json()
        return r.get("country", "Unknown")
    except:
        return "Unknown"

print("[SOC] V2 Engine Loaded")

print("[SOC] Initializing database")
init_db()

def create_default_user():
    con = get_connection()
    c = con.cursor()
    from werkzeug.security import generate_password_hash
    c.execute("SELECT * FROM users")
    if not c.fetchone():
        c.execute("""
        INSERT INTO users(username,password,role,is_first_login)
        VALUES(?,?,?,1)
        """,("admin",generate_password_hash("admin123"),"admin"))
    con.commit()
    con.close()

create_default_user()

# abuse_lookup is deprecated in V2


@app.route("/")
def dashboard():
    """
    Main SOC Dashboard with real-time analytics.
    """
    if "user" not in session:
        return redirect("/login")
    
    # Pre-define defaults to prevent NameErrors if anything fails
    logs = []
    incidents = []
    threat_feeds = []
    total_attacks = 0
    open_incidents_count = 0
    critical_incidents = 0
    threat_level = "GUARDED"
    threat_color = "var(--success)"
    unique_sources = 0
    unique_countries = 0
    top_ips = []
    metrics = {"mttd": 0, "mtti": 0, "mttr": 0}
    role = session.get("role", "analyst")

    from core.database import fetch_logs, fetch_incidents, fetch_threat_feeds, DB_NAME, connect_with_retry, get_incident_stats
    from core.metrics import calculate_metrics

    print(f"DEBUG: Dashboard route triggered for user: {session.get('user')}")
    try:
        # 1. OPTIMIZED STATUS AGGREGATES (SQL-Side)
        stats = get_incident_stats()
        open_incidents_count = stats["open"]
        critical_incidents = stats["critical"]
        
        # 2. LOAD RECENT SAMPLES (Paginated)
        logs = fetch_logs(limit=10)
        incidents = fetch_incidents(limit=10) # Dashboard only needs a few
        threat_feeds = fetch_threat_feeds()
        
        # Connect for windowed heavy stats
        con = connect_with_retry()
        c = con.cursor()
        
        # 3. Total Detected Attacks (Scanning only ID index is fast)
        c.execute("SELECT MAX(id) FROM logs")
        res = c.fetchone()
        total_attacks = res[0] if res and res[0] else 0
        
        # 4. DATA WINDOWING: Scan last 100,000 logs for heavy statistics
        # This ensures O(1) performance regardless of total volume (e.g. 5M+)
        window_size = 100000
        min_id = max(0, total_attacks - window_size)
        
        # Active Monitoring Sources (Unique IPs in window)
        c.execute("SELECT COUNT(DISTINCT ip) FROM logs WHERE id > ?", (min_id,))
        res = c.fetchone()
        unique_sources = res[0] if res else 0

        # Unique Countries (in window)
        c.execute("SELECT COUNT(DISTINCT country) FROM logs WHERE id > ?", (min_id,))
        res = c.fetchone()
        unique_countries = res[0] if res else 0

        # 5. Top Offending IPs (Windowed for speed)
        c.execute("""
            SELECT ip, COUNT(*) as count 
            FROM logs 
            WHERE id > ? 
            GROUP BY ip 
            ORDER BY count DESC 
            LIMIT 5
        """, (min_id,))
        top_ips_raw = c.fetchall()
        for ip, count in top_ips_raw:
            # Sub-fetch for specific IP is fast due to idx_logs_ip
            c.execute("SELECT severity, COUNT(*) FROM logs WHERE ip = ? AND id > ? GROUP BY severity", (ip, min_id))
            sev_counts = dict(c.fetchall())
            top_ips.append({
                "ip": ip,
                "total": count,
                "high": sev_counts.get("High", 0) + sev_counts.get("Critical", 0),
                "medium": sev_counts.get("Medium", 0),
                "low": sev_counts.get("Low", 0)
            })

        # 6. Global Threat Level Logic
        if critical_incidents > 3:
            threat_level = "CRITICAL"
            threat_color = "var(--danger)"
        elif critical_incidents > 0 or open_incidents_count > 10:
            threat_level = "ELEVATED"
            threat_color = "var(--warning)"
        else:
            threat_level = "GUARDED"
            threat_color = "var(--success)"

        # 7. Investigation Metrics (MTTR/MTTD/MTTI)
        metrics = calculate_metrics()

        con.close()
        
    except Exception as e:
        print(f"🔥 [SOC DASHBOARD DATA FETCH ERROR] {e}")
        import traceback
        traceback.print_exc()
        # We continue with defaults if data fetch fails

    try:
        print(f"DEBUG: Data fetch complete. unique_countries={unique_countries}")
        # Windowing for high-volume logs (Dashboard only scans last 100k for performance)
        window = 100000
        min_id = max(0, (total_attacks or 0) - window)
        
        # Check if this is the first login to show onboarding
        show_onboarding = session.get("is_first_login", 0)

        return render_template("dashboard.html", 
                             logs=logs, 
                             incidents=incidents,
                             threat_feeds=threat_feeds,
                             role=role,
                             total_attacks=total_attacks,
                             unique_sources=unique_sources,
                             unique_countries=unique_countries,
                             threat_level=threat_level,
                             threat_color=threat_color,
                             open_incidents_count=open_incidents_count,
                             critical_incidents=critical_incidents,
                             top_ips=top_ips,
                             metrics=metrics,
                             show_onboarding=show_onboarding)
    except Exception as e:
        print(f"🔥 [SOC DASHBOARD RENDER ERROR] {e}")
        import traceback
        traceback.print_exc()
        return f"Internal Dashboard Error: {e}", 500

# Redundant ingest_logs removed. Consolidated into remote_ingest at Line 900.

@app.route("/predict",methods=["POST"])
def predict():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    try:
        data = request.json
        raw_log = f"Packets: {data.get('packets', 0)}, LoginFail: {data.get('login_fail', 0)}, SQL: {data.get('sql', 0)}"

        # ML-POWERED DETECTION (CIC-IDS2017 Model)
        from core.ml_engine import ml_engine
        attack, confidence = ml_engine.predict(raw_log)
        
        severity, risk, mitre = severity_risk_mitre(attack)
        phase = attack_phase(attack)
        
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        country = data.get("country","Unknown")
        
        # AI-DRIVEN REMEDIATION (Ollama/Gemini)
        try:
            analysis, remediation = AIAnalysisEngine.analyze(attack, severity, "NetworkSensor", ip)
        except Exception as ai_e:
            print(f"🔥 [AI ENGINE ERROR] {ai_e}")
            analysis, remediation = AIAnalysisEngine.get_rule_based_analysis(attack, severity, "NetworkSensor")
        
        from core.database import insert_log, create_incident
        insert_log(
            "NetworkSensor", ip, country, raw_log, 
            f"ML:{attack} ({int(confidence*100)}%)", 
            severity, risk, mitre, analysis, remediation, 
            int(confidence*100), phase
        )
        
        if attack != "BENIGN":
            create_incident(f"ML:{attack}", severity, risk, phase, analysis[:100], remediation, "NetworkSensor", ip)
        
        return jsonify({
            "status": "classified", 
            "attack": attack, 
            "severity": severity,
            "risk": risk,
            "mitre": mitre,
            "analysis": analysis,
            "remediation": remediation,
            "confidence": confidence
        })
    except Exception as e:
        print(f"🔥 [PREDICT ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "status": "failed"}), 500

# INCIDENT PAGE (HTML)
@app.route("/incidents")
def incidents_view():
    if "user" not in session:
        return redirect("/login")
    return render_template("incidents.html", role=session["role"])


# INCIDENT API (JSON)
@app.route("/api/incidents")
def api_incidents():
    from core.database import fetch_incidents
    # Default to last 100 for performance; frontend can request more if needed
    rows = fetch_incidents(limit=100)
    return jsonify(rows)


# MARK INCIDENT AS UNDER INVESTIGATION
@app.route("/api/incident/mark_processed/<int:iid>", methods=["POST"])
def api_mark_processed(iid):
    if "user" not in session: return "Unauthorized", 401
    from core.database import mark_incident_processed
    mark_incident_processed(iid)
    return jsonify({"status": "Incident investigation started"})

# ADVANCED CONTAINMENT API
@app.route("/api/contain/isolate_host", methods=["POST"])
def api_isolate_host():
    if session.get("role") != "admin": return "Forbidden", 403
    data = request.json
    hostname = data.get("hostname")
    if not hostname: return "Missing hostname", 400
    isolate_host(hostname)
    return jsonify({"status": f"Host {hostname} isolated"})

@app.route("/api/contain/suspend_user", methods=["POST"])
def api_suspend_user():
    if session.get("role") != "admin": return "Forbidden", 403
    data = request.json
    username = data.get("username")
    if not username: return "Missing username", 400
    suspend_user(username)
    return jsonify({"status": f"User {username} suspended"})

@app.route("/api/contain/block_domain", methods=["POST"])
def api_block_domain():
    if session.get("role") != "admin": return "Forbidden", 403
    data = request.json
    domain = data.get("domain")
    if not domain: return "Missing domain", 400
    block_domain(domain)
    return jsonify({"status": f"Domain {domain} blocked"})

    return jsonify({"status": "Incident closed successfully"})
@app.route("/attack_count")
def attack_count():
    return jsonify({"count":attack_counter})
init_db()

@app.route("/threat-map")
def threat_map():
    if "user" not in session:
        return redirect("/login")
    return render_template("threat_map.html")

@app.route("/api/network_map_data")
def network_map_data():
    from core.database import get_connection
    con = get_connection()
    c = con.cursor()
    # Pull current active/open incidents with the new attacker_ip field
    c.execute("SELECT id, attack, severity, source, attacker_ip, time FROM incidents WHERE status = 'Open' LIMIT 100")
    rows = c.fetchall()
    colnames = [desc[0] for desc in c.description]
    incidents = [dict(zip(colnames, row)) for row in rows]
    con.close()
    
    nodes_dict = {}
    edges_dict = {}
    
    # Define a static "Security Center" node as the ultimate target (optional, but helps keep the map centered)
    nodes_dict["SOC_CORE"] = {
        "id": "SOC_CORE",
        "label": "SOC HUB",
        "group": "asset",
        "title": "Central Monitoring Engine",
        "value": 5
    }

    for inc in incidents:
        origin = inc.get("attacker_ip", "Unknown")
        target_asset = inc.get("source", "Internal Network")
        attack_type = inc.get("attack", "Unknown")
        severity = inc.get("severity", "Low").lower()
        
        # Threat node (Origin)
        if origin not in nodes_dict:
            nodes_dict[origin] = {
                "id": origin, 
                "label": f"Attacker\n{origin}", 
                "group": "attacker",
                "title": f"Incident #{inc.get('id')} - {attack_type}",
                "value": 1
            }
        else:
            nodes_dict[origin]["value"] += 1
            
        # Target node (The Asset/Sensor that detected it)
        if target_asset not in nodes_dict:
            nodes_dict[target_asset] = {
                "id": target_asset,
                "label": f"Asset\n{target_asset}",
                "group": "asset",
                "title": "Protected Infrastructure"
            }
            
        # Edge definition: Origin (Attacker) -> Target (Asset)
        edge_id = f"{origin}->{target_asset}_{attack_type}"
        if edge_id not in edges_dict:
            color = "#ef4444" if severity in ["critical", "high"] else "#f59e0b"
            edges_dict[edge_id] = {
                "id": edge_id,
                "from": origin,
                "to": target_asset,
                "label": attack_type,
                "color": {"color": color},
                "value": 1
            }
        else:
            edges_dict[edge_id]["value"] += 1
            
        # Also link Asset to SOC HUB for global status
        hub_edge_id = f"{target_asset}->SOC_CORE"
        if hub_edge_id not in edges_dict:
            edges_dict[hub_edge_id] = {
                "id": hub_edge_id,
                "from": target_asset,
                "to": "SOC_CORE",
                "label": "Reporting",
                "color": {"color": "#38bdf8"},
                "value": 1
            }

    return jsonify({
        "nodes": list(nodes_dict.values()),
        "edges": list(edges_dict.values())
    })

@app.route("/history")
def history():

    if "user" not in session:
        return redirect("/login")

    return render_template("history.html")

@app.route("/api/history")
def api_history():
    from core.database import fetch_logs
    # Default to last 100 for safety on high-volume 5M+ tables
    rows = fetch_logs(limit=100)
    return jsonify(rows)

@app.route("/api/log/<int:log_id>")
def api_get_log(log_id):
    from core.database import get_connection
    con = get_connection()
    c = con.cursor()
    c.execute("SELECT * FROM logs WHERE id = ?", (log_id,))
    row = c.fetchone()
    if row:
        colnames = [desc[0] for desc in c.description]
        log_dict = dict(zip(colnames, row))
        con.close()
        return jsonify(log_dict)
    con.close()
    return jsonify({"error": "Log not found"}), 404
# ASSIGN ANALYST + COMMENT
@app.route("/update_incident/<int:iid>", methods=["POST"])
def update_incident(iid):

    from flask import request
    import sqlite3

    analyst = request.form.get("analyst")
    comment = request.form.get("comment")

    conn = get_connection()

    c = conn.cursor()

    c.execute("""
        UPDATE incidents
        SET analyst=?, comment=?
        WHERE id=?
    """,(analyst,comment,iid))

    conn.commit()
    conn.close()

    return "ok"

# APPROVE AI ACTION
@app.route("/approve_incident/<int:iid>", methods=["POST"])
def approve_incident(iid):
    if session.get("role") != "admin": return "Unauthorized", 403
    import sqlite3, datetime
    conn = get_connection()
    c = conn.cursor()
    # Unify to 'Closed' so it appears in Archive and counts in Metrics
    c.execute("UPDATE incidents SET approved_action=1, status='Closed', closed_time=datetime('now') WHERE id=?", (iid,))
    conn.commit()
    conn.close()
    return "ok"

# SUBMIT ANALYST FEEDBACK (Learning Loop)
@app.route("/submit_feedback/<int:iid>", methods=["POST"])
def submit_feedback(iid):
    if session.get("role") != "admin": return "Unauthorized", 403
    data = request.json
    corrections = data.get("feedback", "")
    import sqlite3
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Update incident - Unify to 'Closed' for Archive and Metrics
    c.execute("UPDATE incidents SET approved_action=-1, feedback=?, status='Closed', closed_time=datetime('now') WHERE id=?", (corrections, iid))
    
    # 2. Log feedback for learning
    c.execute("SELECT attack, ai_summary FROM incidents WHERE id=?", (iid,))
    inc = c.fetchone()
    if inc:
        c.execute("INSERT INTO feedback_logs(incident_id, analyst, original_analysis, corrections) VALUES(?,?,?,?)",
                  (iid, session.get("user", "Admin"), inc[1], corrections))
    
    conn.commit()
    conn.close()
    return "ok"

# GENERATE FORENSIC REPORT (Markdown)
@app.route("/api/incident_report/<int:iid>")
def get_incident_report(iid):
    import sqlite3
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM incidents WHERE id=?", (iid,))
    inc = c.fetchone()
    conn.close()
    
    if not inc: return "Incident not found", 404
    
    report = f"""# FORENSIC INCIDENT REPORT: INC-{iid}
**Generated by CCL Guard Agentic SOC**

## 1. Executive Summary
- **Attack Type:** {inc[1]}
- **Severity:** {inc[2]}
- **Initial Discovery:** {inc[11]}
- **Status:** {inc[5]}

## 2. Technical Analysis (AI Forensics)
{inc[9]}

## 3. Autonomous Remediation Plan
{inc[10]}

## 4. Governance & Compliance
- **Analyst Approval:** {"Approved" if inc[8] == 1 else "Pending/Corrected"}
- **Feedback Provided:** {inc[12] or "None"}

---
*Confidential - For Internal Use Only*
"""
    return report, 200, {'Content-Type': 'text/markdown'}

# WHATSAPP INTERACTIVE WEBHOOK (Twilio)
@app.route("/api/whatsapp/webhook", methods=["POST"])
def whatsapp_webhook():
    """Receiver for WhatsApp replies (e.g., ANALYZE, ACTION)."""
    incoming_msg = request.values.get('Body', '').upper()
    sender_number = request.values.get('From', '')
    
    print(f"[WHATSAPP WEBHOOK] Received: {incoming_msg} from {sender_number}")
    
    # Process commands
    response_msg = "Command not recognized."
    if "ANALYZE" in incoming_msg:
        response_msg = "Deep Forensic Analysis triggered. Please check the 'Corrected' tab in the SOC dashboard."
    elif "ACTION" in incoming_msg:
        response_msg = "Autonomous Isolation Action triggered for the target host."
    elif "IGNORE" in incoming_msg:
        response_msg = "Incident suppressed. No further alerts for this host."
    
    # Twilio-specific TwiML response
    from twilio.twiml.messaging_response import MessagingResponse
    resp = MessagingResponse()
    resp.message(response_msg)
    return str(resp)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "ccl-guard-default-secret-key-12345")


@app.route("/api/complete_onboarding", methods=["POST"])
def api_complete_onboarding():
    if "user" not in session: return jsonify({"error": "Unauthorized"}), 401
    
    con = get_connection()
    c = con.cursor()
    c.execute("UPDATE users SET is_first_login = 0 WHERE username = ?", (session["user"],))
    con.commit()
    con.close()
    
    session["is_first_login"] = 0
    return jsonify({"status": "success"})

@app.route('/api/v2/ingest', methods=['POST'])
def remote_ingest():
    """Unified endpoint for both single-log testing and high-volume batch ingestion."""
    data = request.json
    if not data:
        return jsonify({"status": "invalid_data"}), 400

    # 1. Handle Single Log (Testing/Webhooks)
    if 'log' in data:
        try:
            source = data.get("source", "SIEM")
            raw_log = str(data.get("log", ""))
            
            # ML Prediction
            from core.ml_engine import ml_engine
            attack, confidence = ml_engine.predict(raw_log)
            severity, risk, mitre = severity_risk_mitre(attack)
            phase = attack_phase(attack)
            
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            country = geo_lookup(ip)
            
            # Synchronous AI Analysis for immediate feedback
            analysis, remediation = AIAnalysisEngine.analyze(attack, severity, source, ip)
            
            from core.database import insert_log, create_incident
            insert_log(source, ip, country, raw_log, f"ML:{attack}", severity, risk, mitre, analysis, remediation, int(confidence*100), phase)
            
            if attack != "BENIGN":
                create_incident(f"ML:{attack}", severity, risk, phase, analysis[:100], remediation, source, ip)
            
            return jsonify({
                "status": "ingested", 
                "detection_engine": "ML (CIC-IDS2017)",
                "attack": attack, 
                "confidence": confidence,
                "analysis": analysis,
                "remediation": remediation
            })
        except Exception as e:
            return jsonify({"status": "error", "message": f"Single ingestion failed: {e}"}), 500

    # 2. Handle Batch Logs (Fortinet Sync)
    if 'logs' in data:
        auth_key = request.headers.get("X-CCL-KEY")
        if auth_key != app.secret_key:
            return jsonify({"status": "unauthorized"}), 401
        
        try:
            insert_logs_batch(data['logs'])
            return jsonify({"status": "success", "count": len(data['logs'])}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": f"Batch ingestion failed: {e}"}), 500

    return jsonify({"status": "invalid_format", "message": "Request must contain 'log' or 'logs' key."}), 400


@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        u = request.form["username"]
        p = request.form["password"]

        import sqlite3
        con = get_connection()

        c = con.cursor()

        c.execute("SELECT password, role, is_first_login FROM users WHERE username=?", (u,))
        r = c.fetchone()
        con.close()

        if r and check_password_hash(r[0], p):
            session["user"] = u
            session["role"] = r[1]
            session["is_first_login"] = r[2]
            return redirect("/")
        else:
            return "Invalid login"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
# ReportLab moved to lazy loading inside functions
from flask import send_file, redirect
import datetime, sqlite3
@app.route("/testmail")
def testmail():
    send_email("SOC TEST", "This is a test email from your SOC system")
    return "Mail triggered"

@app.route("/report")
def report_dashboard():
    # Lazy imports for PDF generation
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    if "user" not in session:
        return redirect("/login")
    
    import sqlite3, json
    con = get_connection()
    c = con.cursor()
    c.execute("SELECT ip,attack,severity,risk,time FROM logs ORDER BY id DESC LIMIT 25")
    rows = c.fetchall()
    colnames = [desc[0] for desc in c.description]
    logs = [dict(zip(colnames, row)) for row in rows]
    con.close()
    
    # Process data for charts
    severities = [l['severity'] for l in logs]
    sev_count = dict(Counter(severities))
    
    attacks = [l['attack'] for l in logs]
    atk_count = dict(Counter(attacks))
    
    return render_template("reporting.html", 
                           logs=logs, 
                           sev_count_json=json.dumps(dict(sev_count)),
                           atk_count_json=json.dumps(dict(atk_count)))

@app.route("/api/generate_report")
def generate_pdf_report():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, Spacer, Table
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    if "user" not in session:
        return redirect("/login")

    import sqlite3
    con = get_connection()
    c = con.cursor()
    c.execute("SELECT ip,attack,severity,risk,time,ai_analysis,source FROM logs ORDER BY id DESC LIMIT 500")
    rows = c.fetchall()
    colnames = [desc[0] for desc in c.description]
    logs = [dict(zip(colnames, row)) for row in rows]
    con.close()
    
    if not logs:
        return "No alerts found. Please wait for incidents before generating a report.", 400
    
    report_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(report_dir, exist_ok=True)

    # --- generate images for PDF ---
    sev_count = Counter([l['severity'] for l in logs])
    plt.figure()
    plt.pie(sev_count.values(), labels=sev_count.keys(), autopct="%1.1f%%", colors=["red", "orange", "green"])
    plt.title("Severity Distribution")
    plt.savefig(os.path.join(report_dir, "severity.png"))
    plt.close()

    atk_count = Counter([l['attack'] for l in logs])
    top_5_atk = dict(atk_count.most_common(5))
    plt.figure(figsize=(6, 4))
    plt.bar(top_5_atk.keys(), top_5_atk.values(), color="#2563eb")
    plt.xticks(rotation=25, ha="right", fontsize=8)
    plt.title("Top Threat Vectors", fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(report_dir, "attacks.png"))
    plt.close()

    critical_count = len([l for l in logs if l['severity'] in ["High", "Critical"]])
    ai_remediated = len([l for l in logs if l['ai_analysis'] and "Pending" not in l['ai_analysis'] and "Routine" not in l['ai_analysis']])
  
    ips = [l['ip'] for l in logs]
    attacks = [l['attack'] for l in logs]
    risks = [(l['ip'], l['risk']) for l in logs]
    sources = [l['source'] for l in logs]

    top_attack = Counter(attacks).most_common(1)[0][0]
    top_ip = Counter(ips).most_common(1)[0][0]
    top_source = Counter(sources).most_common(1)[0][0]

    highest_risk_ip = max(risks, key=lambda x: x[1])[0] if risks else "N/A"
    highest_risk_score = max((l['risk'] for l in logs), default=0)

    times = [l['time'][:13] if l['time'] else "Unknown" for l in logs]
    peak_time = Counter(times).most_common(1)[0][0] + ":00"

    styles = getSampleStyleSheet()
    
    # Custom heading style
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=24, spaceAfter=20, textColor=colors.HexColor("#0f172a"))
    sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=12, textColor=colors.gray, spaceAfter=20)
    exec_style = ParagraphStyle('ExecStyle', parent=styles['Normal'], fontSize=11, leading=16)

    filename = os.path.join(report_dir, "SOC_Report.pdf")

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )

    elements=[]

    # ===== TITLE =====
    elements.append(Paragraph("<b>CCL Guard Executive Threat Report</b>", title_style))
    elements.append(Paragraph(f"AI-Driven SOC Intelligence & Network Telemetry<br/>Generated: {datetime.datetime.now().strftime('%B %d, %Y at %H:%M')}<br/>Report ID: GUARD-{datetime.datetime.now().strftime('%Y%m%d%H%M')}", sub_style))
    elements.append(Spacer(1,10))
    
    elements.append(Paragraph(f"""
    <b>EXECUTIVE SUMMARY</b><br/>
    This report outlines the threat landscape and automated mitigation actions taken by the CCL Guard AI Orchestrator over the last monitoring period.<br/><br/>
    <b>KEY METRICS & AI TELEMETRY</b><br/>
    • <b>Events Analyzed:</b> {len(logs)}<br/>
    • <b>Critical/High Threats:</b> {critical_count}<br/>
    • <b>AI-Auto Remediated:</b> {ai_remediated} threats intercepted<br/>
    • <b>Top Threat Vector:</b> {top_attack}<br/>
    • <b>Primary Attacker IP:</b> {top_ip}<br/>
    • <b>Highest Risk Target:</b> {highest_risk_ip} (Risk Score: {highest_risk_score}/100)<br/>
    • <b>Peak Attack Window:</b> {peak_time}<br/>
    • <b>Primary Sensor:</b> {top_source}<br/>
    """, exec_style))
    
    elements.append(Spacer(1, 15))

    # Add charts in a table
    img1 = Image(os.path.join(report_dir, "severity.png"), width=220, height=180)
    img2 = Image(os.path.join(report_dir, "attacks.png"), width=280, height=180)
    chart_table = Table([[img1, img2]], colWidths=[240, 300])
    elements.append(chart_table)
    elements.append(Spacer(1,15))

    # ===== TABLE (Top 15) =====
    elements.append(Paragraph("<b>TOP 15 CRITICAL INCIDENTS</b>", styles["Heading3"]))
    table_data=[["Attacker IP", "Attack Type", "Severity", "Risk", "Timestamp/Sensor"]]

    # Sort logs by risk descending
    sorted_logs = sorted(logs, key=lambda x: x[3], reverse=True)[:15]

    for l in sorted_logs:
        sev=l[2]
        badge=f"<font color='red'><b>High</b></font>" if sev in ["High","Critical"] else \
              f"<font color='orange'><b>Medium</b></font>" if sev=="Medium" else \
              f"<font color='green'><b>Low</b></font>"

        table_data.append([
            l[0],
            Paragraph(l[1], styles["Normal"]),
            Paragraph(badge, styles["Normal"]),
            str(l[3]),
            Paragraph(f"{l[4][-8:]}<br/>{l[6]}", styles["Normal"])
        ])

    table=Table(table_data,repeatRows=1,colWidths=[80,140,60,40,110])
    table.setStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0f172a")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONT",(0,0),(-1,0),"Helvetica-Bold"),
        ("ALIGN",(0,0),(-1,-1),"LEFT"),
        ("ALIGN",(2,1),(3,-1),"CENTER"),
        ("GRID",(0,0),(-1,-1),0.5,colors.lightgrey),
        ("BOTTOMPADDING",(0,0),(-1,0),8),
        ("BACKGROUND",(0,1),(-1,-1),colors.whitesmoke)
    ])
    elements.append(table)

    # ================= RECOMMENDATIONS =================
    elements.append(Spacer(1,20))
    elements.append(Paragraph(f"""
    <b>STRATEGIC RECOMMENDATIONS & CISO INSIGHTS</b><br/>
    <br/>
    <b>1. Immediate Containment:</b> Disavow routing for IP `<b>{highest_risk_ip}</b>` and globally drop `<b>{top_ip}</b>` at the edge firewall.<br/>
    <b>2. Vector Hardening:</b> <i>{top_attack}</i> represents the highest volume of inbound attacks. Deploy strict Web Application Firewall (WAF) rate-limiting for this signature type.<br/>
    <b>3. AI Autonomous Mode:</b> The AI Engine successfully audited {ai_remediated} complex incident(s) without human intervention. Ensure your SIEM integrations (AWS, Azure, Fortinet) maintain 100% uptime for continuous coverage.<br/>
    <b>4. Threat Hunting:</b> Review the {critical_count} critical incidents identified above for potential lateral movement across endpoints.<br/>
    """, exec_style))

    elements.append(Spacer(1,30))
    elements.append(Paragraph("""<font color='grey'>Generated securely by CCL Guard Platform | Confidential & Proprietary</font>""",styles["Normal"]))

    doc.build(elements)
    return send_file(filename, as_attachment=True, download_name="CCL_Executive_Report.pdf")




@app.route("/api/v2/analyze_url", methods=["POST"])
def analyze_url():
    data = request.json
    url = data.get("url", "")
    
    # Mock Analysis
    is_malicious = "phish" in url or "verify" in url or ".ru" in url
    analysis = "URL indicates phishing characteristics. Domain registered recently (48h ago)." if is_malicious else "URL appears benign via top-level domain reputation."
    remediation = "1. Block domain at perimeter firewall.\n2. Invalidate active sessions from this referrer.\n3. Trigger global password reset for visited users." if is_malicious else "No action required."
    
    return jsonify({
        "status": "Malicious" if is_malicious else "Safe",
        "analysis": analysis,
        "remediation": remediation
    })

@app.route("/api/v2/analyze_email", methods=["POST"])
def analyze_email():
    data = request.json
    subject = data.get("subject", "")
    
    # Mock Analysis
    is_phishing = "urgent" in subject.lower() or "invoice" in subject.lower()
    analysis = "Email content uses high-pressure tactics and suspicious attachments." if is_phishing else "Email passes basic SPF/DKIM checks."
    remediation = "1. Quarantine message globally.\n2. Scan for malicious attachments.\n3. Alert internal users of active phishing campaign." if is_phishing else "No action required."
    
    return jsonify({
        "status": "Phishing" if is_phishing else "Safe",
        "analysis": analysis,
        "remediation": remediation
    })


# ---------------- UPDATE ENDPOINT (Director Push) ----------------

@app.route("/api/update", methods=["POST"])
def receive_update():
    token = request.headers.get("X-Update-Token")
    if token != "secret-admin-token":
        return jsonify({"error": "Unauthorized"}), 403
    
    if 'update' not in request.files:
        return jsonify({"error": "No update file"}), 400
    
    file = request.files['update']
    try:
        # Save to memory and extract
        with zipfile.ZipFile(io.BytesIO(file.read())) as zf:
            zf.extractall(".")
        
        print(f"[UPDATE] Applied code update from Director at {datetime.datetime.now()}")
        
        # In a real scenario, we might want to restart the process here.
        # For now, we'll just acknowledge.
        return jsonify({"status": "Updated successfully"})
    except Exception as e:
        print(f"[UPDATE ERROR] {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    from core.api_assistant import handle_assistant_query
    from core.hunter import agentic_hunt
    
    @app.route("/api/assistant", methods=["POST"])
    def api_assistant():
        return handle_assistant_query()

    def threat_intel_worker():
        while True:
            try:
                fetch_live_threat_intel()
            except Exception as e:
                print(f"[SOC] Background Threat Intel Error: {e}")
            time.sleep(3600) # Fetch every 1 hour

    def remediation_worker():
        """Processes 'Pending AI' logs from high-volume Fortinet ingestion."""
        while True:
            try:
                con = connect_with_retry()
                c = con.cursor()
                c.execute("SELECT id, attack, severity, source, ip FROM logs WHERE ai_analysis LIKE '%Pending AI%' LIMIT 5")
                pending = c.fetchall()
                con.close()
                
                if not pending:
                    time.sleep(30)
                    continue
                    
                for lid, attack, severity, source, ip in pending:
                    print(f"[*] Async AI Analysis for Log {lid} ({attack})...")
                    analysis, remediation = AIAnalysisEngine.analyze(attack, severity, source, ip)
                    
                    con = connect_with_retry()
                    c = con.cursor()
                    c.execute("UPDATE logs SET ai_analysis=?, remediation=? WHERE id=?", (analysis, remediation, lid))
                    con.commit()
                    con.close()
                    time.sleep(5) # Avoid API rate limits
                
            except Exception as e:
                print(f"[SOC] Remediation Worker Error: {e}")
            time.sleep(10)

    def hunter_worker():
        """Background thread for Agentic Hunter."""
        while True:
            try:
                # Hunt every 30 minutes for reactive-to-proactive parity
                agentic_hunt()
            except Exception as e:
                print(f"[SOC] Hunter Error: {e}")
            time.sleep(1800)  # Wait 30 minutes between hunts
    def parent_heartbeat_worker():
        """Background thread to report status to Parent Dashboard."""
        parent_url = os.environ.get("PARENT_SERVER_URL")
        client_name = os.environ.get("CLIENT_NAME")
        client_url = os.environ.get("CLIENT_PUBLIC_URL")
        
        if not parent_url or not client_name:
            return
            
        while True:
            try:
                # Count active incidents
                con = get_connection()
                c = con.cursor()
                c.execute("SELECT COUNT(*) FROM logs WHERE severity='High' AND risk>=80")
                count = c.fetchone()[0]
                con.close()
                
                payload = {
                    "client_name": client_name,
                    "url": client_url or "http://localhost:5001",
                    "active_incidents": count
                }
                resp = requests.post(f"{parent_url.rstrip('/')}/api/register_child", json=payload, timeout=5)
                if resp.status_code == 403:
                    print(f"🛑 [SOC BLOCKED] This instance has been disabled by the Director.")
                    os.environ["SOC_STATUS"] = "BLOCKED"
            except Exception as e:
                pass # Silent fail for heartbeat
            time.sleep(60) # Ping every minute

@app.route("/close_incident/<int:iid>", methods=["POST"])
def api_close_incident(iid):
    if session.get("role") != "admin": return "Forbidden", 403
    data = request.json
    feedback = data.get("comment", "No feedback provided.")
    from core.database import close_incident
    close_incident(iid, session["user"], feedback)
    return jsonify({"status": "Incident closed and metrics updated"})

if __name__ == "__main__":
    # Start threads
    from api.cloudflare_sync import cloudflare_worker
    from api.aws_sync import aws_worker
    from api.azure_sync import azure_worker
    from api.splunk_sync import splunk_worker
    from core.detection_engineer import detection_engine_worker
    
    print("[SOC] Starting background threads...")
    threading.Thread(target=threat_intel_worker, daemon=True).start()
    threading.Thread(target=hunter_worker, daemon=True).start()
    threading.Thread(target=remediation_worker, daemon=True).start()
    threading.Thread(target=cloudflare_worker, daemon=True).start()
    threading.Thread(target=parent_heartbeat_worker, daemon=True).start()
    threading.Thread(target=aws_worker, daemon=True).start()
    threading.Thread(target=azure_worker, daemon=True).start()
    threading.Thread(target=splunk_worker, daemon=True).start()
    threading.Thread(target=detection_engine_worker, daemon=True).start()

    print(f"[SOC] Initializing Flask - Binding to 0.0.0.0:{Config.CLIENT_PORT}...")
    app.run(host="0.0.0.0", port=Config.CLIENT_PORT)
