import requests
import random
import time
import sys

URL = "http://127.0.0.1:5001/api/v2/ingest"

sources = ["Fortinet Firewall", "Splunk SIEM", "AWS GuardDuty", "Azure Sentinel", "Cloudflare WAF"]
attacks = [
    ("DDoS", "Packets: 5000, LoginFail: 0, SQL: 0", "High"),
    ("SQLInjection", "Packets: 100, LoginFail: 0, SQL: 1", "Critical"),
    ("BruteForce", "Packets: 200, LoginFail: 1, SQL: 0", "Medium"),
    ("PortScan", "Packets: 300, LoginFail: 0, SQL: 0", "Low"),
    ("Data Exfiltration", "Packets: 10000, LoginFail: 0, SQL: 0", "Critical")
]

print("[*] Starting Enhanced Multi-Source Breach Simulation (300 Attacks)...")

for i in range(300):
    src = random.choice(sources)
    attack_name, raw_log, severity = random.choice(attacks)
    ip = f"{random.randint(11, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    
    payload = {
        "source": src,
        "log": f"ATTACK={attack_name} SEVERITY={severity} DETAILS={raw_log} SRCIP={ip}"
    }
    
    headers = {"X-Forwarded-For": ip}
    
    try:
        r = requests.post(URL, json=payload, headers=headers, timeout=5)
        print(f"[+] Sent Attack {i+1}/300: {attack_name} from {src} ({ip})")
    except Exception as e:
        print(f"[!] Connection failed: {e}")
        
    time.sleep(5.0)

print("[*] Simulation Completed.")
