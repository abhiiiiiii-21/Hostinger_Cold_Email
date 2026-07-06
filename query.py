import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

cursor.execute("SELECT timestamp, DATE(timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') as local_date FROM success_logs LIMIT 5")
print("success_logs:", cursor.fetchall())

cursor.execute("SELECT CURRENT_TIMESTAMP, CURRENT_TIMESTAMP AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata', DATE(CURRENT_TIMESTAMP AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')")
print("current_time:", cursor.fetchone())
