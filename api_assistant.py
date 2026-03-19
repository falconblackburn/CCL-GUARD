import os
import sqlite3
from flask import jsonify, request
# DB path logic

# Dynamically determine the DB path based on the OS
if os.name == 'nt':
    DB_NAME = os.path.join(os.environ.get('TEMP', 'C:\\temp'), "soc.db")
else:
    DB_NAME = "/tmp/soc.db"

def handle_assistant_query():
    """Handle natural language queries using Gemini."""
    data = request.json
    query = data.get("query", "")
    
    if not query:
        return jsonify({"response": "I didn't catch that. How can I help you today?"})

    try:
        # 1. Fetch current SOC state for context
        con = sqlite3.connect(DB_NAME)
        c = con.cursor()
        
        # Summary of last 24 hours of logs
        c.execute("SELECT attack, severity, COUNT(*) FROM logs WHERE time >= datetime('now', '-1 day') GROUP BY attack, severity")
        summary = c.fetchall()
        
        # Open incidents
        c.execute("SELECT attack, severity FROM incidents WHERE status = 'Open'")
        open_incidents = c.fetchall()
        con.close()

        # 2. Build context for AI
        context = f"--- SOC STATE SUMMARY ---\n"
        context += f"Last 24h Activity: {summary}\n"
        context += f"Active Incidents: {open_incidents}\n"

        assistant_prompt = (
            f"You are the CCL Guard Agentic Assistant. Use the provided context to answer the user's question.\n"
            f"Be concise, technical but helpful, and focus on security insights.\n\n"
            f"{context}\n\n"
            f"USER QUERY: {query}"
        )

        # 3. Call AI (Try Ollama first for free/local usage)
        model_to_use = os.environ.get("OLLAMA_MODEL", "llama3")
        import requests
        try:
            r = requests.post("http://127.0.0.1:11434/api/generate", 
                              json={"model": model_to_use, "prompt": assistant_prompt, "stream": False},
                              timeout=15)
            return jsonify({"response": r.json().get("response", "No response from local agent.")})
        except Exception as e:
            print(f"[ASSISTANT OLLAMA ERROR] {e}. Falling back to Gemini.")

        # 4. Fallback to Gemini
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_api_key:
            return jsonify({"response": "Local AI (Ollama) is offline and no Gemini API key provided."})

        import google.generativeai as genai
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(assistant_prompt)
        return jsonify({"response": response.text})

    except Exception as e:
        return jsonify({"response": f"Assistant system error: {e}"})
