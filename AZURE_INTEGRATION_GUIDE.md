# ☁️ Azure Cloud Integration Guide

CCL Guard is designed to ingest logs from Azure tenant environments without requiring agents on every cloud resource. Follow these steps to stream Azure logs to your SOC.

## 1. Architectural Overview
The most efficient way to get Azure logs (Audit logs, Sign-in logs, Activity logs) into CCL Guard is:
`Azure Monitor` -> `Diagnostic Settings` -> `Azure Event Hub` -> `Azure Function` -> `CCL Guard API`

## 2. Step-by-Step Configuration

### A. Create an Azure Event Hub
1.  Search for **Event Hubs** in the Azure Portal.
2.  Create a new Event Hubs Namespace and a specific Event Hub (e.g., `azure-logs-stream`).

### B. Stream Logs to Event Hub
1.  Go to **Azure Monitor** -> **Diagnostic Settings**.
2.  Click **"Add diagnostic setting"**.
3.  Choose the logs you want (e.g., *SignInLogs*, *AuditLogs*).
4.  Under "Destination Details", select **"Stream to an event hub"** and pick the one you created in Step A.

### C. Connect to CCL Guard via Azure Function
1.  Create a new **Azure Function App** (Python or Node.js).
2.  Use the **Event Hub Trigger** template.
3.  In the function code, write a simple `POST` request to send the log to your CCL Guard URL:
    ```python
    import requests
    import json

    def main(event: str):
        SOC_URL = "http://[YOUR-SERVER-IP]:5001/api/v2/ingest"
        payload = {
            "source": "AzureCloud",
            "log": event
        }
        requests.post(SOC_URL, json=payload)
    ```

## 3. Benefits of this Integration
*   **Security Scanning:** Every Azure sign-in attempt is automatically run through the CCL Guard AI engine.
*   **Anomaly Detection:** Detect unusual admin activity in Azure (e.g., privilege escalation).
*   **Centralized Reporting:** Combine your on-premise Windows logs and Azure Cloud logs into a single Executive Report.

## 4. Office Testing & Demo (Azure Environment)
If you are testing CCL Guard in an office environment with an existing Azure tenant, follow these tips:

### A. Simulate Azure Alerts
1.  Go to **Microsoft Defender for Cloud**.
2.  In the "Security Alerts" tab, click **"Sample alerts"**.
3.  Select a "High" or "Critical" alert to generate a realistic security event in your Azure tenant.
4.  CCL Guard's `azure_sync.py` worker will pick this up automatically (it now polls 24 hours of history).

### B. Verification Logs
Check the CCL Guard terminal (or `app_restart.log`) for this success message:
`[Azure Defender] Processed X alerts.`

### C. Demo Mode (Offline)
If you don't have active Azure alerts, you can run the following to populate the dashboard with 11 pre-configured critical incidents for management review:
```bash
python generate_test_data.py
```

---
**Note:** Ensure your Windows Server Firewall allows inbound traffic on Port **5001** from the Azure Function's IP address.
