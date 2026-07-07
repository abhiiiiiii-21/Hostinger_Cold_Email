import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

# Update success_logs to push them back to July 6
cursor.execute("""
    UPDATE success_logs
    SET timestamp = timestamp - INTERVAL '6 hours'
    WHERE DATE(timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = '2026-07-07'
""")

# Also update email_tracking if any exist for those same sends
cursor.execute("""
    UPDATE email_tracking
    SET sent_at = sent_at - INTERVAL '6 hours'
    WHERE DATE(sent_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = '2026-07-07'
""")

# Also update campaigns
cursor.execute("""
    UPDATE campaigns
    SET timestamp = timestamp - INTERVAL '6 hours'
    WHERE DATE(timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = '2026-07-07'
""")

conn.commit()
print("Successfully shifted timestamps back by 6 hours!")

# Verify
cursor.execute("SELECT COUNT(*), DATE(timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') as local_date FROM success_logs GROUP BY local_date ORDER BY local_date")
print("New groupings:", cursor.fetchall())

cursor.close()
conn.close()
