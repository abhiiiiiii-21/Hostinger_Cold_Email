import time
import random
import threading
import shutil
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import uuid
import smtplib
import sys

from fastapi import FastAPI, UploadFile, File, Response, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT / "backend"))

# Import existing modules
from csv_reader import CSVReader
from classifier import classify, choose_template
from template_loader import load_template
from template_renderer import render_template
from html_renderer import convert_to_html
from template_parser import parse_template
from sender import send_email
import logger
import database
import replies

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Initialize database
database.init_db()

app = FastAPI(title="WebsualMailer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AppState:
    def __init__(self):
        self.is_running = False
        self.is_paused = False
        self.stop_requested = False
        self.is_cooling_down = False
        self.progress = 0
        self.total_leads = 0
        self.processed = 0
        self.sent_list = []
        self.failed_list = []
        self.skipped_list = []
        self.logs = []
        
        # Speed tracking
        self.current_delay = 0
        self.total_time_accumulated = 0
        self.leads_processed_this_run = 0
        self.average_send_time = 35
        self.estimated_completion_seconds = 0

# Multi-tenant state
global_states: Dict[str, AppState] = {}

def get_state_for_user(user_id: str) -> AppState:
    if user_id not in global_states:
        global_states[user_id] = AppState()
    return global_states[user_id]

def add_log(state: AppState, log_type: str, message: str):
    time_str = datetime.now().strftime("%H:%M:%S")
    state.logs.append({"time": time_str, "type": log_type, "message": message})
    if len(state.logs) > 300:
        state.logs.pop(0)

# ── Authentication Dependency ──
def get_user_id(x_api_key: str = Header(None), x_user_id: str = Header(None)):
    expected_secret = os.getenv("BACKEND_API_SECRET", "websual_dev_secret_key")
    if x_api_key != expected_secret:
        raise HTTPException(status_code=401, detail="Unauthorized API Key")
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID is required")
    return x_user_id
# ──────────────────────────────

def calculate_stats(user_id: str):
    """Reads from database to calculate Today, Yesterday, and Monthly stats."""
    return database.get_dashboard_stats(user_id)

def run_campaign_thread(user_id: str, country: str, force_send: bool = False, batch_size: int = 0, cooldown_minutes: int = 0, email_column: str = "email"):
    state = get_state_for_user(user_id)
    try:
        state.is_running = True
        state.is_paused = False
        state.stop_requested = False
        state.is_cooling_down = False
        state.progress = 0
        state.processed = 0
        state.sent_list = []
        state.failed_list = []
        state.skipped_list = []
        state.logs = []
        
        state.current_delay = 0
        state.total_time_accumulated = 0
        state.leads_processed_this_run = 0
        state.average_send_time = 35
        state.estimated_completion_seconds = 0
        
        add_log(state, "INFO", "Initializing sequence...")
        
        # In a real multi-tenant app, the CSV would be stored per-user. 
        # For now, we suffix the user ID to prevent conflicts.
        csv_path = PROJECT_ROOT / "data" / f"leads_{user_id}.csv"
        if not csv_path.exists():
            add_log(state, "ERROR", "leads.csv not found!")
            state.is_running = False
            return
            
        reader = CSVReader(csv_path)
        leads = reader.get_leads()
        state.total_leads = len(leads)
        
        if len(leads) == 0:
            add_log(state, "WARN", "No leads found in CSV.")
            state.is_running = False
            return
            
        add_log(state, "INFO", f"[{len(leads)} leads loaded]")
        
        logger.init_logs()
        sent_emails = logger.get_sent_emails()
        
        campaign_id = database.create_campaign_log(country, len(leads), user_id, email_target=email_column)
        
        for index, lead in enumerate(leads, start=1):
            if state.stop_requested:
                add_log(state, "WARN", "Sequence terminated manually by user.")
                break
                
            while state.is_paused:
                if state.stop_requested:
                    break
                time.sleep(0.5)

            if state.stop_requested:
                add_log(state, "WARN", "Sequence terminated manually by user.")
                break
                
            state.processed = index - 1
            state.progress = int((state.processed / state.total_leads) * 100)
            
            remaining = state.total_leads - state.processed
            state.estimated_completion_seconds = remaining * state.average_send_time
            
            start_time = time.time()
            
            company = lead.get('company name', 'Unknown')
            email = lead.get(email_column, '').strip()
            first_name = lead.get('first name', '').strip()
            last_name = lead.get('last name', '').strip()
            recipient_name = f"{first_name} {last_name}".strip()
            
            add_log(state, "PROCESS", f"Target: {company} ({email})")
            
            if not email:
                add_log(state, "SKIP", "Reason: No email address provided.")
                state.skipped_list.append({"company": company, "email": "N/A", "reason": "No Email"})
                continue
                
            if database.is_hard_bounced(email, user_id):
                add_log(state, "SKIP", "Reason: Email is on hard bounce suppression list.")
                state.skipped_list.append({"company": company, "email": email, "reason": "Hard Bounced"})
                continue
                
            if not force_send and email.lower() in sent_emails:
                add_log(state, "SKIP", "Reason: Lead was already emailed previously.")
                state.skipped_list.append({"company": company, "email": email, "reason": "Already Emailed"})
                
                lead_time = time.time() - start_time
                state.total_time_accumulated += lead_time
                state.leads_processed_this_run += 1
                state.average_send_time = int(state.total_time_accumulated / state.leads_processed_this_run)
                continue
                
            review = lead.get("website review", "")
            issues = classify(review)
            template_name = choose_template(issues)
            
            if template_name is None:
                skip_reason = "Good UI" if "good_ui" in issues else "No matching template (Unclassified)"
                add_log(state, "SKIP", f"Reason: {skip_reason}")
                state.skipped_list.append({"company": company, "email": email, "reason": skip_reason})
                
                lead_time = time.time() - start_time
                state.total_time_accumulated += lead_time
                state.leads_processed_this_run += 1
                state.average_send_time = int(state.total_time_accumulated / state.leads_processed_this_run)
                continue
                
            add_log(state, "INFO", f"Template auto-assigned: {template_name}")
            
            try:
                raw_template = load_template(template_name, country=country)
                rendered_text = render_template(raw_template, lead)
                parsed_email = parse_template(rendered_text)
                html_body = convert_to_html(parsed_email.body)
                
                add_log(state, "SEND", "Transmitting email via Hostinger SMTP...")
                
                tracking_id = str(uuid.uuid4())
                database.log_email_sent(tracking_id, email, company, user_id, campaign_id=campaign_id, website_review=review, recipient_name=recipient_name)
                
                send_email(
                    to_email=email,
                    subject=parsed_email.subject,
                    html_body=html_body,
                    tracking_id=tracking_id
                )
                
                logger.log_success(company, email, parsed_email.subject)
                sent_emails.add(email.lower())
                
                add_log(state, "SUCCESS", f"Delivered successfully to {email}")
                state.sent_list.append({"company": company, "email": email})
                
                # Sleep delay logic (cooldown vs standard)
                if batch_size > 0 and cooldown_minutes > 0 and len(state.sent_list) % batch_size == 0 and len(state.sent_list) > 0:
                    delay = cooldown_minutes * 60
                    state.is_cooling_down = True
                    add_log(state, "SYSTEM", f"Anti-spam limit reached ({batch_size} emails). Cooling down for {cooldown_minutes} minutes...")
                elif len(state.sent_list) % 10 == 0 and len(state.sent_list) > 0:
                    delay = 180  # 3 minutes
                    state.is_cooling_down = True
                    add_log(state, "SYSTEM", f"Micro-cooldown: Delaying 3 minutes after 10 emails...")
                elif index < len(leads):
                    delay = random.uniform(30, 40)
                    state.is_cooling_down = False
                    add_log(state, "SYSTEM", f"Delaying {delay:.1f}s to mimic human behavior...")
                else:
                    delay = 0
                    state.is_cooling_down = False

                if delay > 0 and not state.stop_requested:
                    end_time = time.time() + delay
                    while time.time() < end_time:
                        if state.stop_requested:
                            break
                        while state.is_paused:
                            if state.stop_requested:
                                break
                            time.sleep(0.5)
                            end_time += 0.5
                        if state.stop_requested:
                            break
                        time.sleep(0.1)
                        state.current_delay = int(max(0, end_time - time.time()))
                        if state.estimated_completion_seconds > 0:
                            state.estimated_completion_seconds -= 0.1
                    
                    state.is_cooling_down = False
                    state.current_delay = 0
                        
            except smtplib.SMTPResponseException as e:
                code = e.smtp_code
                msg = e.smtp_error.decode(errors='ignore') if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
                bounce_type = "hard" if 500 <= code < 600 else "soft"
                database.log_bounce(email, bounce_type, f"{code} {msg}", recipient_name, company)
                error_msg = f"SMTP Response: {code} {msg}"
                add_log(state, "ERROR", f"{bounce_type.upper()} BOUNCE: {error_msg}")
                state.failed_list.append({"company": company, "email": email, "error": error_msg})
                logger.log_failure(company, email, "Unknown", error_msg)
            except smtplib.SMTPRecipientsRefused as e:
                for ref_email, (code, msg) in e.recipients.items():
                    msg_str = msg.decode(errors='ignore') if isinstance(msg, bytes) else str(msg)
                    database.log_bounce(ref_email, "hard", f"{code} {msg_str}", recipient_name, company)
                error_msg = f"Recipients Refused: {str(e.recipients)}"
                add_log(state, "ERROR", f"HARD BOUNCE: {error_msg}")
                state.failed_list.append({"company": company, "email": email, "error": error_msg})
                logger.log_failure(company, email, "Unknown", error_msg)
            except Exception as e:
                error_msg = str(e)
                add_log(state, "ERROR", f"SMTP Failure: {error_msg}")
                state.failed_list.append({"company": company, "email": email, "error": error_msg})
                logger.log_failure(company, email, "Unknown", error_msg)

            lead_time = time.time() - start_time
            state.total_time_accumulated += lead_time
            state.leads_processed_this_run += 1
            state.average_send_time = int(state.total_time_accumulated / state.leads_processed_this_run)

        state.processed = state.total_leads if not state.stop_requested else state.processed
        state.progress = int((state.processed / state.total_leads) * 100) if state.total_leads > 0 else 0
        if not state.stop_requested:
            add_log(state, "INFO", "Campaign execution completed.")
            
    except Exception as e:
        add_log(state, "ERROR", f"Critical System Error: {str(e)}")
    finally:
        if state.total_leads > 0:
            try:
                database.update_campaign_log(
                    campaign_id,
                    len(state.sent_list),
                    len(state.failed_list),
                    len(state.skipped_list),
                    user_id
                )
            except Exception as update_e:
                add_log(state, "ERROR", f"Failed to update campaign log: {str(update_e)}")
        state.is_running = False

@app.get("/api/state")
def get_state(user_id: str = Depends(get_user_id)):
    state = get_state_for_user(user_id)
    return {
        "isRunning": state.is_running,
        "isPaused": state.is_paused,
        "isCoolingDown": state.is_cooling_down,
        "progress": state.progress,
        "totalLeads": state.total_leads,
        "processed": state.processed,
        "sentList": state.sent_list,
        "failedList": state.failed_list,
        "skippedList": state.skipped_list,
        "logs": state.logs,
        "currentDelay": state.current_delay,
        "averageSendTime": state.average_send_time,
        "estimatedCompletion": state.estimated_completion_seconds
    }

@app.get("/api/stats")
def get_stats(user_id: str = Depends(get_user_id)):
    return calculate_stats(user_id)

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), user_id: str = Depends(get_user_id)):
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    file_path = data_dir / f"leads_{user_id}.csv"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        reader = CSVReader(file_path)
        leads = reader.get_leads()
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Invalid or empty CSV file: {str(e)}"})
    
    from collections import Counter
    breakdown = Counter()
    
    issue_names = {
        "seo": "SEO",
        "bad_ui": "Bad UI",
        "avg_ui": "Average UI",
        "not_opening": "Not Working",
        "good_ui": "Good UI"
    }
    
    for lead in leads:
        review = lead.get("website review", "")
        issues = classify(review)
        
        if not issues:
            breakdown["Unclassified"] += 1
        elif "good_ui" in issues:
            breakdown["Good UI"] += 1
        else:
            names = [issue_names.get(i, i) for i in issues]
            names.sort()
            cat = " + ".join(names)
            breakdown[cat] += 1
            
    return {
        "status": "success", 
        "message": f"Saved as {file.filename}",
        "total": len(leads),
        "breakdown": dict(breakdown)
    }

@app.post("/api/start")
def start_campaign(country: str = "Unknown", force_send: bool = False, batch_size: int = 0, cooldown_minutes: int = 0, email_column: str = "email", user_id: str = Depends(get_user_id)):
    state = get_state_for_user(user_id)
    if state.is_running:
        return {"status": "error", "message": "Campaign is already running."}
    
    thread = threading.Thread(target=run_campaign_thread, args=(user_id, country, force_send, batch_size, cooldown_minutes, email_column))
    thread.daemon = True
    thread.start()
    return {"status": "success", "message": "Campaign started"}

@app.get("/api/history")
def get_history(user_id: str = Depends(get_user_id)):
    return database.get_recent_campaigns(user_id)

@app.get("/api/history/{campaign_id}/tracking")
def get_campaign_tracking_endpoint(campaign_id: int, user_id: str = Depends(get_user_id)):
    return database.get_campaign_tracking(campaign_id, user_id)

@app.delete("/api/history/{campaign_id}")
def delete_campaign_endpoint(campaign_id: int, user_id: str = Depends(get_user_id)):
    try:
        database.delete_campaign(campaign_id, user_id)
        return {"status": "success", "message": f"Campaign {campaign_id} deleted."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/stop")
def stop_campaign(user_id: str = Depends(get_user_id)):
    state = get_state_for_user(user_id)
    if not state.is_running:
        return {"status": "error", "message": "No campaign running."}
    
    state.stop_requested = True
    return {"status": "success", "message": "Stop requested"}

@app.post("/api/pause")
def pause_campaign(user_id: str = Depends(get_user_id)):
    state = get_state_for_user(user_id)
    if not state.is_running:
        return {"status": "error", "message": "No campaign running."}
    if state.is_paused:
        return {"status": "error", "message": "Already paused."}
    
    state.is_paused = True
    add_log(state, "WARN", "Campaign paused by user.")
    return {"status": "success", "message": "Paused"}

@app.post("/api/resume")
def resume_campaign(user_id: str = Depends(get_user_id)):
    state = get_state_for_user(user_id)
    if not state.is_running:
        return {"status": "error", "message": "No campaign running."}
    if not state.is_paused:
        return {"status": "error", "message": "Not paused."}
    
    state.is_paused = False
    add_log(state, "INFO", "Campaign resumed.")
    return {"status": "success", "message": "Resumed"}

@app.get("/api/track/{tracking_id}.png")
def track_email_open(tracking_id: str):
    """
    Transparent 1x1 pixel endpoint to track email opens.
    This does NOT use user_id because it is triggered by an email client.
    """
    database.log_email_opened(tracking_id)
    
    transparent_pixel = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff"
        b"\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00"
        b"\x01\x00\x00\x02\x01\x44\x00\x3b"
    )
    return Response(content=transparent_pixel, media_type="image/gif")

@app.get("/api/tracking")
def get_tracking(user_id: str = Depends(get_user_id)):
    return database.get_tracking_stats(user_id)

@app.post("/api/sync-replies")
def sync_replies(user_id: str = Depends(get_user_id)):
    # Replies currently sync from a global IMAP account, but log_reply assigns the correct user_id
    # based on the email_tracking table. So one user pressing sync helps all users!
    return replies.check_inbox_for_replies()

@app.get("/api/bounces")
def get_bounces(user_id: str = Depends(get_user_id)):
    return database.get_bounced_contacts(user_id)

@app.get("/api/trend")
def get_trend(days: int = 30, user_id: str = Depends(get_user_id)):
    return database.get_daily_trend_stats(user_id, days)
