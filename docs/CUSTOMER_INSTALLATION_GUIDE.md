# 🚀 CCL Guard: Customer Installation Guide

Deploying CCL Guard is a fully automated process designed to take less than 5 minutes. Follow these steps to set up the SOC on a customer environment.

## 1. Prerequisites
- **Windows Server** (2019/2022) or **Windows 10/11** Pro/Enterprise.
- **PowerShell** (Running as Administrator).
- **Internet Connection** (For Cloudflare Tunneling).

## 2. One-Click Installation
1.  **Download the Package**: Extract the CCL Guard folder to the desired location (e.g., `C:\CCL-Guard-SOC`).
2.  **Run the Installer**:
    -   Right-click `install_wizard.ps1` and select **"Run with PowerShell"**.
    -   *Crucial:* Ensure you run this as **Administrator**.
3.  **Configure Environment**:
    -   The script will ask for your **Client Name** (e.g., "MegaCorp-MainOffice").
    -   Enter your **Director Dashboard URL** when prompted.
    -   (Optional) Provide API keys for Gemini, Twilio, or Cloudflare if you want local integrations active.

## 3. Background Automation (Stealth Mode)
Once the installer finishes:
-   The application will **automatically launch in the background**.
-   It is registered as a **Windows Scheduled Task** named `CCL_Guard_SOC`.
-   It will **automatically restart** whenever the system reboots.
-   No terminal windows will remain open, ensuring it doesn't interrupt the customer's work.

## 4. Verification
1.  Open the **Director Dashboard**.
2.  Check the "Fleet Overview" section.
3.  Your new client instance should appear as **"Online"** within 60 seconds.

---
**Support:** For technical assistance during deployment, contact the CCL Global Support Team.
