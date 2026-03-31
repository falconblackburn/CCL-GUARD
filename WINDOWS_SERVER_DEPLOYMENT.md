# CCL GUARD - Windows Server Deployment Guide

This guide describes how to deploy the CCL Guard AI-powered SOC platform on a Windows Server environment for professional customer demonstrations and production use.

## Prerequisites

1.  **Python 3.10+**: Download and install from [python.org](https://www.python.org/).
    *   > [!IMPORTANT]
    *   > Ensure you check the box **"Add Python to PATH"** during installation.
2.  **Git**: Install [Git for Windows](https://git-scm.com/download/win).
3.  **Administrator Access**: Required to open firewall ports and create background tasks.

## Step 1: Clone the Repository
Open PowerShell and run:
```powershell
cd C:\
git clone <your-repository-url> CCL-Guard
cd CCL-Guard
```

## Step 2: Automated Configuration
Run the provided setup script to create the virtual environment and install dependencies:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\setup_windows.ps1
```

## Step 3: Configure Environment Variables
Edit the `.env` file in the root directory:
```env
GEMINI_API_KEY="your_api_key_here"
USE_AI="true"
OLLAMA_MODEL="llama3" # Optional local backup
```

## Step 4: High Availability (Background Services)
The `setup_windows.ps1` script will ask if you want to install the application as a background service. 
- **CCL_Guard_App**: Main Dashboard (Port 5001)
- **CCL_Guard_Director**: Multi-Tenant Manager (Port 5005)
- **CCL_Guard_Fortinet**: Live Syslog Receiver (Port 5140)

If you select **'y'**, these will start automatically on server boot and running in the background.

## Step 5: Firewall Optimization
The setup script automatically opens Port 5001. If you need to access other ports remotely, use:
```powershell
New-NetFirewallRule -DisplayName "CCL Guard Director" -Direction Inbound -LocalPort 5005 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "CCL Guard Syslog" -Direction Inbound -LocalPort 5140 -Protocol UDP -Action Allow
```

## Troubleshooting
- **Logs not appearing?** Check if `fortinet_sync.py` is running and the firewall is allowing UDP 5140.
- **AI errors?** Ensure your `GEMINI_API_KEY` is valid and you have an active internet connection.
