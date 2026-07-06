import sqlite3
import psycopg2
import csv
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "data" / "campaign_history.db"
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("No DATABASE_URL found.")
    exit(1)

print("Connecting to Postgres...")
pg_conn = psycopg2.connect(DATABASE_URL)
pg_cursor = pg_conn.cursor()

print("Creating tables...")
pg_cursor.execute("""
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

pg_cursor.execute("""
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

pg_cursor.execute("""
    CREATE TABLE IF NOT EXISTS success_logs (
        id SERIAL PRIMARY KEY,
        company TEXT,
        email TEXT,
        subject TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT
    )
""")

pg_cursor.execute("""
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

pg_conn.commit()

# Migrate Campaigns
if DB_PATH.exists():
    print("Migrating SQLite databases...")
    sqlite_conn = sqlite3.connect(DB_PATH)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Check if email_target exists
    sqlite_cursor.execute("PRAGMA table_info(campaigns)")
    camp_cols = [col[1] for col in sqlite_cursor.fetchall()]
    camp_query = "SELECT id, timestamp, country, total_leads, sent, failed, skipped"
    if "email_target" in camp_cols:
        camp_query += ", email_target"
    else:
        camp_query += ", 'email'"
    camp_query += " FROM campaigns"
    
    sqlite_cursor.execute(camp_query)
    campaigns = sqlite_cursor.fetchall()
    for row in campaigns:
        pg_cursor.execute("""
            INSERT INTO campaigns (id, timestamp, country, total_leads, sent, failed, skipped, email_target)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, row)
    
    # email_tracking
    sqlite_cursor.execute("PRAGMA table_info(email_tracking)")
    cols = [col[1] for col in sqlite_cursor.fetchall()]
    
    query = f"SELECT id, tracking_id, email, company, sent_at, opened_at, open_count"
    if "campaign_id" in cols: query += ", campaign_id"
    else: query += ", NULL"
    if "website_review" in cols: query += ", website_review"
    else: query += ", NULL"
    if "recipient_name" in cols: query += ", recipient_name"
    else: query += ", NULL"
    query += " FROM email_tracking"
    
    sqlite_cursor.execute(query)
    tracking = sqlite_cursor.fetchall()
    for row in tracking:
        pg_cursor.execute("""
            INSERT INTO email_tracking (id, tracking_id, email, company, sent_at, opened_at, open_count, campaign_id, website_review, recipient_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, row)
    
    sqlite_conn.close()

# Migrate CSVs
success_csv = PROJECT_ROOT / "logs" / "success.csv"
if success_csv.exists():
    print("Migrating success.csv...")
    with open(success_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pg_cursor.execute("""
                INSERT INTO success_logs (company, email, subject, timestamp, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (row.get('Company'), row.get('Email'), row.get('Subject'), row.get('Timestamp'), row.get('Status')))
            
    # Rename CSV to avoid re-migrating or using it later
    os.rename(success_csv, PROJECT_ROOT / "logs" / "success.csv.bak")

failed_csv = PROJECT_ROOT / "logs" / "failed.csv"
if failed_csv.exists():
    print("Migrating failed.csv...")
    with open(failed_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pg_cursor.execute("""
                INSERT INTO failed_logs (company, email, subject, timestamp, status, error)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (row.get('Company'), row.get('Email'), row.get('Subject'), row.get('Timestamp'), row.get('Status'), row.get('Error')))
            
    os.rename(failed_csv, PROJECT_ROOT / "logs" / "failed.csv.bak")

try:
    pg_cursor.execute("SELECT setval('campaigns_id_seq', (SELECT MAX(id) FROM campaigns));")
    pg_cursor.execute("SELECT setval('email_tracking_id_seq', (SELECT MAX(id) FROM email_tracking));")
except Exception as e:
    print(f"Skipping sequence update: {e}")

pg_conn.commit()
pg_conn.close()
print("Migration completed successfully!")
