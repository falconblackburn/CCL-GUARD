# CCL Guard: Complete Client Deployment & Integration Guide

Welcome to **CCL Guard**, the autonomous AI-driven Security Operations Center. This guide will walk you through the entire process of deploying the application on your own infrastructure and securely funneling your enterprise logs (SIEM, SOAR, Cloud) into the proactive Agentic Hunter engine.

---

## Part 1: Automated Deployment (5 Minutes)

We have designed the deployment process to be entirely automated. You do not need deep programming knowledge to launch your SOC.

### Prerequisites
- A Linux or Mac server/virtual machine.
- Git and Python 3 installed.
- (Optional but Recommended) [Ollama](https://ollama.com/) installed to run the AI engine 100% locally and free of charge.

### Installation Steps

1. **Clone the Repository** (or download the source code to your machine).
2. **Run the Interactive Wizard**:
   Open your terminal and execute:
   ```bash
   bash install_wizard.sh
   ```
   **For Windows Users:**
   Open a PowerShell console as Administrator and run:
   ```powershell
   .\install_wizard.ps1
   ```

3. **Follow the On-Screen Prompts**:
   - **AI Configuration**: Select `1` to use Ollama (Free/Local) or `2` to enter a Google Gemini API Key.
   - **WhatsApp Alerts**: Enter your Twilio Sandbox credentials and mobile number to receive instant, interactive threat alerts.
   - **Cloudflare WAF Ingestion (Optional)**: Provide your Cloudflare API credentials to automatically fetch your website's real-time firewall logs.
     * **How to find these:**
       * **Email**: The email address you use to log into Cloudflare.
       * **Global API Key**: In Cloudflare, go to My Profile -> API Tokens -> Global API Key -> View.
       * **Zone ID**: On your Cloudflare Dashboard, select your website. Scroll down on the right-side menu to find the "Zone ID".
   - **Management Registration**: If you are deploying this as part of a managed fleet, enter the name of your organization and the URL of your centralized Director Dashboard. Leave blank if running standalone.
   - **Public Tunneling**: The script will automatically configure a secure Cloudflare Tunnel, giving you a public URL (e.g., `https://your-soc.trycloudflare.com`) without opening any inbound ports on your firewall.

4. **Launch the SOC**:
   ```bash
   nohup .venv/bin/python3 app.py &
   ```
   Access your dashboard at `http://localhost:5001` or via your secure Cloudflare Tunnel URL.
   *Default Login:* `admin` / `admin123`

---

## Part 2: Pushing Enterprise Logs to CCL Guard

CCL Guard is designed to ingest data from anywhere. Rather than installing heavy agents on all your endpoints, CCL Guard uses a **Webhook / API Ingestion** model. 

This means your existing security tools (Splunk, Sentinel, CrowdStrike, AWS CloudTrail) simply "push" alerts to the CCL Guard API.

### The Universal Ingestion Endpoint

Your SOC constantly listens on this endpoint for new log data:
**`POST http://<YOUR_SOC_IP>:5001/api/v2/ingest`**

**Expected JSON Payload Format:**
```json
{
  "ip_address": "192.168.1.100",
  "country": "US",
  "raw_log": "Failed password for root from 192.168.1.100 port 22 ssh2",
  "attack_type": "Brute Force",
  "severity": "High",
  "risk_score": 85,
  "mitre_technique": "T1110",
  "ai_analysis": "Multiple failed logins indicating a brute force attempt.",
  "remediation": "Block IP 192.168.1.100 on external firewall.",
  "confidence": 95,
  "action_taken": "Alert Generated"
}
```

---

### Integration Examples

#### 1. Ingesting Real-Time Logs (SIEM / Syslog)
If you use a SIEM like **Splunk** or **Microsoft Sentinel**:
- Configure an action or logic app to trigger a webhook when a high-fidelity alert is generated.
- Point the webhook to your CCL Guard `/api/v2/ingest` endpoint.
- Map your SIEM fields to the JSON payload format above.

*Example Splunk Webhook Alert Action:*
Set the URL to `http://<YOUR_SOC_IP>:5001/api/v2/ingest` and configure the body to send the `$result.src_ip$` and `$result._raw$`.

#### 2. Ingesting Cloud Logs (AWS / Azure / Cloudflare)
We have already built a continuous background sync for Cloudflare. For other cloud providers:
- **AWS**: Configure EventBridge to route GuardDuty findings to an SNS Topic, which then triggers an HTTP HTTPS POST to your CCL Guard ingest API.
- **Azure**: Use Azure Logic Apps to forward Microsoft Defender for Cloud alerts directly to the CCL Guard webhook.

#### 3. Ingesting Historical/Old Logs (Batch Processing)
To feed historical data into the SOC (for the AI to learn from past incidents or search for persistent threats), you can write a simple Python script to read your old `.csv` or `.log` files and POST them to the API.

*Example Python Script for bulk ingestion:*
```python
import requests
import csv

SOC_URL = "http://localhost:5001/api/v2/ingest"

with open('historical_alerts.csv', mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        payload = {
            "ip_address": row['src_ip'],
            "country": "Unknown",
            "raw_log": row['raw_event'],
            "attack_type": row['category'],
            "severity": "Medium" if int(row['severity']) < 4 else "High",
            "risk_score": 50,
            "mitre_technique": "Unknown",
            "ai_analysis": "Historical Import",
            "remediation": "Review",
            "confidence": 50,
            "action_taken": "Imported"
        }
        requests.post(SOC_URL, json=payload)
        print(f"Imported {row['src_ip']}")
```

---

## Part 3: The Autonomous Cycle

Once your logs are flowing into the `/api/v2/ingest` endpoint:
1. **The Triage Engine** catches them and logs them in the database.
2. If it's a critical alert, it triggers an **Incident** and fires off an interactive **WhatsApp Alert**.
3. Every 30 minutes, the **Agentic Hunter** (running in the background) correlates all ingested data, pulls OSINT threat intelligence, and hunts for advanced persistent threats across all your historical and real-time logs.
