import requests
import time
import random
import json
from datetime import datetime

INGEST_URL = "http://127.0.0.1:5001/api/v2/ingest"

def send_log(source, attack_type, severity):
    payload = {
        "log": {
            "source": source,
            "ip": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            "country": random.choice(["USA", "China", "Russia", "Germany", "Kenya"]),
            "raw_data": f"DEMO_LOG: {source} detected {attack_type} event at {datetime.now().isoformat()}",
            "attack": attack_type,
            "severity": severity,
            "risk": 90 if severity == "Critical" else 40,
            "mitre": "T1110",
            "phase": "Initial Access"
        }
    }
    try:
        r = requests.post(INGEST_URL, json=payload, timeout=5)
        print(f"[DEMO] Sent {source} log: {attack_type} ({severity}) - Status: {r.status_code}")
    except Exception as e:
        print(f"[DEMO ERROR] Failed to send {source} log: {e}")

def run_demo_stream():
    providers = [
        ("Fortinet", "SQL Injection", "Critical"),
        ("AzureAD", "Brute Force", "High"),
        ("AWS_CloudTrail", "Unauthorized API Call", "Medium"),
        ("Cloudflare_WAF", "DDoS Peak", "Critical"),
        ("Splunk_Forwarder", "Anomaly Detected", "Low")
    ]
    
    print("🚀 Starting Multi-Provider Demo Stream...")
    for _ in range(2): # Run 2 cycles
        for source, attack, severity in providers:
            send_log(source, attack, severity)
            time.sleep(1)
    print("✅ Demo Stream Complete.")

if __name__ == "__main__":
    run_demo_stream()
