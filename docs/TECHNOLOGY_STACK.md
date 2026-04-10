# 🛠️ CCL Guard: Technical Stack & Architecture

CCL Guard is a state-of-the-art AI-Powered SOC (Security Operations Center) platform designed for modern enterprise defense.

## 1. Core Engine (Backend)
- **Python 3.12+**: The primary language for all backend processing, ML, and AI orchestration.
- **Flask**: A lightweight WSGI web application framework used for both the **Director Dashboard** and the **Client SOC Node**.
- **SQLite 3**: A high-performance, concurrent-safe embedded database used for local log storage, incident tracking, and threat intelligence.

## 2. Artificial Intelligence & Machine Learning
- **ML Engine (CIC-IDS2017)**: A custom Machine Learning model trained on the CIC-IDS2017 dataset to detect sophisticated network attacks (DDoS, SQLi, Brute Force) with high confidence.
- **Agentic SOC Orchestrator**:
    - **Ollama (Llama3)**: Primary local LLM for on-premise forensic analysis.
    - **Google Gemini (Flash 1.5/2.5)**: Cloud-native backup LLM for deep correlation and complex remediation strategy generation.
- **Multi-Agent Triage**: A proprietary system that uses three distinct AI agents (Triage, Forensics, Response) to process every alert.

## 3. Integrations & Data Sources
- **Cloudflare API**: Native GraphQL integration for ingesting WAF and firewall logs in real-time.
- **Azure MS Graph API**: Integration with Microsoft Defender for Cloud to ingest enterprise security alerts.
- **Twilio API**: WhatsApp Business API integration for interactive SOC alerts and autonomous action triggers.
- **AbuseIPDB & URLHaus**: Live threat intelligence feeds for IP reputation and malicious URL filtering.

## 4. Frontend & User Interface
- **Vanilla CSS3**: Advanced Glassmorphism UI with custom variables and modern layout patterns.
- **Lucide Icons**: Premium vector-based iconography.
- **JavaScript (ES6+)**: Real-time dashboard updates via asynchronous API polling.

## 5. Security & Connectivity
- **Cloudflare Tunnels**: Secure, agentless connectivity allowing the Director to communicate with clients without open firewall ports.
- **Windows Scheduled Tasks**: Automated background execution as a SYSTEM service for high persistence and stealth.
