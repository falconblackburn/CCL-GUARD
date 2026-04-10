import requests
import json
import time
import random
import sys
from config import Config

def simulate_attack(attack_type, source="TestSimulator"):
    """Fire a single attack event at the local ingestion endpoint."""
    print(f"[SIMULATOR] Launching {attack_type} simulation...")
    
    # Diverse payloads based on attack type
    payloads = {
        "SQLInjection": "SELECT * FROM users WHERE id = '1' OR '1'='1'; --",
        "DDoS": f"GET /login HTTP/1.1\nHost: cclguard.com\nUser-Agent: botnet-v9",
        "BruteForce": "user=admin&pass=123456&login_attempt=failed",
        "Phishing": "Go to http://security-update-ccl.com/login and reset your password.",
        "Ransomware": "Action: CRYPT_FILES | Extension: .ccl_locked | Key: RSA-4096",
        "DataExfiltration": "POST /outbound HTTP/1.1\nContent-Length: 5000000\n[REDACTED DATA]",
        "LateralMovement": "psexec.exe \\\\domain-ctrl-01 -u admin -p admin123"
    }
    
    log_data = payloads.get(attack_type, "Generic suspicious activity detected.")
    
    try:
        r = requests.post(
            Config.INGEST_URL,
            json={
                "source": source,
                "log": f"TIMESTAMP={time.strftime('%Y-%m-%d %H:%M:%S')} {log_data}"
            },
            timeout=10
        )
        print(f"[SIMULATOR] Status: {r.status_code}")
        print(f"[SIMULATOR] Response: {json.dumps(r.json(), indent=2)}")
    except Exception as e:
        print(f"[SIMULATOR ERROR] Failed to reach SOC: {e}")

def run_stress_test(count=10):
    """Simulate a sustained campaign with multiple attack types."""
    print(f"🚀 Starting Stress Test: {count} events...")
    attacks = list(["SQLInjection", "DDoS", "BruteForce", "Phishing", "Ransomware"])
    for i in range(count):
        atk = random.choice(attacks)
        simulate_attack(atk)
        time.sleep(random.uniform(0.5, 2.0))
    print("✅ Stress Test Complete.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "stress":
            run_stress_test(int(sys.argv[2]) if len(sys.argv) > 2 else 5)
        else:
            simulate_attack(cmd)
    else:
        print("Usage: python simulate_attacks.py [SQLInjection|DDoS|BruteForce|Phishing|Ransomware|stress]")
        print("Example: python simulate_attacks.py SQLInjection")
