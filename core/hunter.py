import sqlite3
import os
import time
import requests

# DB path - must match database.py exactly
from config import Config
DB_NAME = Config.DB_NAME

def agentic_hunt():
    """Proactively hunt for threats using AI reasoning."""
    print("[HUNTER] Agentic Hunter initiated. Scanning for deep patterns...")
    
    try:
        con = sqlite3.connect(DB_NAME)
        c = con.cursor()
        
        # 1. Fetch the last 20 events for broad pattern analysis
        c.execute("SELECT ip, attack, severity, time, id FROM logs ORDER BY id DESC LIMIT 20")
        logs = c.fetchall()
        
        if len(logs) < 5:
            print("[HUNTER] Not enough data for a deep hunt yet.")
            con.close()
            return

        # 2. Prepare the dataset for AI reasoning
        log_summary = ""
        for l in logs:
            log_summary += f"ID:{l[4]} | IP:{l[0]} | Type:{l[1]} | Sev:{l[2]} | Time:{l[3]}\n"

        # 3. Ask AI to find 'invisible' anomalies (Try Ollama first)
        model_to_use = os.environ.get("OLLAMA_MODEL", "llama3")
        prompt = (
            "You are a Proactive Threat Hunter. Analyze these recent logs for HIDDEN patterns or tactical shifts "
            "that signature-based systems might miss (e.g., slow-and-low scans, lateral movement, or same-IP escalation).\n\n"
            "--- RECENT LOGS ---\n"
            f"{log_summary}\n\n"
            "TASK:\n"
            "If you find a suspicious pattern, return ONLY a JSON object with this structure:\n"
            '{"found": true, "pattern": "Description of the anomaly", "severity": "High/Critical", "target_ip": "IP address"}\n'
            "If everything looks normal, return: "
            '{"found": false}'
        )

        res_text = ""
        try:
            r = requests.post("http://127.0.0.1:11434/api/generate", 
                              json={"model": model_to_use, "prompt": prompt, "stream": False},
                              timeout=30)
            r.raise_for_status() # Raise an exception for HTTP errors
            res_text = r.json().get("response", "").strip()
        except requests.exceptions.RequestException as e:
            print(f"[HUNTER OLLAMA ERROR] {e}. Falling back to Gemini.")
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            if gemini_api_key:
                import google.generativeai as genai
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(prompt)
                res_text = response.text.strip()
                print(f"[HUNTER DEBUG] Gemini Response: {res_text[:100]}...")
            else:
                print("[HUNTER] No AI engines available. Skipping hunt.")
                con.close()
                return
        except Exception as e: # Catch other potential errors from Ollama processing
            print(f"[HUNTER OLLAMA PROCESSING ERROR] {e}. Falling back to Gemini.")
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            if gemini_api_key:
                import google.generativeai as genai
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(prompt)
                res_text = response.text.strip()
                print(f"[HUNTER DEBUG] Gemini Response (Fallback): {res_text[:100]}...")
            else:
                print("[HUNTER] No AI engines available. Skipping hunt.")
                con.close()
                return

        import json
        
        # Clean response text if AI adds markdown backticks
        res_text = res_text.replace("```json", "").replace("```", "")
        result = json.loads(res_text)

        if result.get("found"):
            print(f"[HUNTER] ANOMALY DETECTED: {result['pattern']}")
            # 4. Create a Proactive Incident
            from core.database import create_incident
            create_incident(
                attack=f"HUNT:{result['pattern'][:30]}",
                severity=result["severity"],
                risk=90 if result["severity"] == "High" else 99,
                phase="Proactive Hunting",
                ai_summary=f"Proactive Hunt: {result['pattern']}",
                remediation_steps="1. Isolate target IP.\n2. Review full traffic history for lateral movement.\n3. Conduct deep packet inspection.",
                source="Agentic Hunter"
            )
        else:
            print("[HUNTER] No deep anomalies found in this cycle.")

        con.close()
    except Exception as e:
        print(f"[HUNTER] Error during hunt: {e}")

if __name__ == "__main__":
    # In production, this would run every hour. For demo, we run once.
    agentic_hunt()
