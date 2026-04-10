import os
import requests
import json
import sqlite3
import re
import datetime
from config import Config
from core.database import get_connection

class AIAnalysisEngine:
    @staticmethod
    def get_model():
        """Detect available model or fallback."""
        try:
            r = requests.get(Config.OLLAMA_ENDPOINT.replace("/generate", "/tags"), timeout=3)
            models = r.json().get("models", [])
            if any(m['name'].startswith("llama3") for m in models): return "llama3"
            if models: return models[0]['name'] 
            return "llama3"
        except:
            return "llama3"

    @staticmethod
    def get_rule_based_analysis(attack_type, severity, source):
        """Advanced heuristic threat intelligence engine for fallback analysis."""
        remediations = {
            "SQLInjection": [
                "Containment: Immediate block of Source IP {} at edge firewall.",
                "Forensics: Review audit logs for successful data exfiltration attempts.",
                "Remediation: Implement Parameterized Queries or ORM layers across all web endpoints.",
                "Sanitization: Verify and sanitize all user input fields to prevent lateral injection."
            ],
            "DDoS": [
                "Containment: Enable Cloudflare/Akamai traffic scrubbing for ingestion point: {}.",
                "Network: Apply rate limiting at the Load Balancer level to prevent resource exhaustion.",
                "Verification: Analyze NetFlow logs for anomalous UDP/HTTP flood patterns.",
                "Mitigation: Coordinate with upstream ISPs to drop the high-volume traffic before the ingress."
            ],
            "BruteForce": [
                "Lockout: Trigger 30-minute account lockout policy for impacted user IDs.",
                "Identity: Enforce Multi-Factor Authentication (MFA) on all external authentication entry points.",
                "Credential Hygiene: Rotate administrative credentials if any session persistence is detected.",
                "Audit: Review successful logins from non-standard geographic locations during the attack window."
            ],
            "PortScan": [
                "Forensics: Identify the reconnaissance intent by reviewing the scan's targeted ports.",
                "Hardening: Minimize surface area by closing non-essential ports on the asset: {}.",
                "ACL: Update Network Security Group (NSG) or Firewall rules to 'Deny All' for the source IP.",
                "Detection: Enable Intrusion Prevention System (IPS) for better detection of future reconnaissance."
            ],
            "Ransomware": [
                "Critical: Immediate isolation of internal asset: {} from the corporate network.",
                "Forensics: Identify the file modification baseline and look for encrypted file extensions.",
                "Recovery: Prioritize Volume Shadow Copy restoration or immutable backup retrieval.",
                "Containment: Disable any known compromised Service Accounts to prevent lateral encryption spreading."
            ],
            "Phishing": [
                "Immediate: Purge identified malicious email from all user mailboxes.",
                "Identity: Reset the credentials for any user who clicked the malicious link from {}.",
                "Domain: Blacklist the phishing URL and originating domain at the DNS/Proxy level.",
                "Awareness: Trigger a mandatory security awareness session for the impacted business unit."
            ],
            "DataExfiltration": [
                "Investigation: Analyze outbound data transfer volume to identify the leaked data assets.",
                "Network: Kill all active TCP/UDP sessions originating from {} to external IPs.",
                "Privacy: Inform the DPO (Data Protection Officer) if PII/PHI was part of the exfiltrated packet.",
                "Hardening: Implement Data Loss Prevention (DLP) rules to monitor for future outbound sensitivity."
            ],
            "LateralMovement": [
                "Containment: Isolate the source host {} to prevent cross-segment propagation.",
                "Forensics: Audit RDP, SSH, and SMB logs for non-standard administrative access.",
                "System: Reset Local Admin passwords across the impacted cluster immediately.",
                "Detection: Deploy EDR (Endpoint Detection & Response) sensors for deep process-level visibility."
            ],
            "Generic": [
                "Intelligence: Investigate the anomalous alert originating from source: {}.",
                "Forensics: Perform a deep log audit for signs of persistence or lateral movement.",
                "IR Plan: Follow the standard Cyber Incident Response Plan (CIRP) for {} incidents.",
                "Policy: Verify the Asset Integrity Management (AIM) policy for the target system: {}."
            ]
        }
        
        rule_key = "Generic"
        if "SQL" in attack_type or "Injection" in attack_type: rule_key = "SQLInjection"
        elif "DDoS" in attack_type or "Flood" in attack_type: rule_key = "DDoS"
        elif "Brute" in attack_type or "Auth" in attack_type: rule_key = "BruteForce"
        elif "Scan" in attack_type: rule_key = "PortScan"
        elif "Ransom" in attack_type or "Cryp" in attack_type: rule_key = "Ransomware"
        elif "Phish" in attack_type or "Mail" in attack_type: rule_key = "Phishing"
        elif "Exfiltr" in attack_type or "Leak" in attack_type: rule_key = "DataExfiltration"
        elif "Lateral" in attack_type or "Jump" in attack_type: rule_key = "LateralMovement"

        rules = remediations.get(rule_key, remediations["Generic"])
        formatted_rem = "\n".join([f"{i+1}. {r.format(source, attack_type, severity)}" for i, r in enumerate(rules)])
        
        analysis = (
            f"HEURISTIC THREAT INTEL: The detection signatures from {source} indicate high-confidence patterns of a {attack_type} campaign. "
            f"Correlation reveals the intent is likely {rule_key.lower()} targeting mission-critical assets. "
            f"Recommend shifting to level {severity} response protocol immediately."
        )
        return analysis, formatted_rem

    @staticmethod
    def get_correlation_context(log_id, ip, raw_data):
        context = f"--- CROSS-DOMAIN INVESTIGATION ---\nPrimary Context (IP {ip}):\n"
        try:
            con = get_connection()
            c = con.cursor()
            c.execute("SELECT attack, source, time FROM logs WHERE ip = ? AND id != ? ORDER BY id DESC LIMIT 5", (ip, log_id))
            for h in c.fetchall():
                context += f"- {h[2]} ({h[1]}): {h[0]}\n"
            
            user_match = re.search(r"user=([a-zA-Z0-9_-]+)", raw_data)
            if user_match:
                user = user_match.group(1)
                context += f"\nIdentity Correlation (User: {user}):\n"
                c.execute("SELECT attack, ip, source, time FROM logs WHERE raw_data LIKE ? AND id != ? LIMIT 5", (f"%user={user}%", log_id))
                for ul in c.fetchall():
                    context += f"- {ul[3]} (at {ul[1]} via {ul[2]}): {ul[0]}\n"
            con.close()
            return context
        except Exception as e:
            return f"Correlation failed: {e}"

    @staticmethod
    def get_few_shot_context():
        try:
            con = get_connection()
            c = con.cursor()
            c.execute("SELECT attack, severity, ai_summary, feedback FROM incidents WHERE approved_action = 1 LIMIT 3")
            approved = c.fetchall()
            con.close()
            if not approved: return ""
            context = "--- LEARNING FROM PAST ANALYST DECISIONS ---\n"
            for row in approved:
                context += f"Attack: {row[0]} | Decision: APPROVED | Logic: {row[3] or row[2][:100]}\n"
            return context + "\n"
        except:
            return ""

    @staticmethod
    def analyze(attack_type, severity, source="Unknown", ip="Unknown"):
        use_ai = Config.USE_AI
        gemini_api_key = Config.GEMINI_API_KEY
        ollama_model = Config.OLLAMA_MODEL

        print(f"\n[AI ORCHESTRATOR] New Request: {attack_type} | Severity: {severity} | IP: {ip}", flush=True)

        try:
            if not use_ai or (not gemini_api_key and not ollama_model):
                rule_analysis, rule_remediation = AIAnalysisEngine.get_rule_based_analysis(attack_type, severity, source)
                return "AGENTIC AI (Local Heuristics): " + rule_analysis, rule_remediation

            correlation_context = AIAnalysisEngine.get_correlation_context(0, ip, f"attack={attack_type} {source}")
            learning_context = AIAnalysisEngine.get_few_shot_context()
            
            full_prompt = (
                f"You are the Agentic SOC Orchestrator. GOAL: Contain the {attack_type} threat from {ip}/{source}.\n\n"
                f"Context: {correlation_context}\n{learning_context}\n"
                f"Return format:\nAnalysis: [Insights]\nRemediation: [Steps]\nRecommendedAction: [ACTION]"
            )

            if gemini_api_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=gemini_api_key)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response = model.generate_content(full_prompt).text
                    if "Analysis:" in response and "Remediation:" in response:
                        parts = response.split("Remediation:")
                        return parts[0].replace("Analysis:", "").strip(), parts[1].split("RecommendedAction:")[0].strip()
                except: pass

            if ollama_model:
                try:
                    r = requests.post(Config.OLLAMA_ENDPOINT, json={"model": ollama_model, "prompt": full_prompt, "stream": False}, timeout=10)
                    response = r.json().get("response", "").strip()
                    if "Analysis:" in response and "Remediation:" in response:
                        parts = response.split("Remediation:")
                        return parts[0].replace("Analysis:", "").strip(), parts[1].split("RecommendedAction:")[0].strip()
                except: pass

            raise Exception("AI Engines Failed")
        except Exception as e:
            print(f"⚠️ [AI FALLBACK] {e}")
            rule_analysis, rule_remediation = AIAnalysisEngine.get_rule_based_analysis(attack_type, severity, source)
            return "AGENTIC AI (Fallback Heuristics): " + rule_analysis, rule_remediation
