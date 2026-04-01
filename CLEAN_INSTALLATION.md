# CCL GUARD - Fresh Client Installation Guide

Follow these steps to deploy a clean, production-ready instance of the AI SOC platform for a new client.

## 1. Environment Preparation
Ensure the server (Windows or Linux) has **Python 3.10+** and **Git** installed.

## 2. Deep Clean (Optional)
If you are reusing a previously deployed server and want to remove ALL old logs, incidents, and data, run the cleanup utility:
```powershell
.\master_cleanup.ps1
```
*This will terminate background services, delete `soc.db`, and purge diagnostic logs.*

## 3. Clone & Setup
Open PowerShell (as Administrator) or Terminal and run:
```bash
git clone https://github.com/falconblackburn/CCL-GUARD.git
cd CCL-GUARD
```

### Windows (Automated)
Run the master setup script:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\setup_windows.ps1
```
> [!TIP]
> When asked to install background services, select **'y'** to ensure the Main App, Director Dashboard, and Fortinet Sync start automatically on boot.

### Linux (Manual)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py # Initial run to create database
```

## 3. Configure Credentials
Create or edit the `.env` file in the root directory:
```env
GEMINI_API_KEY="your_api_key_here"
FLASK_SECRET_KEY="generate_a_random_string"
PARENT_SERVER_URL="https://your-director-url.com" # If using Multi-Tenant
CLIENT_NAME="Client_Company_Name"
```

## 4. Verify Clean State
1. **Database:** Confirm `soc.db` is present (the setup script initializes an empty one).
2. **Logs:** Delete any pre-existing `.log` files in the root directory to start fresh.
3. **Ports:** Ensure firewall access for:
   - **5001**: Client Dashboard (TCP)
   - **5005**: Director Dashboard (TCP)
   - **5140**: Fortinet Syslog (UDP)

## 5. First Run
Start the platform:
```bash
python app.py
```
Log in at `http://localhost:5001` with default credentials:
- **Username:** `admin`
- **Password:** `admin123`
*(Change password immediately under Settings)*
