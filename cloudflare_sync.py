import os
import time
import requests
import datetime
from database import insert_log

def fetch_cloudflare_logs():
    email = os.environ.get("CLOUDFLARE_EMAIL")
    api_key = os.environ.get("CLOUDFLARE_API_KEY")
    zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")

    if not email or not api_key or not zone_id:
        return

    url = "https://api.cloudflare.com/client/v4/graphql"
    headers = {
        "X-Auth-Email": email,
        "X-Auth-Key": api_key,
        "Content-Type": "application/json"
    }

    # Fetch last 24 hours
    since = (datetime.datetime.utcnow() - datetime.timedelta(hours=24)).isoformat() + "Z"

    query = """
    query($zoneTag: string, $limit: int, $since: datetime) {
      viewer {
        zones(filter: { zoneTag: $zoneTag }) {
          firewallEventsAdaptive(
            filter: { datetime_geq: $since }
            limit: $limit
            orderBy: [datetime_DESC]
          ) {
            action
            clientIP
            clientCountryName
            datetime
            rayName
            ruleId
            source
            userAgent
          }
        }
      }
    }
    """
    
    variables = {
        "zoneTag": zone_id,
        "limit": 50,
        "since": since
    }

    try:
        response = requests.post(url, headers=headers, json={"query": query, "variables": variables})
        if response.status_code == 200:
            data = response.json()
            zones = data.get("data", {}).get("viewer", {}).get("zones", [])
            if zones:
                events = zones[0].get("firewallEventsAdaptive", [])
                for evt in events:
                    ip = evt.get("clientIP", "Unknown")
                    country = evt.get("clientCountryName", "Unknown")
                    action = evt.get("action", "unknown")
                    rule = evt.get("ruleId", "WAF Rule")
                    
                    attack_type = f"CF {action.capitalize()}"
                    severity = "High" if action in ["block", "challenge", "jschallenge"] else "Low"
                    risk = 80 if severity == "High" else 20
                    
                    raw_data = f"CF Ray: {evt.get('rayName')} | Rule: {rule} | UA: {evt.get('userAgent')}"
                    
                    insert_log("Cloudflare", ip, country, raw_data, attack_type, severity, risk, "T1190", 
                               "Edge protection triggered by Cloudflare.", f"Review rule {rule}", 90, "Delivery")
                
                print(f"[CLOUDFLARE] Synced {len(events)} edge events.")
        else:
            print(f"[CLOUDFLARE ERROR] {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[CLOUDFLARE ERROR] Sync failed: {e}")

def cloudflare_worker():
    """Background thread to poll Cloudflare logs continuously."""
    while True:
        try:
            fetch_cloudflare_logs()
        except Exception as e:
            pass
        time.sleep(300) # Poll every 5 minutes
