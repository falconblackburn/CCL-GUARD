# CCL Guard - Windows Server Setup Script
# This script automates the installation of dependencies and environment setup on Windows.

# Robust paths
$RootPath = Split-Path -Parent $PSScriptRoot
Set-Location $RootPath

Write-Host "[*] Starting CCL Guard Windows Setup..." -ForegroundColor Cyan

# 1. Check for Python (try python, python3, then py)
$PythonCmd = $null
foreach ($cmd in "python", "python3", "py") {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $PythonCmd = $cmd
        break
    }
}

if (-not $PythonCmd) {
    Write-Host "[!] Python not found! Please ensure Python is installed and added to PATH." -ForegroundColor Red
    Write-Host "[*] Tip: Check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    exit
}

Write-Host "[*] Using Python command: $PythonCmd" -ForegroundColor Gray

# 2. Create Virtual Environment
Write-Host "[*] Creating virtual environment (.venv)..."
& $PythonCmd -m venv .venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Failed to create venv." -ForegroundColor Red
    exit
}

# 3. Install Dependencies
Write-Host "[*] Installing dependencies from requirements.txt..."
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip

# Use --only-binary to avoid needing a C++ compiler on the server
& ".\.venv\Scripts\pip.exe" install -r requirements.txt --only-binary=:all:

if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Failed to install binary dependencies." -ForegroundColor Yellow
    Write-Host "[*] Retrying standard install for remaining packages..." -ForegroundColor Gray
    & ".\.venv\Scripts\pip.exe" install -r requirements.txt
}
Write-Host "[+] Dependencies installed successfully." -ForegroundColor Green

# 4. Initialize Database & Generate Demo Data
Write-Host "[*] Initializing database and generating demo data..."
& ".\.venv\Scripts\python.exe" tests/generate_test_data.py

# 5. Generate Secret Key
if (-not $env:FLASK_SECRET_KEY) {
    $Bytes = New-Object Byte[] 24
    [Reflection.Assembly]::LoadWithPartialName("System.Security") | Out-Null
    $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::Create()
    $rng.GetBytes($Bytes)
    $SecretKey = [System.Convert]::ToHexString($Bytes)
    $env:FLASK_SECRET_KEY = $SecretKey
    Write-Host "[*] Generated dynamic FLASK_SECRET_KEY."
}

# 5. Production Persistence: Create Background Tasks
Write-Host "`n[?] Would you like to install CCL Guard as a background service? (y/n)" -ForegroundColor Cyan
$Choice = Read-Host
if ($Choice -eq "y") {
    $CurrentDir = Get-Location
    $PythonPath = "$CurrentDir\.venv\Scripts\python.exe"
    
    # Task 1: Main Platform (Port 5001)
    Write-Host "[*] Creating background task for CCL Guard App..."
    schtasks /create /tn "CCL_Guard_App" /tr "$PythonPath $CurrentDir\app.py" /sc onstart /ru SYSTEM /rl HIGHEST /f
    schtasks /run /tn "CCL_Guard_App" # Start immediately
    
    # Task 2: Director Dashboard (Port 5005)
    Write-Host "[*] Creating background task for CCL Guard Director..."
    schtasks /create /tn "CCL_Guard_Director" /tr "$PythonPath $CurrentDir\parent_app.py" /sc onstart /ru SYSTEM /rl HIGHEST /f
    schtasks /run /tn "CCL_Guard_Director" # Start immediately

    # Task 3: Fortinet Syslog Receiver (UDP 5140)
    Write-Host "`n[?] Do you want to enable live Fortinet log ingestion on UDP 5140? (y/n)" -ForegroundColor Cyan
    $FortiChoice = Read-Host
    if ($FortiChoice -eq "y") {
        Write-Host "[*] Creating background task for Fortinet Sync..."
        schtasks /create /tn "CCL_Guard_Fortinet" /tr "$PythonPath $CurrentDir\api\fortinet_sync.py --live" /sc onstart /ru SYSTEM /rl HIGHEST /f
        schtasks /run /tn "CCL_Guard_Fortinet" # Start immediately
        Write-Host "[*] Configuring Firewall for Fortinet Syslog (UDP 5140)..."
        New-NetFirewallRule -DisplayName "CCL Guard Syslog" -Direction Inbound -LocalPort 5140 -Protocol UDP -Action Allow -ErrorAction SilentlyContinue
    }
    
    # Task 4: Monitoring Agent
    Write-Host "[*] Creating background task for CCL Guard Agent..."
    schtasks /create /tn "CCL_Guard_Agent" /tr "$PythonPath $CurrentDir\scripts\lightweight_agent.py" /sc onstart /ru SYSTEM /rl HIGHEST /f
    schtasks /run /tn "CCL_Guard_Agent" # Start immediately
    
    # Global Firewall Rules
    Write-Host "[*] Configuring Firewall for Web Dashboards..."
    New-NetFirewallRule -DisplayName "CCL Guard SOC" -Direction Inbound -LocalPort 5001 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName "CCL Guard Director" -Direction Inbound -LocalPort 5005 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue

    Write-Host "`n[+] All CCL Guard services have been started and configured for persistence!" -ForegroundColor Green
}

Write-Host "`n[SUCCESS] Setup Complete!" -ForegroundColor Green
Write-Host "The application is now running as a background service." -ForegroundColor Green
Write-Host "Visit: http://localhost:5001 to begin your Executive Tour." -ForegroundColor Cyan
