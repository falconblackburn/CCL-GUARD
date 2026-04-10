import os
import time
import sqlite3
import random
from core.database import DB_NAME, insert_threat_intel

class DetectionEngineeringAgent:
    """
    Analyzes historical data to propose new rules and identify coverage gaps.
    """
    def __init__(self):
        self.rules = []

    def run_analysis(self):
        print("[DETECTION AGENT] Starting threat profile analysis...")
        
        # 1. Analyze BENIGN logs for anomalies that might have been missed
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT raw_data FROM logs WHERE attack='BENIGN' LIMIT 100")
        logs = c.fetchall()
        
        missed_count = 0
        for (raw,) in logs:
            # Simulate finding a missed pattern
            if "eval(" in raw.lower() or "base64" in raw.lower():
                missed_count += 1
                
        if missed_count > 0:
            print(f"[DETECTION AGENT] Identified {missed_count} potential false negatives. Tuning rules...")
            # Simulate pushing a rule update
            insert_threat_intel("DetectionEngine", f"DE-RULE-{random.randint(1000,9999)}", "RuleUpdate", f"Enhanced detection for obfuscated scripts.")
            
        conn.close()

def detection_engine_worker():
    agent = DetectionEngineeringAgent()
    while True:
        try:
            agent.run_analysis()
        except Exception as e:
            print(f"[DETECTION AGENT ERROR] {e}")
        time.sleep(3600) # Run every hour

if __name__ == "__main__":
    detection_engine_worker()
