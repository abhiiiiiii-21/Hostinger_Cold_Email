import imaplib
import email
from email.header import decode_header
import ssl
import os
from dotenv import load_dotenv
import database
import datetime
import traceback

load_dotenv()

IMAP_HOST = os.getenv("IMAP_HOST")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def check_inbox_for_replies():
    """
    Connects to the IMAP inbox, fetches unread or recent emails, 
    and checks if they match a known sent email.
    """
    if not all([IMAP_HOST, SMTP_EMAIL, SMTP_PASSWORD]):
        print("Missing IMAP configuration for replies.")
        return {"status": "error", "message": "Missing IMAP config"}
        
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=context)
        mail.login(SMTP_EMAIL, SMTP_PASSWORD)
        
        # Select the inbox
        mail.select("inbox")
        
        # Search for all emails (or could filter by UNSEEN to be faster, but let's check ALL to be safe and avoid missing past ones)
        # To avoid scanning thousands of emails every time, we should probably check emails since a certain date, but for now we'll check ALL.
        # Actually, let's just check the last 100 emails to keep it lightweight.
        status, messages = mail.search(None, "ALL")
        if status != "OK" or not messages[0]:
            mail.logout()
            return {"status": "success", "new_replies": 0}
            
        email_ids = messages[0].split()
        latest_ids = email_ids[-100:]  # get last 100
        
        new_replies_count = 0
        
        # We need a quick way to know who we sent emails to.
        # We can fetch all distinct emails from success_logs or email_tracking.
        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT email FROM email_tracking")
        sent_emails = {row[0].lower() for row in cursor.fetchall()}
        
        # Also get already logged replies so we don't log them twice
        cursor.execute("SELECT email, subject FROM replies")
        logged_replies = {(row[0].lower(), row[1]) for row in cursor.fetchall()}
        
        for e_id in latest_ids:
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            if res != "OK":
                continue
                
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Extract From
                    from_header = msg.get("From", "")
                    # Extract email address between < > if present
                    import re
                    match = re.search(r'<(.+?)>', from_header)
                    from_email = match.group(1) if match else from_header
                    from_email = from_email.strip().lower()
                    
                    if from_email in sent_emails:
                        # It's a reply!
                        subject, encoding = decode_header(msg.get("Subject", ""))[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")
                            
                        date_str = msg.get("Date")
                        # Parse date or fallback to now
                        try:
                            from email.utils import parsedate_to_datetime
                            date_replied = parsedate_to_datetime(date_str)
                        except:
                            date_replied = datetime.datetime.now()
                            
                        if (from_email, subject) not in logged_replies:
                            # Check if it's an auto-reply (Out of Office)
                            subject_lower = subject.lower()
                            is_auto_reply = any(keyword in subject_lower for keyword in [
                                "out of office", "automatic reply", "auto-reply", "ooo", "vacation", "autoreply"
                            ])
                            
                            auto_submitted = str(msg.get("Auto-Submitted", "")).lower()
                            if auto_submitted and auto_submitted != "no":
                                is_auto_reply = True

                            if is_auto_reply:
                                # Log as a soft bounce instead of a reply
                                database.log_bounce(from_email, "soft", "Out of Office / Auto-Reply", "", "")
                            else:
                                database.log_reply(from_email, date_replied, subject)
                                new_replies_count += 1
                                
                            logged_replies.add((from_email, subject))
                            
        cursor.close()
        conn.close()
        mail.logout()
        return {"status": "success", "new_replies": new_replies_count}
        
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
