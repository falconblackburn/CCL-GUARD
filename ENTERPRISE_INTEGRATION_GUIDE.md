# 🌍 Enterprise Cloud Integration Guide

CCL Guard is designed as a centralized, API-first SIEM and Security Operations Center. This means you do not need to install heavy agents on your cloud infrastructure. Instead, **any cloud provider** can instantly stream its security logs directly into CCL Guard's AI Engine in real-time using standard Webhooks and APIs.

The universal endpoint for all log ingestion is:
`POST http://[YOUR-SOC-IP]:5001/api/v2/ingest`

Below are the step-by-step integration guides for all major enterprise platforms.

---

## ☁️ 1. Microsoft Azure (Active Directory, VMs, Defender)

The most efficient way to get Azure logs (Audit logs, Sign-in logs, Activity logs) into CCL Guard is via an Event Hub.

**Architecture:** `Azure Monitor` -> `Azure Event Hub` -> `Azure Function` -> `CCL Guard`

1. **Create an Azure Event Hub:** In the Azure Portal, create a new Event Hubs Namespace and a specific Event Hub (e.g., `soc-logs`).
2. **Stream Logs:** Go to **Azure Monitor > Diagnostic Settings**, select your target logs (e.g., *SignInLogs*, *AuditLogs*), and route them to your new Event Hub.
3. **Connect to CCL Guard:** Create an **Azure Function App** (Python) with an Event Hub Trigger. Use this code to send the logs to your SOC:
   ```python
   import requests

   def main(event: str):
       SOC_URL = "http://[YOUR-SOC-IP]:5001/api/v2/ingest"
       payload = { "source": "Azure-Cloud", "log": event }
       requests.post(SOC_URL, json=payload)
   ```

---

## 🟧 2. Amazon Web Services (AWS CloudTrail & GuardDuty)

AWS logs can be pushed in real-time using EventBridge and AWS Lambda.

**Architecture:** `AWS CloudTrail/GuardDuty` -> `EventBridge Rule` -> `AWS Lambda` -> `CCL Guard`

1. **Create an EventBridge Rule:** In AWS, create a rule to capture specific security events (like GuardDuty Findings, or unauthorized IAM API calls).
2. **Create a Lambda Function:** Set the target of your EventBridge Rule to a new Python Lambda function.
3. **Lambda Code:**
   ```python
   import json
   import urllib.request

   def lambda_handler(event, context):
       url = "http://[YOUR-SOC-IP]:5001/api/v2/ingest"
       payload = json.dumps({
           "source": "AWS-GuardDuty",
           "log": json.dumps(event['detail'])
       }).encode('utf-8')
       
       req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
       urllib.request.urlopen(req)
   ```

---

## 🛡️ 3. Cloudflare (WAF & Zero Trust)

Cloudflare can stream edge firewall blocks and Zero Trust access logs directly to your SOC.

**Architecture:** `Cloudflare Logpush or Worker` -> `CCL Guard`

*   **For Enterprise (Logpush):** In the Cloudflare Dashboard, go to Analytics > Logpush. Set the destination to an HTTP endpoint and input your SOC URL (`http://[YOUR-SOC-IP]:5001/api/v2/ingest`).
*   **For Pro/Free (Workers):** Create a Cloudflare Worker that intercepts blocked metrics via the Cloudflare GraphQL API and securely POSTs them to your SOC.

---

## 🏢 4. Microsoft 365 Defender (Email & Endpoints)

If your clients use Microsoft 365, you can ingest email phishing alerts, endpoint malware detections, and DLP events directly into CCL Guard using Microsoft Graph Security API or Webhooks.

1. **Microsoft Defender Portal:** Navigate to Settings > Microsoft 365 Defender > Streaming API.
2. **Configure Endpoint:** Select **Webhook** as the destination.
3. **URL:** Output the alerts to `http://[YOUR-SOC-IP]:5001/api/v2/ingest`.
4. Ensure you map the source identifier to `"Microsoft-365"`.

---

## 🐧 5. Linux & Custom Applications (Syslog / Curl)

For any application not listed above, you can pipe raw output directly into CCL Guard using a simple `curl` command. This is perfect for custom web servers or cron jobs.

```bash
# Example: Sending a blocked SSH attempt from a Linux server
curl -X POST http://[YOUR-SOC-IP]:5001/api/v2/ingest \
-H "Content-Type: application/json" \
-d '{
  "source": "Linux-SSH",
  "log": "Failed password for root from 192.168.1.100 port 22 ssh2"
}'
```

---
### 🔒 Security Best Practice
Always ensure your Windows Server Firewall allows inbound traffic on Port **5001** only from the specific IP addresses of your Cloud Providers (AWS Lambda IPs, Azure Function IPs, etc.) to prevent spoofed logs.
