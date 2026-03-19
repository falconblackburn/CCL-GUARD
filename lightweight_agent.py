import requests
import socket
import time
import os
import json

# ==========================================
# CCL Agentic MSOC - Lightweight Ingestion Agent
# ==========================================
# CONFIGURATION: Update these before sending to client
SOC_INGEST_URL = "http://localhost:5001/api/v2/ingest" 
SOURCE_NAME = socket.gethostname()
POLL_INTERVAL = 10 # Seconds

def monitor_events():
    """
    Monitors local system events and forwards them to the CCL Agentic MSOC.
    For production, this can be extended to watch /var/log/auth.log or Event Viewer.
    """
    print(f"[*] CCL Agentic MSOC Agent started on {SOURCE_NAME}")
    print(f"[*] Forwarding logs to: {SOC_INGEST_URL}")
    print("[*] Monitoring for security events...")
    
    while True:
        # REAL-WORLD INTEGRATION:
        # 1. SIEM: Read from a Syslog socket or a dedicated export file.
        # 2. Cloud: Poll AWS CloudWatch or Azure Monitor APIs and forward the JSON.
        # 3. Local: Use 'tail -f' on /var/log/syslog or Event Viewer IDs.
        
        # DEMO SIMULATION:
        trigger_file = "security_alert.txt"
        
        if os.path.exists(trigger_file):
            try:
                with open(trigger_file, "r") as f:
                    alert_content = f.read().strip()
                
                print(f"[!] Security event detected: {alert_content[:50]}...")
                
                payload = {
                    "source": f"Endpoint:{SOURCE_NAME}",
                    "log": f"Local Alert: {alert_content}"
                }
                
                response = requests.post(SOC_INGEST_URL, json=payload, timeout=8)
                
                if response.status_code == 200:
                    print("[+] Successfully ingested by MSOC AI Engine.")
                    os.remove(trigger_file)
                else:
                    print(f"[?] MSOC returned status: {response.status_code}")
                    
            except Exception as e:
                print(f"[!] Error forwarding event: {e}")
                
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        monitor_events()
    except KeyboardInterrupt:
        print("\n[*] Agent stopped by user.")
