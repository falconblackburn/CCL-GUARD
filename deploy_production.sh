#!/bin/bash

# CCL Guard Production Deployment & Scaling Script
# This script automates the setup of Cloudflare Tunnels (cloudflared) for Secure Webhooks.

echo "🚀 Starting CCL Guard Production Deployment..."

# 1. Install cloudflared (MacOS/Linux check)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v cloudflared &> /dev/null; then
        echo "Installing cloudflared via Homebrew..."
        brew install cloudflared
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! command -v cloudflared &> /dev/null; then
        echo "Installing cloudflared for Linux..."
        curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
        chmod +x cloudflared
        sudo mv cloudflared /usr/local/bin/
    fi
fi

# 2. Authentication (Manual step required)
echo "--------------------------------------------------"
echo "STEP 1: Cloudflare Authentication"
echo "A browser window will open. Log in to your Cloudflare account to authorize this tunnel."
echo "--------------------------------------------------"
cloudflared tunnel login

# 3. Create Tunnel
TUNNEL_NAME="ccl-guard-$(hostname)"
echo "Creating tunnel: $TUNNEL_NAME..."
cloudflared tunnel create $TUNNEL_NAME

# 4. Generate Configuration
mkdir -p ~/.cloudflared
CONFIG_FILE="$HOME/.cloudflared/config.yaml"
TUNNEL_ID=$(cloudflared tunnel list | grep $TUNNEL_NAME | awk '{print $1}')

echo "Generating config.yaml..."
cat <<EOF > $CONFIG_FILE
tunnel: $TUNNEL_ID
credentials-file: $HOME/.cloudflared/$TUNNEL_ID.json

ingress:
  - hostname: soc-alert.yourdomain.com
    service: http://localhost:5001
  - service: http_status:404
EOF

echo "Done! Configuration saved to $CONFIG_FILE"

# 5. Routing
echo "--------------------------------------------------"
echo "STEP 2: Setup DNS Routing"
echo "Please run: cloudflared tunnel route dns $TUNNEL_NAME soc-alert.yourdomain.com"
echo "--------------------------------------------------"

# 6. Service Persistence
echo "Setting up cloudflared as a system service..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    sudo cloudflared service install
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo cloudflared service install
fi

echo "--------------------------------------------------"
echo "PRODUCTION READY!"
echo "Your SOC is now reachable at: https://soc-alert.yourdomain.com"
echo "Update your Twilio Webhook to: https://soc-alert.yourdomain.com/api/whatsapp/webhook"
echo "--------------------------------------------------"
