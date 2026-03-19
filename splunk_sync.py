import os
import time
import sqlite3

try:
    import requests
except ImportError:
    requests = None

from database import insert_log, DB_NAME, create_incident

def splunk_worker():
    """Background thread to poll Splunk Enterprise/Cloud for high-fidelity alerts."""
    splunk_host = os.environ.get("SPLUNK_HOST") # e.g. https://splunk.corp.local:8089
    splunk_token = os.environ.get("SPLUNK_TOKEN")
    
    if not splunk_host or not splunk_token or not requests:
        return # Missing credentials, exit silently
        
    print("[Splunk] Sync worker initialized.")
    
    # In a real scenario, we'd track the latest indexed time to avoid duplicates
    
    headers = {
        "Authorization": f"Bearer {splunk_token}"
    }
    
    # We query for notable events or specific high severity alerts
    search_query = "search index=notable severity=high OR severity=critical | head 10"
    
    while True:
        try:
            # Splunk REST API search workflow (simplified for demonstration)
            # Create a search job
            job_response = requests.post(
                f"{splunk_host}/services/search/jobs",
                headers=headers,
                data={"search": search_query, "output_mode": "json"},
                verify=False, # Often self-signed inner certificates
                timeout=10
            )
            
            if job_response.status_code == 201:
                sid = job_response.json().get('sid')
                
                # Wait for job to finish (ideally should poll, just adding a small sleep here)
                time.sleep(3)
                
                # Fetch results
                results_response = requests.get(
                    f"{splunk_host}/services/search/jobs/{sid}/results?output_mode=json",
                    headers=headers,
                    verify=False,
                    timeout=10
                )
                
                if results_response.status_code == 200:
                    results = results_response.json().get('results', [])
                    
                    if results:
                        con = sqlite3.connect(DB_NAME)
                        for event in results:
                            # Map Splunk fields to CCL Guard
                            ip = event.get('src_ip', event.get('src', 'Splunk'))
                            attack = event.get('signature', event.get('rule_name', 'Splunk Alert'))
                            raw_log = event.get('_raw', str(event))[:200]
                            severity = event.get('severity', 'High').capitalize()
                            
                            risk = 85 if severity == 'Critical' else 75
                            
                            insert_log(ip, raw_log, attack, severity, risk)
                            
                            if risk >= 80:
                                create_incident(ip, attack, severity, "Alert escalated from Splunk SIEM.", "Investigate in Splunk.")
                                
                        con.close()
                        print(f"[Splunk] Processed {len(results)} alerts.")
                        
        except Exception as e:
            print(f"[Splunk] Error polling alerts: {e}")
            
        time.sleep(300) # Poll every 5 minutes
