import time
import random
import threading
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import uuid

from fastapi import FastAPI, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware

# Import existing modules
from .csv_reader import CSVReader
from .classifier import classify, choose_template
from .template_loader import load_template
from .template_renderer import render_template
from .html_renderer import convert_to_html
from .template_parser import parse_template
from .sender import send_email
from . import logger
from . import database

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

global_state = AppState()

def add_log(log_type: str, message: str):
    time_str = datetime.now().strftime("%H:%M:%S")
    global_state.logs.append({"time": time_str, "type": log_type, "message": message})
    if len(global_state.logs) > 300:
        global_state.logs.pop(0)

def calculate_stats():
    """Reads from database to calculate Today, Yesterday, and Monthly stats."""
    return database.get_dashboard_stats()

def run_campaign_thread(country: str, force_send: bool = False, batch_size: int = 0, cooldown_minutes: int = 0, email_column: str = "email"):
    try:
        global_state.is_running = True
        global_state.is_paused = False
        global_state.stop_requested = False
        global_state.is_cooling_down = False
        global_state.progress = 0
        global_state.processed = 0
        global_state.sent_list = []
        global_state.failed_list = []
        global_state.skipped_list = []
        global_state.logs = []
        
        global_state.current_delay = 0
        global_state.total_time_accumulated = 0
        global_state.leads_processed_this_run = 0
        global_state.average_send_time = 35
        global_state.estimated_completion_seconds = 0
        
        add_log("INFO", "Initializing sequence...")
        
        csv_path = PROJECT_ROOT / "data" / "leads.csv"
        if not csv_path.exists():
            add_log("ERROR", "leads.csv not found!")
            global_state.is_running = False
            return
            
        reader = CSVReader(csv_path)
        leads = reader.get_leads()
        global_state.total_leads = len(leads)
        
        if len(leads) == 0:
            add_log("WARN", "No leads found in CSV.")
            global_state.is_running = False
            return
            
        add_log("INFO", f"[{len(leads)} leads loaded]")
        
        logger.init_logs()
        sent_emails = logger.get_sent_emails()
        
        campaign_id = database.create_campaign_log(country, len(leads), email_target=email_column)
        
        for index, lead in enumerate(leads, start=1):
            if global_state.stop_requested:
                add_log("WARN", "Sequence terminated manually by user.")
                break
                
            while global_state.is_paused:
                if global_state.stop_requested:
                    break
                time.sleep(0.5)

            if global_state.stop_requested:
                add_log("WARN", "Sequence terminated manually by user.")
                break
                
            global_state.processed = index - 1
            global_state.progress = int((global_state.processed / global_state.total_leads) * 100)
            
            remaining = global_state.total_leads - global_state.processed
            global_state.estimated_completion_seconds = remaining * global_state.average_send_time
            
            start_time = time.time()
            
            company = lead.get('company name', 'Unknown')
            email = lead.get(email_column, '').strip()
            first_name = lead.get('first name', '').strip()
            last_name = lead.get('last name', '').strip()
            recipient_name = f"{first_name} {last_name}".strip()
            
            add_log("PROCESS", f"Target: {company} ({email})")
            
            if not email:
                add_log("SKIP", "Reason: No email address provided.")
                global_state.skipped_list.append({"company": company, "email": "N/A", "reason": "No Email"})
                continue
                
            if not force_send and email.lower() in sent_emails:
                add_log("SKIP", "Reason: Lead was already emailed previously.")
                global_state.skipped_list.append({"company": company, "email": email, "reason": "Already Emailed"})
                
                lead_time = time.time() - start_time
                global_state.total_time_accumulated += lead_time
                global_state.leads_processed_this_run += 1
                global_state.average_send_time = int(global_state.total_time_accumulated / global_state.leads_processed_this_run)
                continue
                
            review = lead.get("website review", "")
            issues = classify(review)
            template_name = choose_template(issues)
            
            if template_name is None:
                skip_reason = "Good UI" if "good_ui" in issues else "No matching template (Unclassified)"
                add_log("SKIP", f"Reason: {skip_reason}")
                global_state.skipped_list.append({"company": company, "email": email, "reason": skip_reason})
                
                lead_time = time.time() - start_time
                global_state.total_time_accumulated += lead_time
                global_state.leads_processed_this_run += 1
                global_state.average_send_time = int(global_state.total_time_accumulated / global_state.leads_processed_this_run)
                continue
                
            add_log("INFO", f"Template auto-assigned: {template_name}")
            
            try:
                raw_template = load_template(template_name, country=country)
                rendered_text = render_template(raw_template, lead)
                parsed_email = parse_template(rendered_text)
                html_body = convert_to_html(parsed_email.body)
                
                add_log("SEND", "Transmitting email via Hostinger SMTP...")
                
                tracking_id = str(uuid.uuid4())
                database.log_email_sent(tracking_id, email, company, campaign_id=campaign_id, website_review=review, recipient_name=recipient_name)
                
                send_email(
                    to_email=email,
                    subject=parsed_email.subject,
                    html_body=html_body,
                    tracking_id=tracking_id
                )
                
                logger.log_success(company, email, parsed_email.subject)
                sent_emails.add(email.lower())
                
                add_log("SUCCESS", f"Delivered successfully to {email}")
                global_state.sent_list.append({"company": company, "email": email})
                
                # Sleep delay logic (cooldown vs standard)
                if batch_size > 0 and cooldown_minutes > 0 and len(global_state.sent_list) % batch_size == 0 and len(global_state.sent_list) > 0:
                    delay = cooldown_minutes * 60
                    global_state.is_cooling_down = True
                    add_log("SYSTEM", f"Anti-spam limit reached ({batch_size} emails). Cooling down for {cooldown_minutes} minutes...")
                elif len(global_state.sent_list) % 10 == 0 and len(global_state.sent_list) > 0:
                    delay = 180  # 3 minutes
                    global_state.is_cooling_down = True
                    add_log("SYSTEM", f"Micro-cooldown: Delaying 3 minutes after 10 emails...")
                elif index < len(leads):
                    delay = random.uniform(30, 40)
                    global_state.is_cooling_down = False
                    add_log("SYSTEM", f"Delaying {delay:.1f}s to mimic human behavior...")
                else:
                    delay = 0
                    global_state.is_cooling_down = False

                if delay > 0 and not global_state.stop_requested:
                    end_time = time.time() + delay
                    while time.time() < end_time:
                        if global_state.stop_requested:
                            break
                        while global_state.is_paused:
                            if global_state.stop_requested:
                                break
                            time.sleep(0.5)
                            end_time += 0.5
                        if global_state.stop_requested:
                            break
                        time.sleep(0.1)
                        global_state.current_delay = int(max(0, end_time - time.time()))
                        if global_state.estimated_completion_seconds > 0:
                            global_state.estimated_completion_seconds -= 0.1
                    
                    global_state.is_cooling_down = False
                    global_state.current_delay = 0
                        
            except Exception as e:
                error_msg = str(e)
                add_log("ERROR", f"SMTP Failure: {error_msg}")
                global_state.failed_list.append({"company": company, "email": email, "error": error_msg})
                logger.log_failure(company, email, "Unknown", error_msg)

            lead_time = time.time() - start_time
            global_state.total_time_accumulated += lead_time
            global_state.leads_processed_this_run += 1
            global_state.average_send_time = int(global_state.total_time_accumulated / global_state.leads_processed_this_run)

        global_state.processed = global_state.total_leads if not global_state.stop_requested else global_state.processed
        global_state.progress = int((global_state.processed / global_state.total_leads) * 100) if global_state.total_leads > 0 else 0
        if not global_state.stop_requested:
            add_log("INFO", "Campaign execution completed.")
            
    except Exception as e:
        add_log("ERROR", f"Critical System Error: {str(e)}")
    finally:
        if global_state.total_leads > 0:
            try:
                database.update_campaign_log(
                    campaign_id,
                    len(global_state.sent_list),
                    len(global_state.failed_list),
                    len(global_state.skipped_list)
                )
            except Exception as update_e:
                add_log("ERROR", f"Failed to update campaign log: {str(update_e)}")
        global_state.is_running = False

@app.get("/api/state")
def get_state():
    return {
        "isRunning": global_state.is_running,
        "isPaused": global_state.is_paused,
        "isCoolingDown": global_state.is_cooling_down,
        "progress": global_state.progress,
        "totalLeads": global_state.total_leads,
        "processed": global_state.processed,
        "sentList": global_state.sent_list,
        "failedList": global_state.failed_list,
        "skippedList": global_state.skipped_list,
        "logs": global_state.logs,
        "currentDelay": global_state.current_delay,
        "averageSendTime": global_state.average_send_time,
        "estimatedCompletion": global_state.estimated_completion_seconds
    }

@app.get("/api/stats")
def get_stats():
    return calculate_stats()

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    file_path = data_dir / "leads.csv"
    
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
            # Combine issue names (e.g. "Bad UI + SEO")
            names = [issue_names.get(i, i) for i in issues]
            # Sort so "Bad UI + SEO" is consistent
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
def start_campaign(country: str = "Unknown", force_send: bool = False, batch_size: int = 0, cooldown_minutes: int = 0, email_column: str = "email"):
    if global_state.is_running:
        return {"status": "error", "message": "Campaign is already running."}
    
    thread = threading.Thread(target=run_campaign_thread, args=(country, force_send, batch_size, cooldown_minutes, email_column))
    thread.daemon = True
    thread.start()
    return {"status": "success", "message": "Campaign started"}

@app.get("/api/history")
def get_history():
    return database.get_recent_campaigns()

@app.get("/api/history/{campaign_id}/tracking")
def get_campaign_tracking_endpoint(campaign_id: int):
    return database.get_campaign_tracking(campaign_id)

@app.post("/api/stop")
def stop_campaign():
    if not global_state.is_running:
        return {"status": "error", "message": "No campaign running."}
    
    global_state.stop_requested = True
    return {"status": "success", "message": "Stop requested"}

@app.post("/api/pause")
def pause_campaign():
    if not global_state.is_running:
        return {"status": "error", "message": "No campaign running."}
    if global_state.is_paused:
        return {"status": "error", "message": "Already paused."}
    
    global_state.is_paused = True
    add_log("WARN", "Campaign paused by user.")
    return {"status": "success", "message": "Paused"}

@app.post("/api/resume")
def resume_campaign():
    if not global_state.is_running:
        return {"status": "error", "message": "No campaign running."}
    if not global_state.is_paused:
        return {"status": "error", "message": "Not paused."}
    
    global_state.is_paused = False
    add_log("INFO", "Campaign resumed.")
    return {"status": "success", "message": "Resumed"}

@app.get("/api/track/{tracking_id}.png")
def track_email_open(tracking_id: str):
    """
    Transparent 1x1 pixel endpoint to track email opens.
    """
    # Log the open in the database
    database.log_email_opened(tracking_id)
    
    # 1x1 transparent GIF base64 encoded
    transparent_pixel = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff"
        b"\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00"
        b"\x01\x00\x00\x02\x01\x44\x00\x3b"
    )
    return Response(content=transparent_pixel, media_type="image/gif")

@app.get("/api/tracking")
def get_tracking():
    """
    Returns email tracking stats.
    """
    return database.get_tracking_stats()
