"""
sender.py

Responsible for sending emails via Hostinger SMTP and appending them to the Sent folder via IMAP.
Follows the Single Responsibility Principle.
"""

import smtplib
import ssl
import imaplib
import time
import re
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import os
from dotenv import load_dotenv

print(f">>> Loaded sender.py from: {os.path.abspath(__file__)}")

# Load environment variables from .env
load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

IMAP_HOST = os.getenv("IMAP_HOST")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))


def _append_to_sent_folder(msg: MIMEMultipart) -> None:
    """Appends the sent MIME message to the IMAP Sent folder dynamically."""
    print(">>> APPEND FUNCTION ENTERED")
    print(f">>> IMAP_HOST value is: {IMAP_HOST}")
    
    if not IMAP_HOST:
        print(">>> EXITING _append_to_sent_folder EARLY: IMAP_HOST is missing or empty in .env!")
        return
        
    try:
        print("\n--- IMAP Append Debugging ---")
        # Kept SSL bypass for macOS local environment as per previous requirement
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=context) as imap:
            print("✓ Connected to IMAP")
            
            imap.login(SMTP_EMAIL, SMTP_PASSWORD)
            print("✓ Logged in")
            
            # List all mailboxes
            status, mailboxes = imap.list()
            print("✓ Mailboxes discovered:")
            
            sent_folder_name = None
            
            for mb in mailboxes:
                if mb is None:
                    continue
                    
                mb_str = mb.decode('utf-8')
                print(f"  {mb_str}")
                
                # Check for \Sent flag dynamically
                match = re.match(r'\((.*?)\)\s+(".*?"|NIL)\s+(.+)', mb_str)
                if match:
                    flags = match.group(1).lower()
                    folder_name = match.group(3).strip('"')
                    
                    if '\\sent' in flags:
                        sent_folder_name = folder_name
            
            if not sent_folder_name:
                print("❌ STOP: No folder with \\Sent flag found among listed mailboxes.")
                print("-----------------------------\n")
                return
                
            print(f"✓ Selected mailbox: {sent_folder_name}")
            
            # Verify the MIME message
            message_bytes = msg.as_bytes()
            internal_date = imaplib.Time2Internaldate(time.time())
            
            if ' ' in sent_folder_name and not sent_folder_name.startswith('"'):
                target_folder = f'"{sent_folder_name}"'
            else:
                target_folder = sent_folder_name

            # Append the message
            print(f"✓ Attempting to append to: {target_folder}")
            status, response = imap.append(target_folder, '\\Seen', internal_date, message_bytes)
            
            print(f"✓ Append Status: {status}")
            print(f"✓ Append Response: {response}")
            
            if status != 'OK':
                print(f"❌ Append failed! Server responded with: {status} - {response}")
            else:
                print("✓ Message appended. Now verifying...")
                
                # Verify message is in folder
                select_status, select_response = imap.select(target_folder)
                print(f"✓ Select status: {select_status}")
                
                if select_status == 'OK':
                    search_status, message_ids = imap.search(None, "ALL")
                    print(f"✓ Search status: {search_status}")
                    
                    if search_status == 'OK' and message_ids[0]:
                        ids = message_ids[0].split()
                        print(f"✓ Total messages inside {sent_folder_name}: {len(ids)}")
                        
                        latest_id = ids[-1]
                        fetch_status, fetch_data = imap.fetch(latest_id, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM TO)])')
                        
                        if fetch_status == 'OK':
                            print(f"✓ Latest message headers retrieved for verification:")
                            for response_part in fetch_data:
                                if isinstance(response_part, tuple):
                                    print(response_part[1].decode('utf-8', errors='ignore').strip())
                    else:
                        print(f"❌ Search failed or folder is empty.")
                else:
                    print(f"❌ Failed to select {target_folder} for verification.")
                
        print("-----------------------------\n")
                    
    except Exception as e:
        print(f"❌ IMAP Exception encountered: {e}")
        traceback.print_exc()
        print("-----------------------------\n")


def send_email(to_email: str, subject: str, html_body: str) -> None:
    """
    Sends an HTML email using Hostinger SMTP and saves it to the Sent mailbox.

    Args:
        to_email: The recipient's email address.
        subject: The subject line of the email.
        html_body: The formatted HTML body of the email.
    """
    print(">>> send_email() ENTERED")
    if not all([SMTP_HOST, SMTP_EMAIL, SMTP_PASSWORD]):
        raise ValueError("Missing SMTP configuration in .env file.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr(("Websual Agency", SMTP_EMAIL))
    msg["To"] = to_email

    # Attach the HTML body
    part = MIMEText(html_body, "html")
    msg.attach(part)

    # Context for secure connection
    # Disabling strict verification as macOS Python often lacks root certificates by default
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    print(">>> Sending SMTP...")
    # Use SMTP_SSL for port 465, or STARTTLS for 587
    if SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
    
    print(">>> SMTP completed.")
            
    # If SMTP succeeded, save the exact message to the Sent folder
    print(">>> Calling _append_to_sent_folder()")
    _append_to_sent_folder(msg)
