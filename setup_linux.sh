#!/bin/bash

# CCL GUARD - Linux Installation Wizard
# Supported: Ubuntu, Debian, CentOS, RHEL (Systemd based)

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}--------------------------------------------------${NC}"
echo -e "${CYAN}       CCL GUARD - Multi-Tenant SOC Setup        ${NC}"
echo -e "${CYAN}--------------------------------------------------${NC}"

# 1. Dependency Check
echo -e "\n[*] Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "[-] Python 3 not found. Please install it first."
    exit 1
fi

# 2. Virtual Environment
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

# 3. Install Requirements
echo "[*] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Initialize Database
echo "[*] Initializing clean database..."
python3 -c "from database import init_db; init_db()"
python3 app.py --init-only &>/dev/null # Ensure admin user exists

# 5. Service Persistence (Systemd)
echo -e "\n${YELLOW}[?] Would you like to install CCL Guard as background services (systemd)? (y/n)${NC}"
read -r choice
if [ "$choice" == "y" ]; then
    CUR_DIR=$(pwd)
    USER_NAME=$(whoami)
    PYTHON_BIN="$CUR_DIR/venv/bin/python3"

    function create_service {
        NAME=$1
        DESC=$2
        EXEC=$3
        echo "[*] Creating systemd service: $NAME..."
        sudo bash -c "cat <<EOF > /etc/systemd/system/$NAME.service
[Unit]
Description=$DESC
After=network.target

[Service]
User=$USER_NAME
WorkingDirectory=$CUR_DIR
ExecStart=$PYTHON_BIN $EXEC
Restart=always

[Install]
WantedBy=multi-user.target
EOF"
        sudo systemctl daemon-reload
        sudo systemctl enable $NAME
        sudo systemctl start $NAME
    }

    create_service "ccl-guard-app" "CCL Guard Main App" "app.py"
    create_service "ccl-guard-director" "CCL Guard Director Dashboard" "parent_app.py"
    create_service "ccl-guard-agent" "CCL Guard Monitoring Agent" "lightweight_agent.py"

    # Fortinet Ingestion Prompt
    echo -e "\n${YELLOW}[?] Do you want to enable live Fortinet log ingestion on UDP 5140? (y/n)${NC}"
    read -r forti_choice
    if [ "$forti_choice" == "y" ]; then
        create_service "ccl-guard-fortinet" "CCL Guard Fortinet Ingestor" "fortinet_sync.py --live"
        echo "[*] Ensuring UDP 5140 is open (assuming UFW)..."
        sudo ufw allow 5140/udp &>/dev/null
    fi

    sudo ufw allow 5001/tcp &>/dev/null
    sudo ufw allow 5005/tcp &>/dev/null

    echo -e "\n${GREEN}[+] All CCL Guard services are now running in the background!${NC}"
fi

echo -e "\n${GREEN}[SUCCESS] Setup Complete!${NC}"
echo -e "Visit: ${CYAN}http://$(hostname -I | awk '{print $1}'):5001${NC} to begin your Executive Tour."
