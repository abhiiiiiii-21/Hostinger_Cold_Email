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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bounces (
            id SERIAL PRIMARY KEY,
            email TEXT,
            bounce_type TEXT,
            bounce_reason TEXT,
            date_bounced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            contact_name TEXT,
            city TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS replies (
            id SERIAL PRIMARY KEY,
            email TEXT,
            date_replied TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            subject TEXT
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
    
    stats = {
        "today": 0, "yesterday": 0, "month": 0, 
        "today_opens": 0, "yesterday_opens": 0, "month_opens": 0,
        "total_replies": 0, "reply_rate": 0, 
        "hard_bounce_rate": 0, "soft_bounce_rate": 0
    }
    
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
    
    # Total Replies
    cursor.execute("SELECT COUNT(*) FROM replies")
    stats["total_replies"] = cursor.fetchone()[0]

    # Total Sent (all time) for rate calculation
    cursor.execute("SELECT COUNT(*) FROM success_logs")
    total_sent = cursor.fetchone()[0]

    if total_sent > 0:
        stats["reply_rate"] = round((stats["total_replies"] / total_sent) * 100, 2)
        
        cursor.execute("SELECT COUNT(*) FROM bounces WHERE bounce_type = 'hard'")
        hard_bounces = cursor.fetchone()[0]
        stats["hard_bounce_rate"] = round((hard_bounces / total_sent) * 100, 2)
        
        cursor.execute("SELECT COUNT(*) FROM bounces WHERE bounce_type = 'soft'")
        soft_bounces = cursor.fetchone()[0]
        stats["soft_bounce_rate"] = round((soft_bounces / total_sent) * 100, 2)
    
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

def log_bounce(email: str, bounce_type: str, reason: str, contact_name: str = "", city: str = ""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bounces (email, bounce_type, bounce_reason, date_bounced, contact_name, city)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (email, bounce_type, reason, datetime.datetime.now(), contact_name, city))
    conn.commit()
    cursor.close()
    conn.close()

def is_hard_bounced(email: str) -> bool:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM bounces WHERE email = %s AND bounce_type = 'hard' LIMIT 1", (email,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None

def log_reply(email: str, date_replied, subject: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO replies (email, date_replied, subject)
        VALUES (%s, %s, %s)
    """, (email, date_replied, subject))
    conn.commit()
    cursor.close()
    conn.close()

def get_bounced_contacts():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT email, bounce_type, bounce_reason, date_bounced, contact_name, city
        FROM bounces
        ORDER BY date_bounced DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    bounces = []
    for row in rows:
        bounces.append({
            "email": row[0],
            "bounce_type": row[1],
            "bounce_reason": row[2],
            "date_bounced": row[3].isoformat() if row[3] else None,
            "contact_name": row[4],
            "city": row[5]
        })
    return bounces

def get_daily_trend_stats(days: int = 30):
    """Aggregates daily sent, opens, and replies from existing tables for the trend chart."""
    conn = get_db()
    cursor = conn.cursor()
    
    # days is always an integer so safe to format directly; PostgreSQL doesn't allow
    # parameterized INTERVAL values.
    days = int(days)
    
    cursor.execute(f"""
        WITH date_range AS (
            SELECT generate_series(
                (CURRENT_DATE AT TIME ZONE 'Asia/Kolkata') - INTERVAL '{days} days',
                (CURRENT_DATE AT TIME ZONE 'Asia/Kolkata'),
                '1 day'::interval
            )::date AS day
        ),
        daily_sent AS (
            SELECT DATE(timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') AS day, COUNT(*) AS sent
            FROM success_logs
            WHERE timestamp >= (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata' - INTERVAL '{days} days')
            GROUP BY day
        ),
        daily_opens AS (
            SELECT DATE(opened_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') AS day, COUNT(*) AS opens
            FROM email_tracking
            WHERE open_count > 0 AND opened_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata' - INTERVAL '{days} days')
            GROUP BY day
        ),
        daily_replies AS (
            SELECT DATE(date_replied AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') AS day, COUNT(*) AS replies
            FROM replies
            WHERE date_replied >= (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata' - INTERVAL '{days} days')
            GROUP BY day
        )
        SELECT 
            dr.day,
            COALESCE(ds.sent, 0) AS sent,
            COALESCE(dop.opens, 0) AS opens,
            COALESCE(drp.replies, 0) AS replies
        FROM date_range dr
        LEFT JOIN daily_sent ds ON dr.day = ds.day
        LEFT JOIN daily_opens dop ON dr.day = dop.day
        LEFT JOIN daily_replies drp ON dr.day = drp.day
        ORDER BY dr.day ASC
    """)
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [
        {
            "date": row[0].isoformat(),
            "sent": row[1],
            "opens": row[2],
            "replies": row[3]
        }
        for row in rows
    ]

