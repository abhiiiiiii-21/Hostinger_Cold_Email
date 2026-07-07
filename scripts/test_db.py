import os, psycopg2
from dotenv import load_dotenv
load_dotenv('../.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
c = conn.cursor()
c.execute("SELECT DATE(timestamp), COUNT(*) FROM success_logs GROUP BY 1 ORDER BY 1")
print("success_logs:", c.fetchall())
c.execute("SELECT DATE(sent_at), COUNT(*) FROM email_tracking GROUP BY 1 ORDER BY 1")
print("email_tracking:", c.fetchall())
