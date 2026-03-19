# CCL Guard: Full System Testing Guide

This guide ensures that all "Agentic" components of the SOC—from multi-agent reasoning to interactive WhatsApp alerts—are functioning correctly.

## 1. Prerequisites
- **AI Backend**: Ollama running locally (`llama3`) or a valid `GEMINI_API_KEY` in `.env`.
- **Database**: Initialized and populated with test data (using `generate_test_data.py`).
- **Twilio (Optional for WhatsApp)**: Configured credentials in `.env` if testing real mobile alerts.

## 2. Testing the "Autonomous Loop"
### Step A: Trigger Log Analysis
1. Navigate to the **Dashboard**.
2. Find any log in the "Live Threat Intelligence" table.
3. Click the **Analyze** button.
4. **Verification**: Observe the "AI THREAT ANALYSIS" panel. It should perform a multi-agent investigation (Triage -> Forensics -> Response) and provide remediation steps.

### Step B: Human-on-the-Loop Approval
1. Go to the **Incidents** tab.
2. Open an 'Open' incident row.
3. Click **Approve Action**.
4. **Verification**: The incident status should change to 'Approved'. Check the database table `incidents` to see the `approved_action` column set to `1`.

## 3. Testing the "Learning Loop"
1. In an 'Open' incident, click **Correct AI**.
2. Provide a technical correction (e.g., "This appears to be a false positive from our internal vulnerability scanner.").
3. Submit the feedback.
4. **Verification**: The incident moves to 'Corrected'. Trigger a similar log analysis later; the AI should now consider this past feedback in its reasoning via its few-shot context.

## 4. Testing "Cross-Domain Correlation"
I have provided a master script to simulate a complex, multi-stage attack.
1. Run: `.venv/bin/python3 test_all.py`
2. Go to the dashboard and find the "Brute Force" log from `192.168.1.50` (User: `admin_jsmith`).
3. Click **Analyze**.
4. **Verification**: The AI should explicitly mention the correlation with the "Data Discovery" activity on the AWS host from the same user.

## 5. Testing WhatsApp Alerts
1. Ensure your `.env` has the correct `ADMIN_WHATSAPP`.
2. Run: `.venv/bin/python3 verify_whatsapp.py`
3. **Verification**: Check your phone for a formatted alert. If you've set up a Cloudflare Tunnel, reply with `ANALYZE` and check the application logs for the webhook response.

---
*For support or to report bugs, contact the SOC Engineering team.*
