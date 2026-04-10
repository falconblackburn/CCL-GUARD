import sqlite3
import os
import datetime

# Database path (compatible with setup.sh / app.py defaults)
if os.name == 'nt':
    DB_NAME = os.path.join(os.environ.get('TEMP', 'C:\\temp'), "soc.db")
else:
    DB_NAME = "/tmp/soc.db"

def simulate_correlated_attack():
    print("--- 🚀 CCL Guard: Simulating Multi-Stage Campaign ---")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Shared identifier: Admin John Smith
    target_user = "admin_jsmith"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # STAGE 1: Initial Access (Windows/Brute Force)
    print(f"[*] Simulating Stage 1: Brute Force attack on Windows (User: {target_user})")
    c.execute("""
    INSERT INTO logs(source, ip, country, raw_data, attack, severity, risk, mitre, ai_analysis, remediation, attack_prob, phase)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        "Windows", "192.168.1.50", "USA", 
        f"Event ID 4625: Multiple failed login attempts for user={target_user}", 
        "Brute Force", "Medium", 45, "T1110", 
        "Suspicious failed login count registered. Possible credential stuffing.", 
        "1. Alert user.\n2. Verify source IP.", 75, "Initial Access"
    ))

    # STAGE 2: Discovery (AWS / Data Sourcing)
    print(f"[*] Simulating Stage 2: S3 Data Discovery on AWS (User: {target_user})")
    c.execute("""
    INSERT INTO logs(source, ip, country, raw_data, attack, severity, risk, mitre, ai_analysis, remediation, attack_prob, phase)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        "AWS", "10.0.0.5", "Kenya", 
        f"CloudTrail: s3_list_buckets called by user={target_user} from unusual source", 
        "Data Discovery", "High", 70, "T1083", 
        "Unusual API access pattern detected for this administrative user.", 
        "1. Temporarily restrict S3 permissions.\n2. Trigger forensic analysis.", 85, "Discovery"
    ))

    conn.commit()
    conn.close()
    print("\n[✔] Simulation Complete. Both logs are now in the Dashboard.")
    print("[!] Instruction: Open the Dashboard, find the 'Brute Force' log, and click 'Analyze'.")
    print("[!] Observe if the AI pivots and finds the 'Data Discovery' signal from the same user.")

if __name__ == "__main__":
    simulate_correlated_attack()
