import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

cursor.execute("SELECT CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata', DATE(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')")
print("Correct current time:", cursor.fetchone())
