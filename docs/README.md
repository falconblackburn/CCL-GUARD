# 🛡️ CCL Guard: Agentic AI SOC Platform

**CCL Guard** is a production-grade, Agentic Artificial Intelligence Security Operations Center (SOC). It utilizes Local Large Language Models (LLMs) via Ollama and Google Gemini 2.5 to autonomously ingest telemetry, triage alerts, conduct forensic investigations, and execute containment actions in real-time.

This repository transforms traditional manual security monitoring into a fully automated, multi-tenant Blue Team AI workflow.

---

## 🚀 Key Features

- **Agentic AI Investigation Loop:** Automatically executes a 3-stage multi-agent loop (Triage False Positives -> Deep Forensics -> Active Remediation) for every network alert.
- **Agentless Telemetry Ingestion:** Natively integrates with existing infrastructure without endpoint agents:
  - **Fortinet Firewalls:** Live UDP Syslog listener (Port 5140).
  - **Splunk SIEM:** REST API background polling.
  - **AWS / Azure / Cloudflare:** Automated log ingestion via API.
- **Multi-Tenant Director Dashboard:** Managed Service Providers (MSPs) can monitor multiple isolated customer deployments from a single pane of glass (Port 5005).
- **Automated Containment:** Proactively blocks malicious IP addresses on the host firewall (`netsh`, `iptables`) and isolates hosts.
- **Zero-Config Remote Access:** Automatically provisions secure **Cloudflare Tunnels** (`.trycloudflare.com`) during deployment, requiring zero inbound firewall changes.

---

## 💻 System Requirements

Because this platform runs both a web backend and Agentic AI models, the host machine must meet the following specifications:

- **Operating System:** Ubuntu 22.04+ (Recommended) or Windows Server 2022
- **Processor:** 4 vCPU cores (Minimum) / 8 vCPU cores (Recommended)
- **Memory (RAM):** 
  - **8GB RAM** (Minimum - Requires relying on the Gemini Cloud API for AI)
  - **24GB RAM** (Recommended - Allows running local, air-gapped `Llama3`/`Mistral` models via Ollama)
- **Storage:** 50GB SSD
- **Dependencies:** Docker and Docker Compose

---

## 🛠️ Customer Deployment Instructions (Step-by-Step)

Customers can deploy this application securely on their own infrastructure in less than 5 minutes using our interactive Docker setup wizard.

### 1. Download the Application
SSH into the deployment server (Linux VPS or Bare Metal) and clone the repository:
```bash
git clone https://github.com/falconblackburn/CCL-GUARD.git
cd CCL-GUARD
```

### 2. Run the Interactive Installer
Execute the automated setup script. This will build the Docker containers, configure environment variables, and map the persistent databases.
```bash
chmod +x setup_docker.sh
./setup_docker.sh
```

### 3. Follow Wizard Prompts
The wizard will ask you for:
- **Client Name** (For the MSP Director portal)
- **App Port** (Default: `5001`)
- **API Keys** (Optional: Gemini API Key for backup AI, Twilio for mobile alerts)

### 4. Access the Dashboard
Once the installation finishes, the SOC is officially live! The script will automatically output a securely generated **Cloudflare Tunnel URL** (e.g., `https://random-words.trycloudflare.com`). 

You can immediately visit this URL in your web browser to view the SOC dashboard from anywhere in the world. (Default login is typically `admin` / `admin123`).

---

## 🧱 Architecture Flow

1. **Ingestion Layer:** Data flows in via Syslog (UDP 5140), Splunk Polling, or the local Endpoint Agent webhook.
2. **Detection Engine:** ML-driven classification assesses the Risk and MITRE ATT&CK phase.
3. **Agentic AI Orchestrator:** 
   - Attempts local Ollama LLM execution.
   - Falls back to Gemini 2.5 API if local models are unavailable.
4. **Remediation Layer:** Approves automatic host isolation or IP blocking.
5. **Director Sync:** The heartbeat mechanism pushes tenant telemetry to the centralized MSP Director application.

---

## 👨‍💻 Contributing & Support
For advanced deployment modes (Windows PowerShell install, Render PaaS, or Upsun), please refer to the specific deployment guides located in the project root (e.g., `CUSTOMER_DEPLOYMENT_HANDBOOK.md`, `UPSUN_DEPLOYMENT_GUIDE.md`).

*© 2026 CCL Guard Cyber Defense | Agentic Security Solutions*
