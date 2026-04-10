# 🏢 Step-by-Step Office Deployment Guide

This guide provides the exact steps to move **CCL Guard** from a demo environment to a permanent office-wide security installation.

## Step 1: Server Selection & OS
Pick a dedicated machine (Physical Server or Virtual Machine). 
*   **Recommended OS:** Ubuntu 22.04 LTS (for stability and security).
*   **Hardware:** 4 vCPUs, 8GB RAM (minimum if running local AI).

## Step 2: Persistent Installation (The "Permanent" Server)
In your office, you don't want to run the app in a terminal that might close. We use **Gunicorn** and **Systemd** to make it a permanent "service."

1.  **Clone & Setup:**
    ```bash
    git clone [your-repo] /opt/ccl-guard
    cd /opt/ccl-guard
    bash setup.sh
    ```
2.  **Create a Service File:** Create `/etc/systemd/system/cclguard.service` so it starts automatically if the server reboots.
3.  **Static IP:** Ensure the server has a static IP (e.g., `192.168.1.50`) so your sensors and cloud services always know where to send data.

## Step 3: Deployment of the "Eye" (Collection)
Choose your first collection method:
### A. The Endpoint Agent (CCL Agent)
Copy `lightweight_agent.py` to your most critical servers. Update the `SOC_INGEST_URL` in the script to your server's Static IP:
```python
SOC_INGEST_URL = "http://192.168.1.50:5001/api/v2/ingest"
```

### B. The Network Sensor (Agentless)
Connect a network cable from your Core Switch (Mirror Port) to the server and run:
```bash
sudo python3 sensor.py
```

## Step 4: Firewall & SSL Security
Since this dashboard contains sensitive data:
1.  **Restrict Port 5001:** Only allow your office IP range to access the dashboard.
2.  **Reverse Proxy:** Use Nginx or Apache to put the dashboard behind an `https://` (SSL) connection.
3.  **VPN:** For remote access, require your team to be on the company VPN before opening CCL Guard.

## Step 5: Connecting Cloud & SIEM
Finally, go to your cloud console (AWS/Azure) and set up the webhook or Lambda to forward alerts to your server's Public IP or VPN address.

---
**Need Help?** Contact the SOC Engineering Team for custom SIEM integration scripts.
