import socketserver
import argparse
import os
import re
from database import insert_log, init_db

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

def parse_fortinet_syslog(log_line):
    """
    Parses Fortinet Syslog key-value pairs into a dictionary.
    Example: date=2023-11-01 time=12:34:56 devname="FGT" level="warning" srcip=10.0.0.5 msg="Intrusion detected"
    """
    parsed_data = {}
    
    # Use regex to grab key=value pairs (handling quotes securely)
    matches = re.findall(r'(\w+)=(?:\"(.*?)\"|([^ ]+))', log_line)
    for match in matches:
        key = match[0]
        value = match[1] if match[1] else match[2]
        parsed_data[key] = value

    return parsed_data

def process_and_insert(log_line):
    parsed = parse_fortinet_syslog(log_line)
    
    if "srcip" not in parsed:
        return # Skip logs that don't have a source IP to track

    ip_address = parsed.get("srcip", "0.0.0.0")
    level = parsed.get("level", "information").lower()
    risk_level = SEVERITY_MAP.get(level, "Low")
    
    # We only care about Medium/High/Critical events for the SOC dashboard
    if risk_level == "Low":
        return 
        
    event_type = f"Fortinet {parsed.get('subtype', parsed.get('type', 'Firewall Event')).title()}"
    details = parsed.get("msg", "No message provided by firewall")
    
    # Map to V2 Schema: source, ip, country, raw_data, attack, severity, risk, mitre, ai_analysis, remediation, attack_prob, phase
    source = "Fortinet"
    country = "Unknown"
    risk = "High" if risk_level in ["Critical", "High"] else "Medium"
    mitre = "T1190"
    ai_analysis = "Pending analysis"
    remediation = "Pending"
    attack_prob = "100%"
    phase = "Delivery"
    
    insert_log(source, ip_address, country, details, event_type, risk_level, risk, mitre, ai_analysis, remediation, attack_prob, phase)
    print(f"[{risk_level}] Ingested Fortinet Threat from {ip_address}: {event_type}")

class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = bytes.decode(self.request[0].strip(), errors='ignore')
        process_and_insert(data)

def start_syslog_server(host="0.0.0.0", port=5140):
    print(f"🔥 Listening for Live Fortinet Syslogs on UDP {host}:{port}...")
    server = socketserver.UDPServer((host, port), SyslogUDPHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down Syslog Receiver.")

def import_historical_logs(file_path):
    print(f"📦 Importing historical Fortinet logs from: {file_path}")
    if not os.path.exists(file_path):
        print(f"Error: Could not find file {file_path}")
        return

    count = 0
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "srcip=" in line:
                process_and_insert(line)
                count += 1
                
    print(f"✅ Successfully processed {count} historical firewall logs.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CCL Guard - Fortinet Integration Module")
    parser.add_argument("--live", action="store_true", help="Start the live UDP Syslog receiver on Port 5140")
    parser.add_argument("--import-file", type=str, help="Path to a historical Fortinet log file to ingest")
    
    args = parser.parse_args()
    
    # Ensure the database tables exist before importing or listening
    init_db()
    
    if args.import_file:
        import_historical_logs(args.import_file)
    elif args.live:
        start_syslog_server()
    else:
        print("Please specify a mode. Use --live for real-time streaming or --import-file <path> for old logs.")
        print("Run with -h for help.")
