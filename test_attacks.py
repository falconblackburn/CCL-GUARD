import requests
import time
import json
import random

# SOC Configuration
SOC_URL = "http://127.0.0.1:5001"
INGEST_ENDPOINT = f"{SOC_URL}/api/v2/ingest"

def simulate_attack(name, log_data, source="NetworkSensor"):
    print(f"\n🚀 Simulating {name}...")
    payload = {
        "source": source,
        "log": log_data
    }
    
    try:
        response = requests.post(INGEST_ENDPOINT, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Detection: {result.get('attack')} ({result.get('confidence')*100:.1f}%)")
            print(f"🧠 AI Analysis: {result.get('analysis')[:200]}...")
        else:
            print(f"❌ Error: Received status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

def run_test_suite():
    print("=== SOC ATTACK SIMULATION SUITE ===")
    
    # 1. SQL Injection
    simulate_attack(
        "SQL Injection", 
        "SELECT * FROM users WHERE id = '1' OR '1'='1'; -- drop table logs",
        source="WebFirewall"
    )
    
    time.sleep(2)
    
    # 2. Brute Force
    simulate_attack(
        "Brute Force", 
        "Failed login attempt for user 'admin' from IP 192.168.1.50 (Attempt 15/20)",
        source="AuthService"
    )
    
    time.sleep(2)
    
    # 3. DDoS/Traffic Spike
    simulate_attack(
        "DDoS Attack", 
        f"Inbound traffic spike: {random.randint(50000, 100000)} packets/sec from botnet cluster",
        source="EdgeRouter"
    )
    
    time.sleep(2)
    
    # 4. Normal Activity (Benign)
    simulate_attack(
        "Normal Activity", 
        "User 'jdoe' successfully logged in from authorized device.",
        source="AuthService"
    )

if __name__ == "__main__":
    run_test_suite()
    print("\n✅ Simulation complete. Check the Dashboard (http://127.0.0.1:5001) for real-time updates.")
