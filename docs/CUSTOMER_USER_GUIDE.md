# 📖 CCL Guard: Customer User Guide

Welcome to **CCL Guard**, your AI-Powered Security Operations Center. This guide will help you navigate the platform and maximize its security potential.

## 1. The Executive Dashboard (Initial View)
When you log in, you are greeted with the **Intelligence Dashboard**. This is your "Command Center."

*   **Attack Distribution Chart:** See at a glance which types of threats are targeting your organization (e.g., SQL Injection, Brute Force).
*   **Security Posture Metrics:** Live counts of active incidents, blocked IPs, and global threat intel.
*   **Severity Filter:** Use this to isolate **Critical** threats that require your immediate attention.

## 2. Managing Incidents
The **Incidents** tab is where the actual investigation happens.
*   **AI Summary:** For every attack, our AI provides a plain-English explanation of *what happened* and *how risky* it is.
*   **Remediation Steps:** CCL Guard doesn't just find problems; it tells you how to fix them. Follow the step-by-step instructions provided for each incident.
*   **Audit Trail:** Every action taken by your analysts is recorded, ensuring accountability and meeting compliance requirements.

## 3. Threat Hunting & Intelligence
*   **Threat Hunting History:** See a historical timeline of all detection activities.
*   **Live Feeds:** CCL Guard pulls real-world data from global security feeds (like URLHaus) to warn you about new malicious websites before your users click them.
*   **Brand Protection:** Monitor for leaked corporate data or "squatter" domains trying to impersonate your brand.

## 4. Reporting for Leadership
At the top of the dashboard, you can click **"Generate Executive Report"**. 
*   This creates a professional PDF with automated charts and summaries. 
*   **Use this for:** Weekly security briefings or Board of Directors meetings.

## 5. Taking Action (SOC Specialist Tools)
If a threat is verified:
1.  Click **"Analyze"** on the incident.
2.  Input your findings in the **"Analyst Comments"** box.
3.  Click **"Mark as Resolved"** once the threat is mitigated.

## 6. How to Verify it's Working (3-Minute Test)
You can test the system's live detection by simulating a safe security event:

1.  **Open two PowerShell windows.**
2.  In **Window 1**, start the monitoring agent:
    ```powershell
    .\.venv\Scripts\python.exe lightweight_agent.py
    ```
3.  In **Window 2**, create a "fake attack" file in the same folder:
    ```powershell
    "SELECT * FROM users WHERE id = 'admin' OR 1=1" > security_alert.txt
    ```
4.  **Watch the Magic:** 
    *   Window 1 will show: `[!] Security event detected...`
    *   Refresh your browser Dashboard. You will see a new **SQL Injection** incident appear with a full **AI Analysis** and response plan!

---
**CCL Guard:** *Protecting your enterprise with Intelligence-Driven Defense.*
