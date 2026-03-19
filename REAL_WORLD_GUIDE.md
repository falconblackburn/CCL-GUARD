# Real-World Production Guide: CCL Agentic MSOC

This guide outlines how to transition from this testing/demo environment to a live SOC deployment.

## 1. Environment Setup
### Local AI (Ollama)
For the AI Remediation engine to function without cloud dependencies:
1. Install [Ollama](https://ollama.com/) on your host machine.
2. Pull the required models:
   ```bash
   ollama pull llama3
   ollama pull mistral
   ```
3. Ensure Ollama is running on `localhost:11434`.

### Production Server
Use `gunicorn` for a stable deployment:
```bash
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

## 2. Real-Time Data Ingestion
### Using the Lightweight Agent (`lightweight_agent.py`)
Deploy this script on endpoints you wish to monitor. It watches for a `security_alert.txt` file (trigger) and forwards logs to the SOC.
- **To automate:** Modify the script's `monitor_events` function to tail `/var/log/auth.log` or Windows Event Logs.

### Live Network Monitoring (`sensor.py`)
Run the sensor on a network tap or a server's main interface to monitor traffic:
```bash
sudo python3 sensor.py
```
*Note: Requires `scapy` and root privileges for packet sniffing.*

## 3. Simulating Attacks for Testing
To verify your SOC's detection and AI analysis:
1. Ensure the app is running.
2. Run the attack simulation (if available):
   ```bash
   python3 attack_generator.py
   ```
   *If not available, you can trigger individual detections by passing specific payloads (e.g., `' OR 1=1--`) via the `/predict` or `/api/v2/ingest` endpoints.*

## 4. Configuration (Env Vars)
Set these in a `.env` file for production:
- `FLASK_SECRET_KEY`: Long, random hex string.
- `USE_AI`: Set to `true` (requires Ollama) or `false` (uses rule-based fallback).
- `ABUSE_API_KEY`: For external IP reputation checks.
- `EMAIL_PASS`: For automated alerts.

## 5. Security Best Practices
- **Restrict Access:** Use a VPN or firewall to limit access to port 5001.
- **HTTPS:** Deploy behind a reverse proxy (Nginx) with SSL certificates.
- **Audit Logs:** Check the `Audit Log` tab in the dashboard frequently to monitor SOC analyst actions.
