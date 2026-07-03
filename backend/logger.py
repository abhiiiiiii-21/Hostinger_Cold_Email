"""
logger.py

Responsible for managing logs for successful and failed emails.
Also provides resume functionality by checking success logs.
Follows the Single Responsibility Principle.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Set

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
SUCCESS_LOG = LOGS_DIR / "success.csv"
FAILED_LOG = LOGS_DIR / "failed.csv"


def init_logs() -> None:
    """Ensure the logs directory and CSV files exist with headers."""
    LOGS_DIR.mkdir(exist_ok=True)
    
    if not SUCCESS_LOG.exists():
        with open(SUCCESS_LOG, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Company", "Email", "Subject", "Timestamp", "Status"])
            
    if not FAILED_LOG.exists():
        with open(FAILED_LOG, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Company", "Email", "Subject", "Timestamp", "Status", "Error"])


def get_sent_emails() -> Set[str]:
    """
    Reads the success log and returns a set of already sent emails.
    Useful for resuming the script without sending duplicates.
    """
    if not SUCCESS_LOG.exists():
        return set()

    sent = set()
    with open(SUCCESS_LOG, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if email := row.get("Email"):
                sent.add(email.strip().lower())
    return sent


def log_success(company: str, email: str, subject: str) -> None:
    """Logs a successfully sent email."""
    init_logs()
    timestamp = datetime.now().isoformat()
    with open(SUCCESS_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([company, email, subject, timestamp, "SUCCESS"])


def log_failure(company: str, email: str, subject: str, error: str) -> None:
    """Logs a failed email attempt."""
    init_logs()
    timestamp = datetime.now().isoformat()
    with open(FAILED_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([company, email, subject, timestamp, "FAILED", error])
