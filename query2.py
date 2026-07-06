import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*), DATE(timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') as local_date FROM success_logs GROUP BY local_date ORDER BY local_date")
print(cursor.fetchall())
