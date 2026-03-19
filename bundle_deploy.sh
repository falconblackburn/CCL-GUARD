#!/bin/bash
# CCL Guard - Lightweight Deployment Bundler

echo "🚀 Creating CCL Guard Deployment Package..."

# Define the package name
PACKAGE_NAME="CCL_Guard_Deploy_$(date +%F).zip"

# Use the existing project directory
TARGET_DIR="."

# Remove any old deployment zips
rm -rf CCL_Guard_Deploy_*.zip

# Create a zip while EXCLUDING bulky directories and logs
echo "📦 Compressing source code (Excluding bulky files)..."
zip -r "$PACKAGE_NAME" . \
    -x "./venv/*" \
    -x "./.venv/*" \
    -x "*/venv/*" \
    -x "*/.venv/*" \
    -x "*/__pycache__/*" \
    -x "*.log" \
    -x "*.db" \
    -x "app_log.txt" \
    -x "parent_log.txt" \
    -x "zi*" \
    -x "reports/*" \
    -x "reports_test/*" \
    -x ".git/*" \
    -x "node_modules/*" \
    -x "*.pdf" \
    -x "*.png" \
    -x ".DS_Store" \
    -x "*.zip" \
    -x "CCL_Guard_Final_Deploy/*" \
    -x "CCL_Guard_Lite_v4/*"

echo "✅ Package Created: $PACKAGE_NAME"
echo "📏 Size: $(du -sh $PACKAGE_NAME | cut -f1)"
echo ""
echo "💡 INSTRUCTION FOR CLIENT:"
echo "1. Send this ZIP file to the client."
echo "2. Client extracts the ZIP."
echo "3. Client runs 'python -m venv .venv' and 'pip install -r requirements.txt' locally."
echo "4. This ensures the transfer is 1MB instead of 400MB."
