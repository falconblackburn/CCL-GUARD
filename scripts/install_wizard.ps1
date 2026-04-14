Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   CCL Guard - Automated Installer & Setup Wizard (Windows)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Robust paths
$RootPath = Split-Path -Parent $PSScriptRoot
Set-Location $RootPath

# Helper to update/set .env values cleanly
function Update-Env($key, $value) {
    if (-not $value) { return }
    $envFile = Join-Path $RootPath ".env"
    if (Test-Path $envFile) {
        if (Select-String -Path $envFile -Pattern "^$key=") {
            (Get-Content $envFile) -replace "^$key=.*", "$key=$value" | Set-Content $envFile
            return
        }
    }
    Add-Content -Path $envFile -Value "$key=$value"
}

Write-Host ""
Write-Host "[1/4] Installing Backend Dependencies..." -ForegroundColor Yellow

# Robust Python Detection
$pythonCmd = ""
$pythonArgs = @("-m", "venv", ".venv")

if (Get-Command "py" -ErrorAction SilentlyContinue) { 
    $pythonCmd = "py"
    $pythonArgs = @("-3") + $pythonArgs
}
elseif (Get-Command "python" -ErrorAction SilentlyContinue) { $pythonCmd = "python" }
elseif (Get-Command "python3" -ErrorAction SilentlyContinue) { $pythonCmd = "python3" }

if (-not $pythonCmd) {
    Write-Host "❌ Python is not installed or not in PATH. Please install Python 3 and try again." -ForegroundColor Red
    Pause
    Exit
}

Write-Host "Using Python command: $pythonCmd"
& $pythonCmd $pythonArgs
if (-not (Test-Path ".venv")) {
    Write-Host "❌ Failed to create virtual environment." -ForegroundColor Red
    Pause
    Exit
}

# Activate and Install
& ".\.venv\Scripts\pip.exe" install -r requirements.txt

Write-Host ""
Write-Host "[2/4] AI Engine Configuration" -ForegroundColor Yellow
Write-Host "To ensure you NEVER run out of credits, CCL Guard supports Ollama"
Write-Host "which runs a powerful Cyber Security AI locally on your machine for FREE."
Write-Host "If you don't have Ollama, you can download it from ollama.com."
Write-Host ""
Write-Host "1) Use Ollama (Local, 100% Free, Private)"
Write-Host "2) Use Google Gemini (Cloud, API Key required)"
$ai_choice = Read-Host "Choose AI Engine (1 or 2)"

    Update-Env "OLLAMA_MODEL" "llama3"
    Write-Host "✅ Selected Ollama (Free Local AI)." -ForegroundColor Green
} else {
    Update-Env "GEMINI_API_KEY" $gemini_key
    Write-Host "✅ Selected Google Gemini." -ForegroundColor Green
}

Write-Host ""
Write-Host "[3/4] WhatsApp Interactive Alerts (Twilio Sandbox)" -ForegroundColor Yellow
$wa_choice = Read-Host "Do you want to enable WhatsApp alerts? (y/n)"

if ($wa_choice -eq "y") {
    $twilio_sid = Read-Host "Enter Twilio Account SID"
    $twilio_token = Read-Host "Enter Twilio Auth Token"
    $admin_wa = Read-Host "Enter Your Mobile Number (e.g. +1234567890)"
    
    Update-Env "TWILIO_ACCOUNT_SID" $twilio_sid
    Update-Env "TWILIO_AUTH_TOKEN" $twilio_token
    Update-Env "TWILIO_WHATSAPP_ID" "whatsapp:+14155238886"
    Update-Env "ADMIN_WHATSAPP" $admin_wa
    Write-Host "✅ WhatsApp Configured." -ForegroundColor Green
}

Write-Host ""
Write-Host "[4/6] Cloudflare WAF Log Ingestion (Optional)" -ForegroundColor Yellow
Write-Host "CCL Guard can automatically pull firewall logs from your Cloudflare account."
$cf_choice = Read-Host "Do you want to enable Cloudflare Log Ingestion? (y/n)"

if ($cf_choice -eq "y") {
    $cf_email = Read-Host "Enter Cloudflare Account Email"
    $cf_api_key = Read-Host "Enter Cloudflare Global API Key"
    $cf_zone_id = Read-Host "Enter Cloudflare Zone ID (for the domain you want to monitor)"
    
    Update-Env "CLOUDFLARE_EMAIL" $cf_email
    Update-Env "CLOUDFLARE_API_KEY" $cf_api_key
    Update-Env "CLOUDFLARE_ZONE_ID" $cf_zone_id
    Write-Host "✅ Cloudflare Log Ingestion Configured." -ForegroundColor Green
}

Write-Host ""
Write-Host "[5/7] Enterprise SIEM & Cloud Integrations (Optional)" -ForegroundColor Yellow
Write-Host "CCL Guard can seamlessly poll alerts from your existing enterprise platforms."
$ent_choice = Read-Host "Do you want to configure native AWS, Azure, or Splunk ingestion? (y/n)"

if ($ent_choice -eq "y") {
    Write-Host "--- AWS GuardDuty ---" -ForegroundColor Cyan
    $aws_key = Read-Host "Enter AWS Access Key ID (Leave blank to skip AWS)"
    if ([string]::IsNullOrWhiteSpace($aws_key) -eq $false) {
        $aws_secret = Read-Host "Enter AWS Secret Access Key"
        $aws_region = Read-Host "Enter AWS Region (e.g., us-east-1)"
        if ([string]::IsNullOrWhiteSpace($aws_region)) { $aws_region = "us-east-1" }
        Update-Env "AWS_ACCESS_KEY_ID" $aws_key
        Update-Env "AWS_SECRET_ACCESS_KEY" $aws_secret
        Update-Env "AWS_REGION" $aws_region
        Write-Host "✅ AWS GuardDuty Polling Configured." -ForegroundColor Green
    }

    Write-Host "--- Azure Monitor / Defender ---" -ForegroundColor Cyan
    $az_tenant = Read-Host "Enter Azure Tenant ID (Leave blank to skip Azure)"
    if ([string]::IsNullOrWhiteSpace($az_tenant) -eq $false) {
        $az_client = Read-Host "Enter Azure Client ID"
        $az_secret = Read-Host "Enter Azure Client Secret"
        Update-Env "AZURE_TENANT_ID" $az_tenant
        Update-Env "AZURE_CLIENT_ID" $az_client
        Update-Env "AZURE_CLIENT_SECRET" $az_secret
        Write-Host "✅ Azure Defender Polling Configured." -ForegroundColor Green
    }

    Write-Host "--- Splunk SIEM ---" -ForegroundColor Cyan
    $splunk_host = Read-Host "Enter Splunk Host URL (Leave blank to skip Splunk)"
    if ([string]::IsNullOrWhiteSpace($splunk_host) -eq $false) {
        $splunk_token = Read-Host "Enter Splunk API Token"
        Update-Env "SPLUNK_HOST" $splunk_host
        Update-Env "SPLUNK_TOKEN" $splunk_token
        Write-Host "✅ Splunk SIEM Polling Configured." -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "[6/7] Cloudflare Edge Security & Public Access" -ForegroundColor Yellow
Write-Host "Setting up an automated secure tunnel for your SOC (No Port Forwarding needed)..."

# Ensure cloudflared is accessible
$cloudflaredCmd = Get-Command "cloudflared" -ErrorAction SilentlyContinue
if (-not $cloudflaredCmd) {
    if (-not (Test-Path "$PSScriptRoot\cloudflared.exe")) {
        Write-Host "Downloading Cloudflared..."
        Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "$PSScriptRoot\cloudflared.exe"
    }
    $cloudflaredPath = "$PSScriptRoot\cloudflared.exe"
} else {
    $cloudflaredPath = $cloudflaredCmd.Source
}

# Start Cloudflared in background and log to file
Write-Host "Starting Cloudflare Tunnel..." -ForegroundColor Yellow
$logFile = Join-Path $PSScriptRoot "cloudflared.log"
if (Test-Path $logFile) { Remove-Item $logFile }

# Run without showing a window, redirect stderr to log
Start-Process -NoNewWindow -FilePath $cloudflaredPath -ArgumentList "tunnel --url http://127.0.0.1:5001" -RedirectStandardError $logFile

Write-Host "Waiting for Cloudflare to establish tunnel and generate public URL..."
$public_url = ""
$pattern = "https://[a-zA-Z0-9-]+\.trycloudflare\.com"

for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $logFile) {
        $content = Get-Content $logFile -Raw
        if ($content -match $pattern) {
            $public_url = $matches[0]
            break
        }
    }
}

if ($public_url) {
    Write-Host "✅ Public URL Generated: $public_url" -ForegroundColor Green
    # Use a helper to update/set .env values cleanly
    function Update-Env($key, $value) {
        $envFile = Join-Path $RootPath ".env"
        if (Test-Path $envFile) {
            if (Select-String -Path $envFile -Pattern "^$key=") {
                (Get-Content $envFile) -replace "^$key=.*", "$key=$value" | Set-Content $envFile
                return
            }
        }
        Add-Content -Path $envFile -Value "$key=$value"
    }
    Update-Env "CLIENT_PUBLIC_URL" "`"$public_url`""
} else {
    Write-Host "⚠️ Failed to extract Cloudflare URL after 30 seconds." -ForegroundColor Red
    Write-Host "   You can still access the SOC locally at http://localhost:5001"
}

Write-Host ""
Write-Host "[7/7] Multi-Tenant Parent Registration" -ForegroundColor Yellow
Write-Host "If this instance is managed by a centralized SOC team, enter the details below."
$client_name = Read-Host "Project/Customer Name (Leave blank to skip)"

if ([string]::IsNullOrWhiteSpace($client_name) -eq $false) {
    $parent_url = Read-Host "Director Dashboard URL"
    Update-Env "CLIENT_NAME" "`"$client_name`""
    Update-Env "PARENT_SERVER_URL" "`"$parent_url`""
    Write-Host "✅ Registered for Centralized Management." -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " SETUP COMPLETE! 🎉" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " ► LOCAL ACCESS: http://localhost:5001"
if ($public_url) {
    Write-Host " ► PUBLIC ACCESS: $public_url"
}
Write-Host ""
Write-Host "► BACKGROUND SERVICE: Registering as a Windows Startup Task..." -ForegroundColor Yellow
$RootPath = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $RootPath ".venv\Scripts\python.exe"
$appPath = Join-Path $RootPath "app.py"
$taskName = "CCL_Guard_SOC"

try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    $action = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$appPath`"" -WorkingDirectory $RootPath
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden
    Register-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -TaskName $taskName -User "SYSTEM" -RunLevel Highest -Force
    Write-Host "✅ Registered Background Task: $taskName" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Task Registration failed (Run as Admin to fix)." -ForegroundColor Red
}

Write-Host ""
Write-Host "🚀 Launching CCL Guard SOC now..." -ForegroundColor Cyan
# Launch in a new command prompt window so the client can see the startup logs
Start-Process cmd -ArgumentList "/k `"$pythonPath`" `"$appPath`"" -WorkingDirectory $PSScriptRoot

Write-Host ""
Write-Host "Press any key to close this wizard..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
