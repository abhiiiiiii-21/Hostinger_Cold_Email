import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
USER_ID = "user_3GC2vsR4jhRIIA5fbsaNNfzAdYb"

def migrate():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    tables = ["campaigns", "email_tracking", "success_logs", "failed_logs", "bounces", "replies"]
    
    for table in tables:
        print(f"Migrating table: {table}")
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS user_id TEXT;")
            cursor.execute(f"UPDATE {table} SET user_id = %s WHERE user_id IS NULL;", (USER_ID,))
            conn.commit()
            print(f"Success for {table}")
        except Exception as e:
            print(f"Error for {table}: {e}")
            conn.rollback()
            
    cursor.close()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
