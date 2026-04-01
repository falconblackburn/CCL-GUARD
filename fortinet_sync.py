import socketserver
import argparse
import os
import re
import time
import threading
from database import insert_logs_batch, init_db, create_incident

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
    
    source = "Fortinet"
    country = "Unknown"
    risk = "High" if risk_level in ["Critical", "High"] else ("Medium" if risk_level == "Medium" else "Low")
    mitre = "T1190"
    
    # NON-BLOCKING AI: High volume logs must have AI performed asynchronously
    if risk_level in ["Critical", "High"]:
        ai_analysis = "Pending AI Analysis (High Volume Mode)"
        remediation = "Pending"
    else:
        ai_analysis = "Routine operational event."
        remediation = "None"
        
    attack_prob = "100%" if risk_level in ["Critical", "High"] else "0%"
    from app import attack_phase # Delayed import to avoid circular dependency
    phase = "Delivery"

    log_entry = (
        source, ip_address, country, details, event_type, 
        risk_level, risk, mitre, ai_analysis, remediation, 
        attack_prob, phase
    )
    
    with buffer_lock:
        log_buffer.append(log_entry)
        if len(log_buffer) >= MAX_BUFFER_SIZE:
            flush_buffer()
            
    return True

def flush_buffer():
    global log_buffer
    with buffer_lock:
        if not log_buffer:
            return
        print(f"[*] Flushing {len(log_buffer)} logs to database...")
        insert_logs_batch(log_buffer)
        log_buffer = []

def ticker_flush():
    """Background thread to flush buffer periodically."""
    while True:
        time.sleep(FLUSH_INTERVAL)
        flush_buffer()

class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = bytes.decode(self.request[0].strip(), errors='ignore')
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
    args = parser.parse_args()
    
    init_db()
    
    if args.import_file:
        import_historical_logs(args.import_file)
    elif args.live:
        start_syslog_server()
