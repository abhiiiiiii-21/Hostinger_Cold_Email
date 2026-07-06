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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_id TEXT UNIQUE,
            email TEXT,
            company TEXT,
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            opened_at DATETIME,
            open_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def create_campaign_log(country: str, total_leads: int, email_target: str = "email") -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO campaigns (timestamp, country, total_leads, sent, failed, skipped, email_target)
        VALUES (?, ?, ?, 0, 0, 0, ?)
    """, (datetime.datetime.now(), country, total_leads, email_target))
    campaign_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return campaign_id

def update_campaign_log(campaign_id: int, sent: int, failed: int, skipped: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE campaigns
        SET sent = ?, failed = ?, skipped = ?
        WHERE id = ?
    """, (sent, failed, skipped, campaign_id))
    conn.commit()
    conn.close()

def get_recent_campaigns(limit=50):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Ordered by newest first, include opens count
    cursor.execute("""
        SELECT c.id, c.timestamp, c.country, c.total_leads, c.sent, c.failed, c.skipped,
               (SELECT COUNT(*) FROM email_tracking e WHERE e.campaign_id = c.id AND e.open_count > 0) AS opens,
               c.email_target
        FROM campaigns c
        ORDER BY c.timestamp DESC 
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
            "skipped": row[6],
            "opens": row[7],
            "email_target": row[8] if len(row) > 8 else "email"
        })
    return campaigns

def log_email_sent(tracking_id: str, email: str, company: str, campaign_id: int = None, website_review: str = "", recipient_name: str = ""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO email_tracking (tracking_id, email, company, sent_at, campaign_id, website_review, recipient_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (tracking_id, email, company, datetime.datetime.now(), campaign_id, website_review, recipient_name))
    conn.commit()
    conn.close()

def log_email_opened(tracking_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE email_tracking 
        SET open_count = open_count + 1, opened_at = ?
        WHERE tracking_id = ?
    """, (datetime.datetime.now(), tracking_id))
    conn.commit()
    conn.close()

def get_tracking_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tracking_id, email, company, sent_at, opened_at, open_count
        FROM email_tracking
        ORDER BY sent_at DESC
        LIMIT 100
    """)
    rows = cursor.fetchall()
    conn.close()
    
    tracking_data = []
    for row in rows:
        tracking_data.append({
            "tracking_id": row[0],
            "email": row[1],
            "company": row[2],
            "sent_at": row[3],
            "opened_at": row[4],
            "open_count": row[5]
        })
    return tracking_data

def get_today_opens():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Query distinct opens for today. We consider 'today' based on sent_at date.
    cursor.execute("""
        SELECT COUNT(*)
        FROM email_tracking
        WHERE open_count > 0 AND date(sent_at) = date('now', 'localtime')
    """)
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_campaign_tracking(campaign_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tracking_id, email, company, sent_at, opened_at, open_count, website_review, recipient_name
        FROM email_tracking
        WHERE campaign_id = ?
        ORDER BY sent_at DESC
    """, (campaign_id,))
    rows = cursor.fetchall()
    conn.close()
    
    tracking_data = []
    for row in rows:
        tracking_data.append({
            "tracking_id": row[0],
            "email": row[1],
            "company": row[2],
            "sent_at": row[3],
            "opened_at": row[4],
            "open_count": row[5],
            "website_review": row[6],
            "recipient_name": row[7]
        })
    return tracking_data
