import sqlite3
import datetime
from pathlib import Path

# Database setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "campaign_history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            country TEXT,
            total_leads INTEGER,
            sent INTEGER,
            failed INTEGER,
            skipped INTEGER
        )
    """)
    conn.commit()
    conn.close()

def log_campaign(country: str, total_leads: int, sent: int, failed: int, skipped: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO campaigns (timestamp, country, total_leads, sent, failed, skipped)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.datetime.now(), country, total_leads, sent, failed, skipped))
    conn.commit()
    conn.close()

def get_recent_campaigns(limit=50):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Ordered by newest first
    cursor.execute("""
        SELECT id, timestamp, country, total_leads, sent, failed, skipped 
        FROM campaigns 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    campaigns = []
    for row in rows:
        campaigns.append({
            "id": row[0],
            "timestamp": row[1],
            "country": row[2],
            "total_leads": row[3],
            "sent": row[4],
            "failed": row[5],
            "skipped": row[6]
        })
    return campaigns
