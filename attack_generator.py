import requests
import random
import time
import sys
import argparse

# ==========================================
# CCL Agentic MSOC - Breach Simulator
# ==========================================

parser = argparse.ArgumentParser(description="Simulate security breaches for MSOC testing.")
parser.add_argument("--count", type=int, default=0, help="Number of attacks to simulate (0 for infinite)")
parser.add_argument("--interval", type=int, default=3, help="Seconds between attacks")
args = parser.parse_args()

URL = "http://127.0.0.1:5001/predict"

print(f"[*] Starting Breach Simulation (Count: {'Infinite' if args.count == 0 else args.count})...")

attacks_sent = 0
while True:
    data = {
        "packets": random.randint(300, 2500),
        "login_fail": random.randint(0, 1),
        "sql": random.randint(0, 1),
    }

    headers = {
        "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    }

    try:
        r = requests.post(URL, json=data, headers=headers, timeout=5)
        attacks_sent += 1
        print(f"[+] Attack {attacks_sent} sent: {data}")
    except Exception as e:
        print(f"[!] Target MSOC unreachable: {e}")

    if args.count > 0 and attacks_sent >= args.count:
        print("[*] Simulation complete.")
        break
        
    time.sleep(args.interval)
