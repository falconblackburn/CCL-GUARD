# CCL GUARD - Master Cleanup Utility (Windows)
# This script will purge all existing data and logs for a 100% fresh installation.

# Robust paths
$RootPath = Split-Path -Parent $PSScriptRoot
Set-Location $RootPath

# 1. Stop all CCL Guard Background Tasks
Write-Host "[*] Stopping background services..." -ForegroundColor Cyan
schtasks /end /tn "CCL_Guard_App" 2>$null
schtasks /end /tn "CCL_Guard_Director" 2>$null
schtasks /end /tn "CCL_Guard_Fortinet" 2>$null
schtasks /end /tn "CCL_Guard_Agent" 2>$null

# 2. Kill any remaining Python processes
Write-Host "[*] Terminating any orphan Python processes..." -ForegroundColor Cyan
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue

# 3. Purge Database
Write-Host "[*] Deleting SOC Database (soc.db)..." -ForegroundColor Yellow
if (Test-Path "soc.db") { Remove-Item "soc.db" -Force }

# 4. Purge Diagnostic Logs
Write-Host "[*] Deleting all log files..." -ForegroundColor Yellow
Get-ChildItem -Path . -Filter "*.log" | Remove-Item -Force
if (Test-Path "logs/") { Remove-Item "logs/*" -Force -Recurse }

# 5. Re-initialize Environment
Write-Host "[*] Re-initializing clean state..." -ForegroundColor Cyan
# Running app.py briefly will recreate the clean database with the admin user
Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "app.py" -NoNewWindow
Start-Sleep -Seconds 5
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue

Write-Host "`n[SUCCESS] System has been deep-cleaned!" -ForegroundColor Green
Write-Host "All old deployments and logs have been removed." -ForegroundColor Green
Write-Host "You can now run setup_windows.ps1 for a fresh installation." -ForegroundColor Cyan
