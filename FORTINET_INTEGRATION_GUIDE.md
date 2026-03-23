# 🏢 Fortinet Firewall Integration Guide

This guide explains how to connect your office's Fortinet Firewall (FortiGate) to the CCL Guard SOC. This allows CCL Guard to actively analyze attacks hitting your physical firewall and block them globally.

## 🕰️ Option 1: Importing Historical (Old) Logs
If you want to view logs from last week or test the platform before making it live, you can import an old text log file retrieved from your FortiGate or FortiAnalyzer.

1. Export your Fortigate logs from your firewall dashboard to a Text/CSV file (e.g., `forti_logs_march.txt`).
2. Move that file onto the computer or server running CCL Guard.
3. Run the import command:
   ```bash
   python3 fortinet_sync.py --import-file forti_logs_march.txt
   ```
   *The script will instantly parse the old firewall events, categorize their severity, and populate your SOC Dashboard with the historical attacks.*

---

## ⚡ Option 2: Live Log Streaming (Real-Time)
To turn CCL Guard into an active, live SOC for your office, you need to configure your FortiGate to stream Syslogs directly to the server running CCL Guard.

### Step 1: Start the CCL Guard Receiver
If you are running CCL Guard via Docker (`docker-compose up -d`), Port `5140 (UDP)` is already exposed and ready!

Just open a terminal on your server and tell the Sync module to start listening:
```bash
python3 fortinet_sync.py --live
```

### Step 2: Configure the FortiGate
Log into your FortiGate Firewall Admin Dashboard.

**Via the Web UI (GUI):**
1. Go to **Log & Report** > **Log Settings**.
2. Enable **Send logs to syslog**.
3. Set the **IP Address/FQDN** to the local IP address of the computer running CCL Guard (e.g., `192.168.1.100`).
4. Set the **Port** to `5140`.
5. Click **Apply**.

**Via the CLI (Terminal):**
You can also configure this by opening the FortiGate CLI and typing:
```text
config log syslogd setting
    set status enable
    set server "YOUR_CCL_GUARD_SERVER_IP"
    set port 5140
    set facility local7
end
```

### Step 3: Watch the Attacks Roll In!
Once configured, any time the FortiGate detects a blocked Intrusion (IPS), Malware, or Web Filter violation, it will beam the log to Port 5140. `fortinet_sync.py` will catch it, process it, and instantly drop it into your Client Dashboard table!
