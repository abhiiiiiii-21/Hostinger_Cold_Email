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
            email_target TEXT DEFAULT 'email',
            city TEXT DEFAULT 'NA',
            user_id TEXT
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
            recipient_name TEXT,
            email_subject TEXT,
            email_body TEXT,
            user_id TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS link_clicks (
            id SERIAL PRIMARY KEY,
            tracking_id TEXT,
            url TEXT,
            clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS success_logs (
            id SERIAL PRIMARY KEY,
            company TEXT,
            email TEXT,
            subject TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT,
            user_id TEXT
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
            error TEXT,
            user_id TEXT
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
            city TEXT,
            user_id TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS replies (
            id SERIAL PRIMARY KEY,
            email TEXT,
            date_replied TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            subject TEXT,
            user_id TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_emails (
            id SERIAL PRIMARY KEY,
            user_id TEXT,
            email TEXT,
            company TEXT,
            recipient_name TEXT,
            subject TEXT,
            body TEXT,
            attachments JSON,
            scheduled_at TIMESTAMP,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    
    # Safely add columns if they don't exist
    try:
        cursor.execute("ALTER TABLE email_tracking ADD COLUMN email_subject TEXT;")
    except psycopg2.Error:
        conn.rollback()
    
    try:
        cursor.execute("ALTER TABLE email_tracking ADD COLUMN email_body TEXT;")
    except psycopg2.Error:
        conn.rollback()

    try:
        cursor.execute("ALTER TABLE campaigns ADD COLUMN city TEXT DEFAULT 'NA';")
    except psycopg2.Error:
        conn.rollback()

    conn.commit()
    cursor.close()
    conn.close()

def create_campaign_log(country: str, city: str, total_leads: int, user_id: str, email_target: str = "email") -> int:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO campaigns (timestamp, country, city, total_leads, sent, failed, skipped, email_target, user_id)
        VALUES (%s, %s, %s, %s, 0, 0, 0, %s, %s)
        RETURNING id
    """, (datetime.datetime.now(), country, city, total_leads, email_target, user_id))
    campaign_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return campaign_id

def update_campaign_log(campaign_id: int, sent: int, failed: int, skipped: int, user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE campaigns
        SET sent = %s, failed = %s, skipped = %s
        WHERE id = %s AND user_id = %s
    """, (sent, failed, skipped, campaign_id, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_recent_campaigns(user_id: str, limit=50):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.timestamp, c.country, c.total_leads, c.sent, c.failed, c.skipped,
               (SELECT COUNT(*) FROM email_tracking e WHERE e.campaign_id = c.id AND e.open_count > 0) AS opens,
               c.email_target, c.city
        FROM campaigns c
        WHERE c.user_id = %s
        ORDER BY c.timestamp DESC 
        LIMIT %s
    """, (user_id, limit))
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    campaigns = []
    for row in rows:
        campaigns.append({
            "id": row[0],
            "timestamp": row[1].isoformat() + "Z" if row[1] else None,
            "country": row[2],
            "total_leads": row[3],
            "sent": row[4],
            "failed": row[5],
            "skipped": row[6],
            "opens": row[7],
            "email_target": row[8],
            "city": row[9]
        })
    return campaigns

def log_email_sent(tracking_id: str, email: str, company: str, user_id: str, campaign_id: int = None, website_review: str = "", recipient_name: str = "", email_subject: str = "", email_body: str = ""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO email_tracking (tracking_id, email, company, sent_at, campaign_id, website_review, recipient_name, user_id, email_subject, email_body)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (tracking_id, email, company, datetime.datetime.now(), campaign_id, website_review, recipient_name, user_id, email_subject, email_body))
    conn.commit()
    cursor.close()
    conn.close()

def log_email_opened(tracking_id: str, city: str = None):
    conn = get_db()
    cursor = conn.cursor()
    if city:
        cursor.execute("""
            UPDATE email_tracking 
            SET open_count = open_count + 1, opened_at = %s, city = %s
            WHERE tracking_id = %s
        """, (datetime.datetime.now(), city, tracking_id))
    else:
        cursor.execute("""
            UPDATE email_tracking 
            SET open_count = open_count + 1, opened_at = %s
            WHERE tracking_id = %s
        """, (datetime.datetime.now(), tracking_id))
    conn.commit()
    cursor.close()
    conn.close()

def log_link_click(tracking_id: str, url: str):
    conn = get_db()
    cursor = conn.cursor()
    # Find the user_id from the original email tracking
    cursor.execute("SELECT user_id FROM email_tracking WHERE tracking_id = %s LIMIT 1", (tracking_id,))
    row = cursor.fetchone()
    user_id = row[0] if row else None
    
    cursor.execute("""
        INSERT INTO link_clicks (tracking_id, url, clicked_at, user_id)
        VALUES (%s, %s, %s, %s)
    """, (tracking_id, url, datetime.datetime.now(), user_id))
    conn.commit()
    cursor.close()
    conn.close()

def delete_campaign(campaign_id: int, user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    # Delete associated success logs by matching email within the timeframe of this campaign
    cursor.execute("""
        DELETE FROM success_logs
        WHERE id IN (
            SELECT s.id 
            FROM success_logs s
            JOIN email_tracking e ON s.email = e.email
            WHERE e.campaign_id = %s AND e.user_id = %s
            AND s.timestamp >= e.sent_at - INTERVAL '2 minute'
            AND s.timestamp <= e.sent_at + INTERVAL '2 minute'
        )
    """, (campaign_id, user_id))
    cursor.execute("DELETE FROM email_tracking WHERE campaign_id = %s AND user_id = %s", (campaign_id, user_id))
    cursor.execute("DELETE FROM campaigns WHERE id = %s AND user_id = %s", (campaign_id, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def delete_single_send(tracking_id: str, user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM email_tracking WHERE tracking_id = %s AND user_id = %s AND campaign_id IS NULL", (tracking_id, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_tracking_stats(user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tracking_id, email, company, sent_at, opened_at, open_count
        FROM email_tracking
        WHERE user_id = %s
        ORDER BY sent_at DESC
        LIMIT 100
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    tracking_data = []
    for row in rows:
        tracking_data.append({
            "tracking_id": row[0],
            "email": row[1],
            "company": row[2],
            "sent_at": row[3].isoformat() + "Z" if row[3] else None,
            "opened_at": row[4].isoformat() + "Z" if row[4] else None,
            "open_count": row[5]
        })
    return tracking_data

def get_dashboard_stats(user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    
    stats = {
        "today": 0, "yesterday": 0, "month": 0, 
        "today_opens": 0, "yesterday_opens": 0, "month_opens": 0,
        "total_replies": 0, "reply_rate": 0, 
        "hard_bounce_rate": 0, "soft_bounce_rate": 0
    }
    
    cursor.execute("SELECT COUNT(*) FROM success_logs WHERE user_id = %s AND DATE(timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = DATE(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')", (user_id,))
    stats["today"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM success_logs WHERE user_id = %s AND DATE(timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = DATE(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata') - INTERVAL '1 day'", (user_id,))
    stats["yesterday"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM success_logs WHERE user_id = %s AND date_trunc('month', timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = date_trunc('month', CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')", (user_id,))
    stats["month"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM email_tracking WHERE user_id = %s AND open_count > 0 AND DATE(sent_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = DATE(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')", (user_id,))
    stats["today_opens"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM email_tracking WHERE user_id = %s AND open_count > 0 AND DATE(sent_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = DATE(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata') - INTERVAL '1 day'", (user_id,))
    stats["yesterday_opens"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM email_tracking WHERE user_id = %s AND open_count > 0 AND date_trunc('month', sent_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = date_trunc('month', CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')", (user_id,))
    stats["month_opens"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM replies WHERE user_id = %s", (user_id,))
    stats["total_replies"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM success_logs WHERE user_id = %s", (user_id,))
    total_sent = cursor.fetchone()[0]

    if total_sent > 0:
        stats["reply_rate"] = round((stats["total_replies"] / total_sent) * 100, 2)
        
        cursor.execute("SELECT COUNT(*) FROM bounces WHERE user_id = %s AND bounce_type = 'hard'", (user_id,))
        hard_bounces = cursor.fetchone()[0]
        stats["hard_bounce_rate"] = round((hard_bounces / total_sent) * 100, 2)
        
        cursor.execute("SELECT COUNT(*) FROM bounces WHERE user_id = %s AND bounce_type = 'soft'", (user_id,))
        soft_bounces = cursor.fetchone()[0]
        stats["soft_bounce_rate"] = round((soft_bounces / total_sent) * 100, 2)
    
    cursor.close()
    conn.close()
    return stats

def get_campaign_tracking(campaign_id: int, user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.tracking_id, e.email, e.company, e.sent_at, e.opened_at, e.open_count, e.website_review, e.recipient_name,
               (SELECT COUNT(*) FROM link_clicks lc WHERE lc.tracking_id = e.tracking_id) AS click_count
        FROM email_tracking e
        WHERE e.campaign_id = %s AND e.user_id = %s
        ORDER BY e.sent_at DESC
    """, (campaign_id, user_id))
    rows = cursor.fetchall()
    
    # Fetch all clicks for this campaign
    cursor.execute("""
        SELECT lc.tracking_id, lc.url, lc.clicked_at
        FROM link_clicks lc
        JOIN email_tracking e ON lc.tracking_id = e.tracking_id
        WHERE e.campaign_id = %s AND e.user_id = %s
        ORDER BY lc.clicked_at DESC
    """, (campaign_id, user_id))
    click_rows = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Group clicks by tracking_id
    clicks_by_tracking_id = {}
    for click_row in click_rows:
        tid = click_row[0]
        if tid not in clicks_by_tracking_id:
            clicks_by_tracking_id[tid] = []
        clicks_by_tracking_id[tid].append({
            "url": click_row[1],
            "clicked_at": click_row[2].isoformat() + "Z" if click_row[2] else None
        })
    
    tracking_data = []
    for row in rows:
        tid = row[0]
        tracking_data.append({
            "tracking_id": tid,
            "email": row[1],
            "company": row[2],
            "sent_at": row[3].isoformat() + "Z" if row[3] else None,
            "opened_at": row[4].isoformat() + "Z" if row[4] else None,
            "open_count": row[5],
            "website_review": row[6],
            "recipient_name": row[7],
            "click_count": row[8],
            "clicks": clicks_by_tracking_id.get(tid, [])
        })
    return tracking_data

def get_single_sends_tracking(user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.tracking_id, e.email, e.company, e.sent_at, e.opened_at, e.open_count, e.website_review, e.recipient_name, e.email_subject, e.email_body,
               (SELECT COUNT(*) FROM link_clicks lc WHERE lc.tracking_id = e.tracking_id) AS click_count, e.city
        FROM email_tracking e
        WHERE e.campaign_id IS NULL AND e.user_id = %s
        ORDER BY e.sent_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    
    # Fetch all clicks for single sends
    cursor.execute("""
        SELECT lc.tracking_id, lc.url, lc.clicked_at
        FROM link_clicks lc
        JOIN email_tracking e ON lc.tracking_id = e.tracking_id
        WHERE e.campaign_id IS NULL AND e.user_id = %s
        ORDER BY lc.clicked_at DESC
    """, (user_id,))
    click_rows = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Group clicks by tracking_id
    clicks_by_tracking_id = {}
    for click_row in click_rows:
        tid = click_row[0]
        if tid not in clicks_by_tracking_id:
            clicks_by_tracking_id[tid] = []
        clicks_by_tracking_id[tid].append({
            "url": click_row[1],
            "clicked_at": click_row[2].isoformat() + "Z" if click_row[2] else None
        })
    
    tracking_data = []
    for row in rows:
        tid = row[0]
        tracking_data.append({
            "tracking_id": tid,
            "email": row[1],
            "company": row[2],
            "sent_at": row[3].isoformat() + "Z" if row[3] else None,
            "opened_at": row[4].isoformat() + "Z" if row[4] else None,
            "open_count": row[5],
            "website_review": row[6],
            "recipient_name": row[7],
            "email_subject": row[8],
            "email_body": row[9],
            "click_count": row[10],
            "city": row[11],
            "clicks": clicks_by_tracking_id.get(tid, [])
        })
    return tracking_data

def log_bounce(email: str, bounce_type: str, reason: str, contact_name: str = "", city: str = ""):
    conn = get_db()
    cursor = conn.cursor()
    # Find the user_id from the original email tracking
    cursor.execute("SELECT user_id FROM email_tracking WHERE email = %s ORDER BY sent_at DESC LIMIT 1", (email,))
    row = cursor.fetchone()
    user_id = row[0] if row else None
    
    cursor.execute("""
        INSERT INTO bounces (email, bounce_type, bounce_reason, date_bounced, contact_name, city, user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (email, bounce_type, reason, datetime.datetime.now(), contact_name, city, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def is_hard_bounced(email: str, user_id: str) -> bool:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM bounces WHERE email = %s AND user_id = %s AND bounce_type = 'hard' LIMIT 1", (email, user_id))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None

def log_reply(email: str, date_replied, subject: str):
    conn = get_db()
    cursor = conn.cursor()
    # Find the user_id from the original email tracking
    cursor.execute("SELECT user_id FROM email_tracking WHERE email = %s ORDER BY sent_at DESC LIMIT 1", (email,))
    row = cursor.fetchone()
    user_id = row[0] if row else None
    
    cursor.execute("""
        INSERT INTO replies (email, date_replied, subject, user_id)
        VALUES (%s, %s, %s, %s)
    """, (email, date_replied, subject, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_bounced_contacts(user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT email, bounce_type, bounce_reason, date_bounced, contact_name, city
        FROM bounces
        WHERE user_id = %s
        ORDER BY date_bounced DESC
    """, (user_id,))
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

def get_daily_trend_stats(user_id: str, days: int = 30):
    conn = get_db()
    cursor = conn.cursor()
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
            WHERE user_id = %s AND timestamp >= (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata' - INTERVAL '{days} days')
            GROUP BY day
        ),
        daily_opens AS (
            SELECT DATE(opened_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') AS day, COUNT(*) AS opens
            FROM email_tracking
            WHERE user_id = %s AND open_count > 0 AND opened_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata' - INTERVAL '{days} days')
            GROUP BY day
        ),
        daily_replies AS (
            SELECT DATE(date_replied AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') AS day, COUNT(*) AS replies
            FROM replies
            WHERE user_id = %s AND date_replied >= (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata' - INTERVAL '{days} days')
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
    """, (user_id, user_id, user_id))
    
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

def insert_scheduled_email(user_id: str, email: str, company: str, recipient_name: str, subject: str, body: str, scheduled_at: datetime.datetime, attachments: list = None):
    conn = get_db()
    cursor = conn.cursor()
    try:
        import json
        attachments_json = json.dumps(attachments) if attachments else "[]"
        cursor.execute("""
            INSERT INTO scheduled_emails (user_id, email, company, recipient_name, subject, body, scheduled_at, attachments)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (user_id, email, company, recipient_name, subject, body, scheduled_at, attachments_json))
        new_id = cursor.fetchone()[0]
        conn.commit()
        return new_id
    finally:
        cursor.close()
        conn.close()

def get_due_scheduled_emails():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, user_id, email, company, recipient_name, subject, body, attachments, scheduled_at 
            FROM scheduled_emails 
            WHERE status = 'pending' AND scheduled_at <= CURRENT_TIMESTAMP
        """)
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    finally:
        cursor.close()
        conn.close()

def mark_scheduled_email_sent(email_id: int):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE scheduled_emails SET status = 'sent' WHERE id = %s
        """, (email_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
