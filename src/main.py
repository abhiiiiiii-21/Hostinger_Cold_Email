"""
main.py

Entry point for the cold email automation pipeline.

Pipeline: Read CSV -> Classify -> Choose Template -> Load -> Render -> Parse Subject/Body -> Convert to HTML -> Check sent -> Send -> Log -> Sleep -> Next
"""

import time
import random
from typing import Dict, Optional, Set
from pathlib import Path

from csv_reader import CSVReader
from classifier import classify, choose_template
from template_loader import load_template
from template_renderer import render_template
from html_renderer import convert_to_html
from template_parser import parse_template
from sender import send_email
import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def process_lead(lead: Dict[str, str], index: int, sent_emails: Set[str]) -> None:
    """
    Process a single lead through the full email pipeline.

    Args:
        lead: A single row from the CSV as a dictionary.
        index: The 1-based index of this lead (for display).
        sent_emails: Set of already sent emails to avoid duplicates.
    """
    company = lead.get('Company Name', 'Unknown')
    email = lead.get('Email', '').strip()
    
    print("=" * 70)
    print(f"Lead #{index}")
    print(f"Agency   : {company}")
    print(f"Email    : {email}")
    
    if not email:
        print("Status   : ⏭️  Skipped (No Email)")
        print("=" * 70 + "\n")
        return
        
    if email.lower() in sent_emails:
        print("Status   : ⏭️  Skipped (Already Sent)")
        print("=" * 70 + "\n")
        return

    review = lead.get("Website Review", "")
    print(f"Review   : {review}")
    
    issues = classify(review)
    template_name: Optional[str] = choose_template(issues)

    if template_name is None:
        print("Status   : ⏭️  Skipped (Good UI)")
        print("=" * 70 + "\n")
        return

    print(f"Template : {template_name}")

    try:
        # Load raw template -> render -> parse -> to HTML
        raw_template = load_template(template_name)
        rendered_text = render_template(raw_template, lead)
        
        parsed_email = parse_template(rendered_text)
        html_body = convert_to_html(parsed_email.body)

        print(f"Subject  : {parsed_email.subject}")
        print("Status   : ⏳ Sending...")

        # Send email (will fail if .env is missing/incorrect, triggering the except block)
        send_email(
            to_email=email,
            subject=parsed_email.subject,
            html_body=html_body
        )

        # Log success and update local state
        logger.log_success(company, email, parsed_email.subject)
        sent_emails.add(email.lower())
        
        print("Status   : ✅ Sent successfully")
        print("=" * 70 + "\n")
        
        # Random delay between 20 and 30 seconds
        delay = random.uniform(30, 40)
        print(f"Sleeping for {delay:.2f} seconds...\n")
        time.sleep(delay)

    except Exception as e:
        error_msg = str(e)
        subject_log = parsed_email.subject if 'parsed_email' in locals() else "Unknown"
        print(f"Status   : ❌ Failed ({error_msg})")
        print("=" * 70 + "\n")
        logger.log_failure(company, email, subject_log, error_msg)


def main() -> None:
    """Run the cold email automation pipeline."""
    csv_path = PROJECT_ROOT / "data" / "leads.csv"
    reader = CSVReader(csv_path)
    leads = reader.get_leads()
    
    # Initialize logs and state
    logger.init_logs()
    sent_emails = logger.get_sent_emails()

    print(f"\n🚀 Starting Email Automation... ({len(leads)} leads found)\n")

    for index, lead in enumerate(leads, start=1):
        process_lead(lead, index, sent_emails)

    print("✅ Pipeline complete.\n")


if __name__ == "__main__":
    main()
