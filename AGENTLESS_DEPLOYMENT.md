# 🛰️ CCL Guard: Agentless Deployment Guide

An **Agentless Deployment** means you can protect your entire office without installing software on every individual computer. This is ideal for large organizations or for monitoring devices like printers, cameras, and firewalls.

## 1. Method: Centralized Syslog Clearinghouse
Most enterprise hardware (Firewalls, Switches, Routers) can send "Syslog" data.
*   **The Setup:** Configure your Core Firewall (Cisco, Fortinet, etc.) to forward logs to the CCL Guard server's IP address.
*   **The Bridge:** CCL Guard can be configured to act as a Syslog receiver. It catches these logs, uses AI to analyze them, and displays results on the dashboard instantly.
*   **Benefit:** Zero software installed on user devices.

## 2. Method: Network Traffic Sniffing (IDS Mode)
By using the included `sensor.py` script on a "Network Tap" or "Mirror Port":
*   **How it works:** Your network switch sends a copy of *all* office traffic to the CCL Guard server.
*   **AI Analysis:** CCL Guard looks for patterns like SQL Injection or Port Scanning in the raw traffic.
*   **Benefit:** Complete visibility into every device on the network without touching a single end-user machine.

## 3. Method: Cloud-Native Ingestion (AWS/Azure/GCP)
If your office uses cloud services, you can push logs directly to the CCL Guard API.
*   **Cloud Function:** Use an AWS Lambda or Azure Function to trigger whenever a security alert occurs in the cloud.
*   **API Push:** The function sends a simple JSON message to: `http://[YOUR-IP]:5001/api/v2/ingest`.
*   **Payload Example:**
    ```json
    {
      "source": "AWS GuardDuty",
      "log": "Unauthorized access attempt detected in SSH on production server."
    }
    ```

## Summary of Agentless Value
| Feature | Agent-Based | Agentless |
| :--- | :--- | :--- |
| **Ease of Deployment** | Manual install on each PC | One-time network config |
| **Coverage** | Specific monitored PCs | Entire network segment |
| **Visibility** | Deep system-level logs | Wide network & service logs |
| **Best For** | High-risk laptops/servers | Guest Wi-Fi, Cloud, IoT |
