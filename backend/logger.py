import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_logs() -> None:
    pass # Managed by database.py init_db()

def get_sent_emails() -> set:
    """
    Reads the success_logs table and returns a set of already sent emails.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM success_logs")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    sent = set()
    for row in rows:
        if row[0]:
            sent.add(row[0].strip().lower())
    return sent

def log_success(company: str, email: str, subject: str) -> None:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO success_logs (company, email, subject, timestamp, status)
        VALUES (%s, %s, %s, %s, 'SUCCESS')
    """, (company, email, subject, datetime.now()))
    conn.commit()
    cursor.close()
    conn.close()

def log_failure(company: str, email: str, subject: str, error: str) -> None:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO failed_logs (company, email, subject, timestamp, status, error)
        VALUES (%s, %s, %s, %s, 'FAILED', %s)
    """, (company, email, subject, datetime.now(), str(error)))
    conn.commit()
    cursor.close()
    conn.close()
