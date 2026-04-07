import socketserver
import argparse
import os
import re
import time
import threading
import requests
import json
from database import insert_logs_batch, init_db, create_incident, DB_NAME

# Map Fortinet severity levels to CCL Guard Risk Levels
SEVERITY_MAP = {
    "emergency": "Critical",
    "alert": "Critical",
    "critical": "Critical",
    "error": "High",
    "warning": "Medium",
    "notice": "Low",
    "information": "Low",
    "debug": "Low"
}

# --- BATCH CONFIG ---
MAX_BUFFER_SIZE = 250
FLUSH_INTERVAL = 5 # seconds
log_buffer = []
buffer_lock = threading.Lock()

remote_url = None
auth_key = None

def parse_fortinet_syslog(log_line):
    parsed_data = {}
    matches = re.findall(r'(\w+)=(?:\"(.*?)\"|([^ ]+))', log_line)
    for match in matches:
        key = match[0]
        value = match[1] if match[1] else match[2]
        parsed_data[key] = value
    return parsed_data

def process_log(log_line):
    """Parses a log and adds it to the global batch buffer."""
    global log_buffer
    parsed = parse_fortinet_syslog(log_line)
    
    if "srcip" not in parsed:
        return False

    ip_address = parsed.get("srcip", "0.0.0.0")
    level = parsed.get("level", "information").lower()
    risk_level = SEVERITY_MAP.get(level, "Low")
    
    event_type = f"Fortinet {parsed.get('subtype', parsed.get('type', 'Firewall Event')).title()}"
    details = parsed.get("msg", "No message provided by firewall")
    
    # Standardized 12-tuple for batch insertion
    log_entry = (
        "Fortinet",
        ip_address,
        parsed.get("dstcountry", "Internal"),
        log_line.strip(),
        event_type,
        risk_level,
        80 if risk_level == "Critical" else 50,
        "T1190",
        details,
        "Verify firewall policy and source IP reputation.",
        90,
        "Delivery"
    )

    with buffer_lock:
        log_buffer.append(log_entry)
        if len(log_buffer) >= MAX_BUFFER_SIZE:
            threading.Thread(target=flush_buffer).start()
    
    return True

def flush_buffer():
    global log_buffer
    with buffer_lock:
        if not log_buffer:
            return
        
        batch = list(log_buffer)
        log_buffer = []

    if remote_url:
        try:
            print(f"☁️ Pushing {len(batch)} logs to Vercel...")
            headers = {"X-CCL-KEY": auth_key, "Content-Type": "application/json"}
            resp = requests.post(f"{remote_url}/api/v2/ingest", headers=headers, json={"logs": batch})
            if resp.status_code != 200:
                print(f"[ERROR] Remote push failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"[ERROR] Remote push failed: {e}")
    else:
        # Local SQLite/Postgres
        insert_logs_batch(batch)

def ticker_flush():
    while True:
        time.sleep(FLUSH_INTERVAL)
        flush_buffer()

class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip().decode('utf-8', errors='ignore')
        process_log(data)

def start_syslog_server(host="0.0.0.0", port=5140):
    print(f"🔥 Listening for Live Fortinet Syslogs on UDP {host}:{port} (BATCH MODE)...")
    
    # Start ticker
    threading.Thread(target=ticker_flush, daemon=True).start()
    
    server = socketserver.UDPServer((host, port), SyslogUDPHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        flush_buffer()
        print("Shutting down Syslog Receiver.")

def import_historical_logs(file_path):
    print(f"📦 Importing historical Fortinet logs from: {file_path}")
    if not os.path.exists(file_path):
        return

    count = 0
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "srcip=" in line:
                if process_log(line):
                    count += 1
    
    flush_buffer() # Final flush
    print(f"✅ Successfully processed {count} firewall logs.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--import-file", type=str)
    parser.add_argument("--remote-url", type=str, help="Vercel App URL (e.g. https://ccl-guard.vercel.app)")
    parser.add_argument("--auth-key", type=str, help="FLASK_SECRET_KEY for authentication")
    args = parser.parse_args()
    
    init_db()
    
    if args.remote_url:
        global remote_url, auth_key
        remote_url = args.remote_url.rstrip("/")
        auth_key = args.auth_key or os.environ.get("FLASK_SECRET_KEY", "ccl_guard_secure_key")
        print(f"🚀 Cloud-Sync Mode Active: Pushing to {remote_url}")

    if args.import_file:
        import_historical_logs(args.import_file)
    elif args.live:
        start_syslog_server()
