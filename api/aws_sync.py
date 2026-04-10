import os
import time
import sqlite3
import datetime

# Conditional import so the app doesn't crash if boto3 isn't installed
try:
    import boto3
except ImportError:
    boto3 = None

from core.database import insert_log, DB_NAME, create_incident

def aws_worker():
    """Background thread to poll AWS GuardDuty for new findings."""
    aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    aws_region = os.environ.get("AWS_REGION", "us-east-1")
    
    if not aws_access_key or not aws_secret_key or not boto3:
        return # Missing credentials or boto3, exit silently
        
    print("[AWS GuardDuty] Sync worker initialized.")
    
    # Simple state tracking (in memory for this implementation)
    processed_finding_ids = set()
    
    try:
        client = boto3.client(
            'guardduty',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # We need a Detector ID to query GuardDuty
        response = client.list_detectors()
        detector_ids = response.get('DetectorIds', [])
        if not detector_ids:
            print("[AWS GuardDuty] No active detectors found.")
            return
            
        detector_id = detector_ids[0]
        
    except Exception as e:
        print(f"[AWS GuardDuty] Failed to connect: {e}")
        return

    while True:
        try:
            # List findings created in the last 15 minutes
            five_mins_ago = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=15)).timestamp() * 1000
            
            response = client.list_findings(
                DetectorId=detector_id,
                FindingCriteria={
                    'Criterion': {
                        'updatedAt': {
                            'Gte': int(five_mins_ago)
                        }
                    }
                }
            )
            
            finding_ids = response.get('FindingIds', [])
            new_ids = [fid for fid in finding_ids if fid not in processed_finding_ids]
            
            if new_ids:
                findings_response = client.get_findings(
                    DetectorId=detector_id,
                    FindingIds=new_ids
                )
                
                for finding in findings_response.get('Findings', []):
                    # Extract details
                    title = finding.get('Title', 'Unknown AWS Threat')
                    desc = finding.get('Description', '')
                    sev_num = finding.get('Severity', 1.0)
                    
                    # Map AWS Severity (1-10) to CCL Guard Severity
                    if sev_num >= 7.0:
                        mapped_sev = "Critical"
                        risk = 95
                    elif sev_num >= 4.0:
                        mapped_sev = "High"
                        risk = 75
                    else:
                        mapped_sev = "Medium"
                        risk = 40
                        
                    # Attempt to extract an IP
                    ip = "AWS"
                    try:
                        action = finding.get('Service', {}).get('Action', {})
                        if 'NetworkConnectionAction' in action:
                            ip = action['NetworkConnectionAction']['RemoteIpDetails']['IpAddressV4']
                        elif 'AwsApiCallAction' in action:
                            ip = action['AwsApiCallAction']['RemoteIpDetails']['IpAddress']
                    except Exception:
                        pass
                        
                    # Insert into Database
                    con = sqlite3.connect(DB_NAME)
                    c = con.cursor()
                    # Just passing the raw description as the 'raw log'
                    insert_log(ip, desc[:200], title, mapped_sev, risk)
                    
                    if risk >= 80:
                        create_incident(ip, title, mapped_sev, "Suspicious activity detected by AWS GuardDuty.", "Review IAM/Security Groups.")
                        
                    con.close()
                    processed_finding_ids.add(finding['Id'])
                    
                print(f"[AWS GuardDuty] Processed {len(new_ids)} new findings.")
                
        except Exception as e:
            print(f"[AWS GuardDuty] Error polling findings: {e}")
            
        time.sleep(300) # Poll every 5 minutes
