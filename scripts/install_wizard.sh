#!/bin/bash
echo "=========================================================="
echo "   CCL Guard - Automated Installer & Setup Wizard         "
echo "=========================================================="

echo ""
echo "[1/4] Installing Backend Dependencies..."
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

echo ""
echo "[2/4] AI Engine Configuration"
echo "To ensure you NEVER run out of credits, CCL Guard supports Ollama"
echo "which runs a powerful Cyber Security AI locally on your machine for FREE."
echo "If you don't have Ollama, you can download it from ollama.com."
echo ""
echo "1) Use Ollama (Local, 100% Free, Private)"
echo "2) Use Google Gemini (Cloud, API Key required)"
read -p "Choose AI Engine (1 or 2): " ai_choice

if [ "$ai_choice" == "1" ]; then
    echo "OLLAMA_MODEL=llama3" >> .env
    echo "✅ Selected Ollama (Free Local AI)."
else
    read -p "Enter your Gemini API Key: " gemini_key
    echo "GEMINI_API_KEY=$gemini_key" >> .env
    echo "✅ Selected Google Gemini."
fi

echo ""
echo "[3/4] WhatsApp Interactive Alerts (Twilio Sandbox)"
echo "Do you want to enable WhatsApp alerts? (y/n)"
read -p "Choice: " wa_choice

if [ "$wa_choice" == "y" ]; then
    read -p "Enter Twilio Account SID: " twilio_sid
    read -p "Enter Twilio Auth Token: " twilio_token
    read -p "Enter Your Mobile Number (e.g. +1234567890): " admin_wa
    
    echo "TWILIO_ACCOUNT_SID=$twilio_sid" >> .env
    echo "TWILIO_AUTH_TOKEN=$twilio_token" >> .env
    echo "TWILIO_WHATSAPP_ID=whatsapp:+14155238886" >> .env
    echo "ADMIN_WHATSAPP=$admin_wa" >> .env
    echo "✅ WhatsApp Configured."
fi

echo ""
echo "[4/6] Cloudflare WAF Log Ingestion (Optional)"
echo "CCL Guard can automatically pull firewall logs from your Cloudflare account."
read -p "Do you want to enable Cloudflare Log Ingestion? (y/n): " cf_choice

if [ "$cf_choice" == "y" ]; then
    read -p "Enter Cloudflare Account Email: " cf_email
    read -p "Enter Cloudflare Global API Key: " cf_api_key
    read -p "Enter Cloudflare Zone ID (for the domain you want to monitor): " cf_zone_id
    
    echo "CLOUDFLARE_EMAIL=$cf_email" >> .env
    echo "CLOUDFLARE_API_KEY=$cf_api_key" >> .env
    echo "CLOUDFLARE_ZONE_ID=$cf_zone_id" >> .env
    echo "✅ Cloudflare Log Ingestion Configured."
fi

echo ""
echo "[5/7] Enterprise SIEM & Cloud Integrations (Optional)"
echo "CCL Guard can seamlessly poll alerts from your existing enterprise platforms."
read -p "Do you want to configure native AWS, Azure, or Splunk ingestion? (y/n): " ent_choice

if [ "$ent_choice" == "y" ]; then
    echo "--- AWS GuardDuty ---"
    read -p "Enter AWS Access Key ID (Leave blank to skip AWS): " aws_key
    if [ -n "$aws_key" ]; then
        read -p "Enter AWS Secret Access Key: " aws_secret
        read -p "Enter AWS Region (e.g., us-east-1): " aws_region
        echo "AWS_ACCESS_KEY_ID=$aws_key" >> .env
        echo "AWS_SECRET_ACCESS_KEY=$aws_secret" >> .env
        echo "AWS_REGION=${aws_region:-us-east-1}" >> .env
        echo "✅ AWS GuardDuty Polling Configured."
    fi

    echo "--- Azure Monitor / Defender ---"
    read -p "Enter Azure Tenant ID (Leave blank to skip Azure): " az_tenant
    if [ -n "$az_tenant" ]; then
        read -p "Enter Azure Client ID: " az_client
        read -p "Enter Azure Client Secret: " az_secret
        echo "AZURE_TENANT_ID=$az_tenant" >> .env
        echo "AZURE_CLIENT_ID=$az_client" >> .env
        echo "AZURE_CLIENT_SECRET=$az_secret" >> .env
        echo "✅ Azure Defender Polling Configured."
    fi

    echo "--- Splunk SIEM ---"
    read -p "Enter Splunk Host URL (Leave blank to skip Splunk): " splunk_host
    if [ -n "$splunk_host" ]; then
        read -p "Enter Splunk API Token: " splunk_token
        echo "SPLUNK_HOST=$splunk_host" >> .env
        echo "SPLUNK_TOKEN=$splunk_token" >> .env
        echo "✅ Splunk SIEM Polling Configured."
    fi
fi

echo ""
echo "[6/7] Cloudflare Edge Security & Public Access"
echo "Setting up an automated secure tunnel for your SOC (No Port Forwarding needed)..."

if ! command -v cloudflared &> /dev/null; then
    echo "Installing cloudflared..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install cloudflared
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
        chmod +x cloudflared
        sudo mv cloudflared /usr/local/bin/
    fi
fi

echo "Starting Cloudflare Tunnel..."
cloudflared tunnel --url http://127.0.0.1:5001 > cloudflared.log 2>&1 &

echo "Waiting for Cloudflare to establish tunnel and generate public URL..."
public_url=""
max_attempts=20
attempt=1

while [ $attempt -le $max_attempts ]; do
    sleep 1
    # Check if the URL has appeared in the log
    if grep -q 'https://[a-zA-Z0-9-]*\.trycloudflare\.com' cloudflared.log; then
        public_url=$(grep -o 'https://[a-zA-Z0-9-]*\.trycloudflare\.com' cloudflared.log | head -1)
        break
    fi
    attempt=$((attempt + 1))
done

if [ -n "$public_url" ]; then
    echo "CLIENT_PUBLIC_URL=$public_url" >> .env
    echo "✅ Public URL Generated: $public_url"
else
    echo "⚠️ Failed to extract Cloudflare URL after 20 seconds. Check cloudflared.log."
fi


echo ""
echo "[7/7] Multi-Tenant Parent Registration"
echo "If this instance is managed by a centralized SOC team, enter the details below."
echo "Leave blank to run as a standalone, isolated SOC."
read -p "Client/Customer Name: " client_name
if [ -n "$client_name" ]; then
    read -p "Parent Server URL (e.g., https://director.cclguard.com): " parent_url
    
    echo "CLIENT_NAME=$client_name" >> .env
    echo "PARENT_SERVER_URL=$parent_url" >> .env
    echo "✅ Registered for Centralized Management."
fi

echo ""
echo "=========================================================="
echo " SETUP COMPLETE! 🎉"
echo " "
echo " ► START SOC: run 'nohup .venv/bin/python3 app.py &'"
if [ -n "$public_url" ]; then
    echo " ► WHATSAPP FIX: Ensure your Twilio Sandbox Webhook is set to:"
    echo "   $public_url/api/whatsapp/webhook"
fi
echo "=========================================================="
