#!/bin/bash

# CCL Guard - Automated Setup Script
# This script prepares the environment and runs the application.

echo "------------------------------------------------"
echo "   🛡️  CCL Guard - Intelligence-Driven SOC"
echo "------------------------------------------------"
echo "[*] Initializing setup..."

# 1. Check for Python
if ! command -v python3 &> /dev/null
then
    echo "[!] Error: python3 could not be found. Please install Python 3."
    exit 1
fi

# 2. Create Virtual Environment
echo "[*] Creating virtual environment (.venv)..."
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Dependencies
echo "[*] Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Initialize Database & Demo Data
echo "[*] Initializing database and generating demo data..."
python3 generate_test_data.py

# 5. Generate Secret Key if not exists
if [ -z "$FLASK_SECRET_KEY" ]; then
    export FLASK_SECRET_KEY=$(python3 -c 'import os; print(os.urandom(24).hex())')
    echo "[*] Generated dynamic FLASK_SECRET_KEY."
fi

# 6. Final Instructions
echo "------------------------------------------------"
echo "[+] Setup Complete!"
echo "[*] To start the server, run:"
echo "    source .venv/bin/activate && python3 app.py"
echo "------------------------------------------------"
echo "[*] Starting the server now..."
python3 app.py
