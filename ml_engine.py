import random

class UnsupervisedAnomalyDetector:
    """
    Identifies zero-day or unknown threats using statistical rarity.
    In a real implementation, this would use IsolationForest or Local Outlier Factor.
    """
    def __init__(self):
        self.baseline_stats = {"request_rate": 10, "payload_size": 500}

    def inspect(self, raw_log):
        # Simulated statistical anomaly detection
        score = random.uniform(0, 1)
        if score > 0.95:
            return True, score # High anomaly
        return False, score

class CICIDS2017Model:
    """
    Simulated Machine Learning Model based on CIC-IDS2017 dataset features.
    """
    
    LABELS = [
        "BENIGN", "DDoS", "PortScan", "Bot", "Infiltration", 
        "Web Attack - Brute Force", "Web Attack - SQL Injection", "FTP-Patator", "Phishing"
    ]

    def __init__(self):
        print("[ML] ML Engine Initialized: Loading CIC-IDS2017 weights...")
        self.anomaly_detector = UnsupervisedAnomalyDetector()

    def extract_features(self, raw_log):
        features = {
            "flow_duration": random.randint(100, 1000000),
            "total_fwd_pkts": random.randint(1, 50),
            "fwd_pkt_len_max": random.randint(40, 1500)
        }
        return features

    def predict(self, raw_log):
        log_lower = raw_log.lower()
        
        # 1. Zero-Day Anomaly Detection (Unsupervised)
        is_anomaly, anomaly_score = self.anomaly_detector.inspect(raw_log)
        if is_anomaly:
            return "Zero-Day Anomaly", anomaly_score

        # 2. Extract numeric features from common SOC log format
        # Format example: "Packets: 10000, LoginFail: 50, SQL: 1"
        try:
            import re
            p_match = re.search(r"packets:\s*(\d+)", log_lower)
            l_match = re.search(r"loginfail:\s*(\d+)", log_lower)
            s_match = re.search(r"sql:\s*(\d+)", log_lower)
            
            packets = int(p_match.group(1)) if p_match else 0
            login_fail = int(l_match.group(1)) if l_match else 0
            sql = int(s_match.group(1)) if s_match else 0
            
            if packets > 5000: return "DDoS", 0.99
            if login_fail > 20: return "Web Attack - Brute Force", 0.95
            if sql > 0: return "Web Attack - SQL Injection", 0.98
        except:
            pass

        # 3. Phishing Detection
        if "bit.ly" in log_lower or "urgent" in log_lower or "verify account" in log_lower:
            return "Phishing", 0.92

        # 4. Web Attack Detection (Regex fallback)
        if "select " in log_lower or "union " in log_lower or "drop table" in log_lower:
            return "Web Attack - SQL Injection", 0.98
        
        if ("password" in log_lower and "fail" in log_lower) or "invalid login" in log_lower:
            return "Web Attack - Brute Force", 0.94
            
        # 5. Network Attack Detection
        if "flood" in log_lower or "volumetric" in log_lower or "syn-ack" in log_lower:
            return "DDoS", 0.99
            
        if "scan" in log_lower or "probe" in log_lower or "nmap" in log_lower:
            return "PortScan", 0.91
            
        # 6. Default
        return "BENIGN", 0.12

ml_engine = CICIDS2017Model()
