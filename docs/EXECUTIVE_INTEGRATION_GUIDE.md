# 🛡️ CCL Guard: Enterprise Deployment & Ingestion Guide

This guide provides step-by-step instructions for deploying the AI SOC platform in production environments and configuring advanced log ingestion for multi-cloud visibility.

---

## 💻 1. Windows Server Deployment (IIS / Windows Service)

Windows Server is commonly used in corporate headquarters for local SOC hosting.

### A. Prerequisites
1.  **Python 3.10+**: Install from python.org (ensure "Add to PATH" is checked).
2.  **Git for Windows**: To pull updates.
3.  **Virtual Environment**:
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt
    ```

### B. Running as a Windows Service (NSSM)
To ensure the SOC starts automatically after a reboot:
1.  Download **NSSM** (Non-Sucking Service Manager).
2.  Open PowerShell as Administrator and run:
    ```powershell
    nssm install CCL_Guard_SOC
    ```
3.  **Path**: `C:\path\to\CCL-GUARD\venv\Scripts\python.exe`
4.  **Startup Directory**: `C:\path\to\CCL-GUARD`
5.  **Arguments**: `app.py`
6.  Repeat for `parent_app.py` if hosting the Central Director on the same machine.

---

## 🐧 2. Linux Server Deployment (Systemd + Nginx)

Recommended for VPS/Cloud deployments (Ubuntu 22.04+).

### A. Systemd Unit File
Create `/etc/systemd/system/ccl-soc.service`:
```ini
[Unit]
Description=CCL Guard AI SOC Client
After=network.target

[Service]
User=root
WorkingDirectory=/opt/ccl-guard
Environment="PYTHONPATH=/opt/ccl-guard"
ExecStart=/opt/ccl-guard/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### B. Nginx Reverse Proxy (SSL)
Configure Nginx to handle HTTPS traffic:
```nginx
server {
    listen 80;
    server_name soc.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name soc.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/soc.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/soc.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🔌 3. Log Ingestion Recipes

### 🛡️ Fortinet (FortiGate)
**Option 1: Syslog (Live Stream)**
1.  Log in to FortiOS.
2.  Go to **Log & Report > Log Settings**.
3.  Enable **Send Logs to Syslog**.
4.  **IP Address**: Your SOC IP.
5.  **Port**: 514 (Must ensure firewall allows UDP 514).

**Option 2: API Poll (FortiAnalyzer)**
Use `api/fortinet_sync.py` by providing your API key and URL in the `.env` file.

### ☁️ Microsoft Azure (Entra ID / Sign-ins)
1.  **App Registration**: Create an App in Azure Portal.
2.  **API Permissions**: Grant `SecurityEvents.Read.All` and `LogAnalytics.Read`.
3.  **Environment**: Add `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, and `AZURE_TENANT_ID` to `.env`.
4.  The `api/azure_sync.py` script will automatically pull security graph alerts.

### 🚀 Cloudflare (WAF Logs)
1.  Navigate to **Analytics & Logs > Logpush**.
2.  Select **HTTP Events**.
3.  Choose **Destination: S3 Compatible or Webhook**.
4.  **Endpoint**: `https://your-soc.com/api/v2/ingest`
5.  **Headers**: `X-SOC-TOKEN: your_secret_token`.

### 🔍 Splunk
Direct Splunk to forward data using a **Heavy Forwarder** or **Webhook Alert**:
1.  Create an Alert in Splunk.
2.  Under **Trigger Actions**, select **Webhook**.
3.  **URL**: `https://your-soc.com/api/v2/ingest`.
4.  Payload will be automatically parsed by the SOC's universal ingestion engine.

---

## 📊 4. Ingesting Historic Logs
To ingest a CSV/JSON dump from a previous tool:
1.  Format the file containing `timestamp, source, raw_data`.
2.  Use the `scripts/bulk_ingest.py` tool (included in core packages) to replay logs into the SOC engine.
