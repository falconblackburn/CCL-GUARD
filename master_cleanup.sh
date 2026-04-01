#!/bin/bash

# CCL GUARD - Linux Master Cleanup Utility
# Purges all data and logs for a 100% fresh installation.

RED='\033[0;31m'
NC='\033[0m'
YELLOW='\033[1;33m'

echo -e "${RED}[!] WARNING! This will delete ALL logs and database data!${NC}"
echo -e "${YELLOW}[?] Are you sure you want to continue? (y/n)${NC}"
read -r choice
if [ "$choice" != "y" ]; then
    exit 0
fi

# 1. Stop all Services
echo "[*] Stopping systemd services..."
sudo systemctl stop ccl-guard-app ccl-guard-director ccl-guard-fortinet ccl-guard-agent 2>/dev/null

# 2. Kill orphan python processes
echo "[*] Killing remaining python processes..."
pkill -f "python3 app.py"
pkill -f "python3 parent_app.py"
pkill -f "python3 fortinet_sync.py"
pkill -f "python3 lightweight_agent.py"

# 3. Purge Data
echo "[*] Deleting SOC Database..."
rm -f soc.db

# 4. Purge Logs
echo "[*] Deleting all log files..."
rm -rf *.log
rm -rf logs/

# 5. Re-initialize
echo "[*] Resetting to clean state..."
if [ -d "venv" ]; then
    ./venv/bin/python3 -c "from database import init_db; init_db()"
fi

echo -e "\n${RED}[SUCCESS] System has been deeply cleaned!${NC}"
echo -e "You can now run ./setup_linux.sh for a fresh installation."
