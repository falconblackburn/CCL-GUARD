## 1. Prerequisites on Windows Server
*   **Python 3.10 - 3.12 (Recommended)**: 
    > [!WARNING]
    > You are using **Python 3.14**, which is a "Developer/Experimental" version. Many libraries (like `matplotlib`) do not have ready-to-use installers for this version yet, which is why it is trying to "compile" and failing. **Please install Python 3.12 for a smooth experience.**
*   **Ollama (for AI)**: If you want to test the AI Remediation feature, install [Ollama for Windows](https://ollama.com/download/windows).
*   **Permissions**: Ensure you have Administrator rights to modify Firewall rules (if testing the "Block IP" feature).

## 2. One-Click Setup
Open PowerShell as Administrator in the project folder and run:
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force ; 
.\setup_windows.ps1
```
This script handles the heavy lifting: creating a Python environment, installing libraries, and generating test data.

## 4. Remote Testing (From your MacBook)
**First, run this on the Windows Server to open the door:**
```powershell
New-NetFirewallRule -DisplayName "CCL Guard SOC" -Direction Inbound -LocalPort 5001 -Protocol TCP -Action Allow
```

To verify that your Windows Server SOC can receive data from the outside world:

### A. The "API Attack" (Fastest)
Run this command in your **MacBook Terminal** (replace `[SERVER-IP]` with your Windows Server IP):
```bash
curl -X POST http://[SERVER-IP]:5001/api/v2/ingest \
-H "Content-Type: application/json" \
-d '{"source": "MacBook-Scanner", "log": "SQL-INJECTION-TEST: SELECT * FROM users WHERE id=1 OR 1=1"}'
```
*Go to your Windows Dashboard: You should see a high-severity alert from "MacBook-Scanner".*

### B. Network Scan (If using `sensor.py`)
If you have `sensor.py` running on Windows, run this from your Mac:
```bash
nmap -Pn -sV [SERVER-IP]
```
*This will trigger "Port Scanning" alerts on the dashboard.*

Open PowerShell as Administrator and run:
```powershell
.\.venv\Scripts\python.exe app.py
```
2.  **Remote Access**: To see it from *another* computer (like your laptop):
    *   Open Windows Firewall.
    *   Add an "Inbound Rule" for Port **5001**.
    *   Connect via `http://[SERVER-IP]:5001`.

## 4. Verification Checklist
Run these tests to confirm "Customer Readiness":
- [ ] **Data Check**: Does the dashboard show exactly 11 incidents and 20 logs?
- [ ] **Filter Check**: Does selecting "Critical" isolate the red-badged threats?
- [ ] **AI Check**: Click "Analyze" on an incident. (Requires Ollama running).
- [ ] **Report Check**: Click "Executive Report" and verify the `SOC_Report.pdf` is generated in the `reports/` folder.
- [ ] **Block Test**: (Optional) Click "Resolve" on an incident. If you provide a comment and submit, check if a new rule appears in `Windows Defender Firewall with Advanced Security`.

## 5. Simulating a "Real" Victim
Run the agent on a *different* Windows machine in your network:
1.  Copy `lightweight_agent.py` to that machine.
2.  Change `SOC_INGEST_URL` to point to your Virtual Server's IP.
3.  Create a file called `security_alert.txt` and type `Hacker detected!`.
4.  Watch the dashboard on the server—an incident should appear within seconds.

---
**Windows specific note:** If you see any errors related to `scapy`, you may need to install [Npcap](https://npcap.com/) for the network sensor to work.
