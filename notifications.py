import os
import requests
from dotenv import load_dotenv

load_dotenv()

class WhatsAppNotifier:
    """Handles sending real-time security alerts via WhatsApp."""
    
    @staticmethod
    def send_incident_alert(attack, severity, source, description):
        """Sends a formatted incident alert with interactive options."""
        # Config
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        from_whatsapp = os.environ.get("TWILIO_WHATSAPP_ID", "whatsapp:+14155238886") # Default Twilio Sandbox
        to_whatsapp = os.environ.get("ADMIN_WHATSAPP")
        
        message_body = (
            f"🚨 *CCL GUARD: NEW INCIDENT*\n\n"
            f"*Attack:* {attack}\n"
            f"*Severity:* {severity}\n"
            f"*Source:* {source}\n\n"
            f"*Insight:* {description[:150]}...\n\n"
            f"--- ACTION REQUIRED ---\n"
            f"Reply *ANALYZE* for deep forensics.\n"
            f"Reply *ACTION* to isolate the host.\n"
            f"Reply *IGNORE* to suppress."
        )

        if not account_sid or not auth_token or not to_whatsapp:
            print("[WHATSAPP MOCK] No API keys found. Simulating message...")
            print("-" * 30)
            print(message_body)
            print("-" * 30)
            return True

        try:
            # Twilio API call
            from twilio.rest import Client
            client = Client(account_sid, auth_token)
            
            message = client.messages.create(
                body=message_body,
                from_=from_whatsapp,
                to=f"whatsapp:{to_whatsapp}"
            )
            print(f"[WHATSAPP] Alert sent successfully. SID: {message.sid}")
            return True
        except ImportError:
            print("[WHATSAPP ERROR] 'twilio' library not installed. Mocking...")
            print(message_body)
            return False
        except Exception as e:
            print(f"[WHATSAPP ERROR] Failed to send alert: {e}")
            return False

def send_incident_alert(attack, severity, source, description):
    """Facade for easy integration."""
    return WhatsAppNotifier.send_incident_alert(attack, severity, source, description)
