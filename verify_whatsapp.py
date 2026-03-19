import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from database import create_incident, init_db

def test_whatsapp_trigger():
    print("Initializing test database...")
    init_db()
    
    print("\nTriggering a test incident to verify WhatsApp notification...")
    attack = "SQL Injection (Test)"
    severity = "Critical"
    risk = 99
    phase = "Exploitation"
    ai_summary = "Test AI analysis detecting malicious payload on sensitive endpoint."
    remediation = "1. Block IP\n2. Patch application"
    source = "Test Agent"
    
    create_incident(attack, severity, risk, phase, ai_summary, remediation, source)
    print("\nTest complete. Check the console for '[WHATSAPP MOCK]' output.")

if __name__ == "__main__":
    test_whatsapp_trigger()
