# 🚀 CCL Guard: Comprehensive Deployment Guide

This guide covers the end-to-end deployment of CCL Guard in a production customer environment.

## 1. Environment Readiness Audit
Before deployment, verify the following:
- [ ] **Python 3.12+** installed and added to PATH.
- [ ] **SQLite 3** available (Standard with Python).
- [ ] **Internet Access** enabled for Gemini API and Cloudflare Tunnels.
- [ ] **Admin Privileges** available for service registration.

## 2. Deployment Steps

### Option A: One-Click Windows Install (Recommended)
1.  **Extract Package**: Move the `CyberSecurity-AI-SOC` folder to `C:\Program Files\CCL-Guard`.
2.  **Run Installer**: Right-click `install_wizard.ps1` -> **Run with PowerShell**.
3.  **Enter Configuration**:
    -   `Client Name`: A unique identifier for the customer.
    -   `Director URL`: The URL of your centralized Director Dashboard.
4.  **Verification**: After the script finishes, wait 60 seconds and check for the client in the Director Dashboard.

### Option B: Manual CLI Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
copy .env.example .env
nano .env # Add GEMINI_API_KEY, CLIENT_NAME, etc.

# 3. Start the application in background (using nohup or PM2)
nohup python app.py > soc.log 2>&1 &
```

## 3. Post-Deployment Verification
To ensure the SOC is working correctly, run the provided simulation tool:
```bash
python test_attacks.py
```
This will send mock attacks to the local engine and verify that:
1.  The ML model detects the attack type.
2.  The AI Orchestrator generates analysis and remediation.
3.  The event appears on the Dashboard immediately.

## 4. Troubleshooting
- **Dashboard 500 Error**: Check `soc_app.log` for database locks or missing variables. Ensure `database.py` has `connect_with_retry` implemented.
- **AI Not Responding**: Verify your `GEMINI_API_KEY` in the `.env` file. Check if `Ollama` is running if using local mode.
- **Client Not Showing in Director**: Check the `parent_app.py` logs (port 5005) to see if heartbeats are being rejected.

---
**Security Note:** Always ensure the `.env` file is secured and not world-readable.
