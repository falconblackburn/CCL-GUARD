import sqlite3
import random
from core.database import DB_NAME

def format_time(seconds):
    if not seconds: return "0s"
    m = int(seconds // 60)
    s = int(seconds % 60)
    if m > 0:
        return f"{m} min {s} sec"
    return f"{s} sec"

def calculate_metrics():
    """
    Calculates MTTD, MTTI, and MTTR.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # MTTI: Time from Incident creation to 'processed_time'
    # MTTR: Time from Incident creation to 'closed_time'
    
    c.execute("""
        SELECT 
            AVG(strftime('%s', filtered.processed_time) - strftime('%s', filtered.time)) as mtti,
            AVG(strftime('%s', filtered.closed_time) - strftime('%s', filtered.time)) as mttr
        FROM (
            SELECT time, processed_time, closed_time 
            FROM incidents 
            WHERE status='Closed' AND processed_time IS NOT NULL AND closed_time IS NOT NULL
            ORDER BY id DESC LIMIT 1000
        ) as filtered
    """)
    
    row = c.fetchone()
    conn.close()
    
    mtti_sec = row[0] if row[0] else 0
    mttr_sec = row[1] if row[1] else 0
    
    # Automated MTTD (Arrival to Detection) - Simulated in Seconds
    mttd_sec = random.randint(120, 300) 
    
    return {
        "mttd": format_time(mttd_sec),
        "mtti": format_time(mtti_sec),
        "mttr": format_time(mttr_sec)
    }
