# CCL GUARD - Master Deployment Guide (v2.0)

This guide provides the definitive step-by-step process for deploying the AI SOC platform in a client environment. The application is now **Production-Ready** and verified for high-volume (5M+ log) scenarios.

---

## 🚀 PHASE 1: Environment Preparation
Ensure the server (Windows or Linux) meets these minimum requirements:
- **Python 3.10+** (Required)
- **Git** (Required for updates)
- **Ports Open:** 5001 (Main UI), 5005 (Director), 5140 (Syslog UDP)

---

## 🧹 PHASE 2: Deep Clean (For Re-deployments)
If resetting an existing client environment, run the cleanup utility **first**:

**Windows:** `.\master_cleanup.ps1`
**Linux:** `./master_cleanup.sh`

---

## 📦 PHASE 3: Automated Installation
Clone the repository and run the platform-specific wizard.

### **Option A: Windows Server**
1. Open PowerShell as **Administrator**.
2. Run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\setup_windows.ps1
```
3. Follow the prompts to install as a **Background Service**.

### **Option B: Linux Server**
1. Open Terminal as **Root**.
2. Run:
```bash
chmod +x setup_linux.sh
./setup_linux.sh
```
3. Follow the prompts to enable **Systemd** services.

---

## 🛡️ PHASE 4: Fortinet Log Ingestion

### **1. Live Log Streaming**
During the installation wizard, select **'y'** to enable Fortinet Ingestion.
- **Config:** Point the FortiGate Syslog server to the SOC IP on **UDP Port 5140**.
- **Service:** The `CCL_Guard_Fortinet` service handles this in the background.

### **2. Historical Log Import**
If the client has legacy logs (e.g., `logs.txt`), use the import utility:
```bash
# Windows
.\.venv\Scripts\python.exe fortinet_sync.py --import-file "C:\path\to\logs.txt"

# Linux
./venv/bin/python3 fortinet_sync.py --import-file "/path/to/logs.txt"
```

---

## 🏆 PHASE 5: Client Hand-off
1. Visit `http://<server-ip>:5001`
2. **First Login:** Use `admin` / `admin123`.
3. **Executive Tour:** The system will automatically launch the **Interactive Onboarding Tour**.
4. **Verified Status:** All AI remediation, incident triggering, and database windowing are active by default.

---
**CONVERSION CONFIRMED:** The application is stable and ready for live production use.
