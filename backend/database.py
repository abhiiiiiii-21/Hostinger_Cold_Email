import psycopg2
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            country TEXT,
            total_leads INTEGER,
            sent INTEGER,
            failed INTEGER,
            skipped INTEGER,
            email_target TEXT DEFAULT 'email'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_tracking (
            id SERIAL PRIMARY KEY,
            tracking_id TEXT UNIQUE,
            email TEXT,
            company TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            opened_at TIMESTAMP,
            open_count INTEGER DEFAULT 0,
            campaign_id INTEGER,
            website_review TEXT,
            recipient_name TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS success_logs (
            id SERIAL PRIMARY KEY,
            company TEXT,
            email TEXT,
            subject TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS failed_logs (
            id SERIAL PRIMARY KEY,
            company TEXT,
            email TEXT,
            subject TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT,
            error TEXT
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def create_campaign_log(country: str, total_leads: int, email_target: str = "email") -> int:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO campaigns (timestamp, country, total_leads, sent, failed, skipped, email_target)
        VALUES (%s, %s, %s, 0, 0, 0, %s)
        RETURNING id
    """, (datetime.datetime.now(), country, total_leads, email_target))
    campaign_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return campaign_id

def update_campaign_log(campaign_id: int, sent: int, failed: int, skipped: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE campaigns
        SET sent = %s, failed = %s, skipped = %s
        WHERE id = %s
    """, (sent, failed, skipped, campaign_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_recent_campaigns(limit=50):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.timestamp, c.country, c.total_leads, c.sent, c.failed, c.skipped,
               (SELECT COUNT(*) FROM email_tracking e WHERE e.campaign_id = c.id AND e.open_count > 0) AS opens,
               c.email_target
        FROM campaigns c
        ORDER BY c.timestamp DESC 
        LIMIT %s
    """, (limit,))
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    campaigns = []
    for row in rows:
        campaigns.append({
            "id": row[0],
            "timestamp": row[1].isoformat() if row[1] else None,
            "country": row[2],
            "total_leads": row[3],
            "sent": row[4],
            "failed": row[5],
            "skipped": row[6],
            "opens": row[7],
            "email_target": row[8]
        })
    return campaigns

def log_email_sent(tracking_id: str, email: str, company: str, campaign_id: int = None, website_review: str = "", recipient_name: str = ""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO email_tracking (tracking_id, email, company, sent_at, campaign_id, website_review, recipient_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (tracking_id, email, company, datetime.datetime.now(), campaign_id, website_review, recipient_name))
    conn.commit()
    cursor.close()
    conn.close()

def log_email_opened(tracking_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE email_tracking 
        SET open_count = open_count + 1, opened_at = %s
        WHERE tracking_id = %s
    """, (datetime.datetime.now(), tracking_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_tracking_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tracking_id, email, company, sent_at, opened_at, open_count
        FROM email_tracking
        ORDER BY sent_at DESC
        LIMIT 100
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    tracking_data = []
    for row in rows:
        tracking_data.append({
            "tracking_id": row[0],
            "email": row[1],
            "company": row[2],
            "sent_at": row[3].isoformat() if row[3] else None,
            "opened_at": row[4].isoformat() if row[4] else None,
            "open_count": row[5]
        })
    return tracking_data

def get_dashboard_stats():
    conn = get_db()
    cursor = conn.cursor()
    
    stats = {"today": 0, "yesterday": 0, "month": 0, "today_opens": 0, "yesterday_opens": 0, "month_opens": 0}
    
    # Today sent (IST timezone correction)
    cursor.execute("SELECT COUNT(*) FROM success_logs WHERE DATE(timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = DATE(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')")
    stats["today"] = cursor.fetchone()[0]
    
    # Yesterday sent (IST timezone correction)
    cursor.execute("SELECT COUNT(*) FROM success_logs WHERE DATE(timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = DATE(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata') - INTERVAL '1 day'")
    stats["yesterday"] = cursor.fetchone()[0]
    
    # Month sent (IST timezone correction)
    cursor.execute("SELECT COUNT(*) FROM success_logs WHERE date_trunc('month', timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = date_trunc('month', CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')")
    stats["month"] = cursor.fetchone()[0]
    
    # Today opens (IST timezone correction)
    cursor.execute("SELECT COUNT(*) FROM email_tracking WHERE open_count > 0 AND DATE(sent_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = DATE(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')")
    stats["today_opens"] = cursor.fetchone()[0]

    # Yesterday opens (IST timezone correction)
    cursor.execute("SELECT COUNT(*) FROM email_tracking WHERE open_count > 0 AND DATE(sent_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = DATE(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata') - INTERVAL '1 day'")
    stats["yesterday_opens"] = cursor.fetchone()[0]

    # Month opens (IST timezone correction)
    cursor.execute("SELECT COUNT(*) FROM email_tracking WHERE open_count > 0 AND date_trunc('month', sent_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = date_trunc('month', CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')")
    stats["month_opens"] = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    return stats

def get_campaign_tracking(campaign_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tracking_id, email, company, sent_at, opened_at, open_count, website_review, recipient_name
        FROM email_tracking
        WHERE campaign_id = %s
        ORDER BY sent_at DESC
    """, (campaign_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    tracking_data = []
    for row in rows:
        tracking_data.append({
            "tracking_id": row[0],
            "email": row[1],
            "company": row[2],
            "sent_at": row[3].isoformat() if row[3] else None,
            "opened_at": row[4].isoformat() if row[4] else None,
            "open_count": row[5],
            "website_review": row[6],
            "recipient_name": row[7]
        })
    return tracking_data
