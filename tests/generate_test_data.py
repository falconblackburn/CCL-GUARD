import sqlite3
import random
import datetime
import os

# Use centralized configuration
from config import Config
from core.database import init_db
DB_NAME = Config.DB_NAME

def generate_incidents():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Clear existing data for a clean demo state
    c.execute("DELETE FROM incidents")
    c.execute("DELETE FROM logs")
    c.execute("DELETE FROM threat_feeds")
    c.execute("DELETE FROM feedback_logs")

    attacks = [
        ("SQL Injection", "Critical", 95, "Exploitation", "Critical SQL injection detected on /api/login.", "1. Block source IP.\n2. Sanitize inputs.\n3. Audit logs."),
        ("DDoS Attack", "High", 90, "Impact", "Massive traffic detected from multiple sources.", "1. Enable cloud scrubbing.\n2. Apply rate limiting."),
        ("Brute Force", "Medium", 65, "Initial Access", "Multiple failed login attempts on SSH port.", "1. Disable password auth.\n2. Implement Fail2Ban.\n3. Change SSH port."),
        ("Port Scanning", "Low", 30, "Recon", "Nmap scan detected from unknown range.", "1. Review firewall rules.\n2. Close unused ports.\n3. Update IDS signatures."),
        ("Data Exfiltration", "Critical", 95, "Exfiltration", "Suspicious data transfer to external IP.", "1. Isolate compromised host.\n2. Reset credentials.\n3. Perform forensic analysis."),
        ("Phishing Campaign", "Medium", 50, "Delivery", "Suspicious emails with malicious attachments reported.", "1. Quarantine emails.\n2. Alert users.\n3. Update mail filters."),
        ("Unauthorized Access", "High", 75, "Privilege Escalation", "Admin account logged in from unusual location.", "1. Suspend account.\n2. Reset MFA.\n3. Verify session logs."),
        ("Malware Detection", "High", 80, "Installation", "Trojan identified on internal file server.", "1. Quarantine file.\n2. Scan network.\n3. Restore from backup."),
        ("Ransomware", "Critical", 98, "Impact", "Encrypted files found on NAS.", "1. Shutdown network storage.\n2. Disconnect infected hosts.\n3. Contact IR team."),
        ("Internal Recon", "Low", 20, "Discovery", "Internal host scanning for SMB shares.", "1. Investigate internal host.\n2. Check for lateral movement.\n3. Update access controls.")
    ]

    for attack, severity, risk, phase, summary, remediation in attacks:
        local_time = datetime.datetime.now() - datetime.timedelta(minutes=random.randint(1, 1440))
        c.execute("""
        INSERT INTO incidents(attack, severity, risk, phase, status, ai_summary, remediation_steps, time, approved_action, feedback)
        VALUES(?,?,?,?, 'Open', ?, ?, ?, ?, ?)
        """, (attack, severity, risk, phase, summary, remediation, local_time.strftime("%Y-%m-%d %H:%M:%S"), 0, None))

    # Add a "Human Approved" incident to bootstrap the Learning Loop
    c.execute("""
    INSERT INTO incidents(attack, severity, risk, phase, status, ai_summary, remediation_steps, time, approved_action, feedback)
    VALUES(?,?,?,?, 'Approved', ?, ?, ?, 1, ?)
    """, ("SQL Injection", "Critical", 95, "Exploitation", "Verified SQLi targeting /api/admin", "1. WAF Block\n2. Query Param Audit", 
          datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Analyst confirmed this was an active attack from a known VPN."))

    # Threat Feeds
    feeds = [
        ("URLHaus", "http://malicious.ru/payload.exe", "Malicious executable hosted on Russian domain.", "Malware"),
        ("AbuseIPDB", "1.2.3.4", "Recent report of SSH brute force activity.", "Attack Source"),
        ("Feodo Tracker", "C&C Server 185.112.x.x", "Active botnet command and control node.", "Botnet")
    ]
    for source, indicator, desc, f_type in feeds:
        c.execute("INSERT INTO threat_feeds(source, indicator, description, type) VALUES(?,?,?,?)", (source, indicator, desc, f_type))

    # Also insert some logs
    for _ in range(20):
        source = random.choice(["SIEM", "AWS", "Windows", "NetworkSensor", "Cloudflare"])
        ip = f"192.168.1.{random.randint(1, 254)}"
        country = random.choice(["USA", "Kenya", "Germany", "China", "Russia"])
        attack_info = random.choice(attacks)
        raw_log = f"Log event: {attack_info[0]} detected at {datetime.datetime.now()}"
        
        c.execute("""
        INSERT INTO logs(source, ip, country, raw_data, attack, severity, risk, mitre, ai_analysis, remediation, attack_prob, phase)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """, (source, ip, country, raw_log, attack_info[0], attack_info[1], attack_info[2], "T1000", attack_info[4], attack_info[5], random.randint(70, 100), attack_info[3]))

    # --- CORRELATED SIGNAL DEMO ---
    # User "admin_jsmith" compromised?
    correlated_user = "admin_jsmith"
    c.execute("""
    INSERT INTO logs(source, ip, country, raw_data, attack, severity, risk, mitre, ai_analysis, remediation, attack_prob, phase)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
    """, ("Windows", "192.168.1.50", "USA", f"Failed login for user={correlated_user}", "Brute Force", "Medium", 40, "T1110", "Multiple failed logins for high-privilege account.", "Enable MFA.", 80, "Initial Access"))

    c.execute("""
    INSERT INTO logs(source, ip, country, raw_data, attack, severity, risk, mitre, ai_analysis, remediation, attack_prob, phase)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
    """, ("AWS", "10.0.0.5", "Kenya", f"S3 Bucket Access by user={correlated_user}", "Data Discovery", "High", 70, "T1083", "Unusual S3 access pattern for this user.", "Review IAM policy.", 85, "Discovery"))

    conn.commit()
    conn.close()
    print("Successfully generated 11 incidents and 20 logs.")

if __name__ == "__main__":
    # Ensure tables exist before generating data
    init_db()
    generate_incidents()
