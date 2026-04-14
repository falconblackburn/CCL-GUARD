# 🖥️ CCL Guard: Windows Server Installation Guide

This guide provides a comprehensive, professional workflow for deploying the CCL Guard AI SOC platform on Windows Server 2019, 2022, or higher.

---

## 📋 1. Prerequisites

Before beginning the installation, ensure the following are installed and configured:

1.  **Python 3.10 or Higher**:
    - Download from [python.org](https://www.python.org/downloads/windows/).
    - **CRITICAL**: Check the box **"Add Python to PATH"** during installation.
2.  **Git for Windows**:
    - Download from [git-scm.com](https://git-scm.com/download/win).
3.  **Administrator Privileges**:
    - You must run PowerShell as an Administrator to configure Firewall rules and Scheduled Tasks.

---

## ⚡ 2. Automated Installation (Easiest)

We provide an interactive Setup Wizard that automates environment creation, AI selection, and persistent background task registration.

1.  **Download/Clone the Repository**:
    ```powershell
    git clone https://github.com/your-repo/CCL-GUARD.git
    cd CCL-GUARD
    ```
2.  **Run the Installer**:
    Right-click `scripts\install_wizard.ps1` and select **"Run with PowerShell"**, or run centrally from an Admin terminal:
    ```powershell
    .\scripts\install_wizard.ps1
    ```
3.  **Follow the Prompts**:
    - The wizard will create your virtual environment and install all dependencies.
    - It will help you configure your AI Engine (Ollama for Local or Gemini for Cloud).
    - It will automatically register the SOC as a **Windows Startup Task** so it runs in the background even after a reboot.

---

## 🛠️ 3. Manual Enterprise Installation (Step-by-Step)

For highly secured or customized environments, follow these manual steps:

### A. Environment Setup
```powershell
# Navigate to project root
cd CCL-GUARD

# Create Virtual Environment
python -m venv .venv

# Activate and Install Dependencies
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### B. Database Initialization
```powershell
python tests/generate_test_data.py
```

### C. Configuration
Create a `.env` file in the project root with the following essential keys:
```env
FLASK_SECRET_KEY="your_secure_random_string"
CLIENT_PORT=5001
DIRECTOR_PORT=5005
# AI_ENGINE_CHOICE examples: OLLAMA or GEMINI
GEMINI_API_KEY="your_key_here"
```

### D. Production Hosting with NSSM (Recommended)
While we provide a "Scheduled Task" option in the wizard, professional enterprise environments often prefer **NSSM (Non-Sucking Service Manager)** to run apps as a Windows Service.

1.  Download [NSSM](https://nssm.cc/download).
2.  In an Administrator terminal:
    ```powershell
    nssm.exe install CCL_Guard_SOC
    ```
3.  **Path**: `C:\Path\To\CCL-GUARD\.venv\Scripts\python.exe`
4.  **Startup Directory**: `C:\Path\To\CCL-GUARD`
5.  **Arguments**: `app.py`
6.  Set **Startup Type** to `Automatic`.

---

## 🧱 4. Firewall Configuration

For the SOC to be accessible from other machines on the network, you must open the following Inbound ports:

- **SOC Dashboard**: `5001` (TCP)
- **Director Dashboard**: `5005` (TCP)
- **Fortinet Syslog Receiver**: `5140` (UDP)

**Quick PowerShell Command (Admin)**:
```powershell
New-NetFirewallRule -DisplayName "CCL Guard SOC" -Direction Inbound -LocalPort 5001 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "CCL Guard Director" -Direction Inbound -LocalPort 5005 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "CCL Guard Syslog" -Direction Inbound -LocalPort 5140 -Protocol UDP -Action Allow
```

---

## 🔍 5. Troubleshooting & Support

| Issue | Solution |
| :--- | :--- |
| **Scripts Disabled** | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| **Port 5001 in Use** | Kill any existing python processes or change `CLIENT_PORT` in `.env`. |
| **Aesthetics Missing** | Ensure `static/executive.css` is correctly loaded. Hard refresh browser (Ctrl+F5). |
| **DB Errors** | Ensure the user running the service has Read/Write permissions to `soc.db`. |

---
> [!IMPORTANT]
> Always ensure your Windows Server is patched and that Python is kept up to date to maintain security integrity.
