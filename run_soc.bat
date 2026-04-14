@echo off
TITLE CCL Guard - AI SOC Platform
echo ==========================================================
echo    CCL Guard - Quick Launch (Windows)
echo ==========================================================
echo.

:: Check if virtual environment exists
if not exist ".venv" (
    echo [!] Virtual environment not found. Running setup wizard first...
    powershell -ExecutionPolicy Bypass -File "scripts\install_wizard.ps1"
)

:: Re-check after possible setup
if not exist ".venv" (
    echo.
    echo [ERROR] Virtual environment could not be created.
    echo Please ensure Python 3 is installed and added to your PATH.
    pause
    exit /b
)

echo [*] Starting AI SOC Dashboard...
".venv\Scripts\python.exe" app.py
pause
