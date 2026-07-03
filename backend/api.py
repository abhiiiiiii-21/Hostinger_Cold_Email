import time
import random
import threading
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

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
    """Reads success.csv to calculate Today, Yesterday, and Monthly stats."""
    sent_today = 0
    sent_yesterday = 0
    sent_month = 0
    
    if not logger.SUCCESS_LOG.exists():
        return {"today": 0, "yesterday": 0, "month": 0}
        
    now = datetime.now()
    today_date = now.date()
    yesterday_date = today_date - timedelta(days=1)
    
    import csv
    with open(logger.SUCCESS_LOG, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamp_str = row.get("Timestamp")
            if timestamp_str:
                try:
                    dt = datetime.fromisoformat(timestamp_str)
                    if dt.date() == today_date:
                        sent_today += 1
                    if dt.date() == yesterday_date:
                        sent_yesterday += 1
                    if dt.month == now.month and dt.year == now.year:
                        sent_month += 1
                except:
                    pass
                    
    return {
        "today": sent_today,
        "yesterday": sent_yesterday,
        "month": sent_month
    }

def run_campaign_thread(country: str, force_send: bool = False):
    try:
        global_state.is_running = True
        global_state.is_paused = False
        global_state.stop_requested = False
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
            email = lead.get('email', '').strip()
            
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
                
                send_email(
                    to_email=email,
                    subject=parsed_email.subject,
                    html_body=html_body
                )
                
                logger.log_success(company, email, parsed_email.subject)
                sent_emails.add(email.lower())
                
                add_log("SUCCESS", f"Delivered successfully to {email}")
                global_state.sent_list.append({"company": company, "email": email})
                
                # Sleep delay unless it's the last lead
                if index < len(leads) and not global_state.stop_requested:
                    delay = random.uniform(30, 40)
                    global_state.current_delay = int(delay)
                    add_log("SYSTEM", f"Delaying {delay:.1f}s to mimic human behavior...")
                    
                    # We sleep in chunks so we can interrupt quickly if stop_requested
                    sleep_chunks = int(delay * 10)
                    for _ in range(sleep_chunks):
                        if global_state.stop_requested:
                            break
                        while global_state.is_paused:
                            if global_state.stop_requested:
                                break
                            time.sleep(0.5)
                        if global_state.stop_requested:
                            break
                        time.sleep(0.1)
                        if global_state.estimated_completion_seconds > 0:
                            global_state.estimated_completion_seconds -= 0.1
                        
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
            database.log_campaign(
                country,
                global_state.total_leads,
                len(global_state.sent_list),
                len(global_state.failed_list),
                len(global_state.skipped_list)
            )
        global_state.is_running = False

@app.get("/api/state")
def get_state():
    return {
        "isRunning": global_state.is_running,
        "isPaused": global_state.is_paused,
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
def start_campaign(country: str = "Unknown", force_send: bool = False):
    if global_state.is_running:
        return {"status": "error", "message": "Campaign is already running."}
    
    thread = threading.Thread(target=run_campaign_thread, args=(country, force_send,))
    thread.daemon = True
    thread.start()
    return {"status": "success", "message": "Campaign started"}

@app.get("/api/history")
def get_history():
    return database.get_recent_campaigns()

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
