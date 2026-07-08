import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

import os
import uuid
import database
import sender
from dotenv import load_dotenv

load_dotenv()

def test_sender_regex():
    print("--- Testing Sender Regex ---")
    html = """
    <html>
      <body>
        <p>Check out our <a href="https://websual.co/course">course</a>!</p>
        <p>Email us at <a href="mailto:hello@websual.co">hello@websual.co</a></p>
        <p>Already tracked <a href="http://localhost:8000/api/click/123?url=https%3A%2F%2Fwebsual.co">link</a></p>
      </body>
    </html>
    """
    
    # Simulate sender logic
    import re
    import urllib.parse
    tracking_id = "test-uuid-123"
    tracking_base_url = "http://localhost:8000"
    
    def replace_link(match):
        prefix = match.group(1)
        original_url = match.group(2)
        suffix = match.group(3)
        
        if original_url.lower().startswith(('mailto:', 'tel:', '#')) or '/api/click/' in original_url:
            return match.group(0)
            
        encoded_url = urllib.parse.quote(original_url, safe='')
        tracking_url = f"{tracking_base_url.rstrip('/')}/api/click/{tracking_id}?url={encoded_url}"
        return f"{prefix}{tracking_url}{suffix}"

    new_html = re.sub(r'(<a\s+[^>]*href=")([^"]+)(")', replace_link, html, flags=re.IGNORECASE)
    print("New HTML:")
    print(new_html)
    assert "api/click/test-uuid-123" in new_html
    assert "https%3A%2F%2Fwebsual.co%2Fcourse" in new_html
    assert "mailto:hello@websual.co" in new_html # Should remain unchanged
    print("Regex works!\n")

def test_database():
    print("--- Testing Database ---")
    database.init_db()
    user_id = "test_user_123"
    tracking_id = str(uuid.uuid4())
    campaign_id = database.create_campaign_log("US", 1, user_id)
    
    database.log_email_sent(tracking_id, "test@test.com", "Test Corp", user_id, campaign_id, "Good", "Test Recipient")
    
    database.log_link_click(tracking_id, "https://websual.co/course")
    database.log_link_click(tracking_id, "https://websual.co/about")
    
    data = database.get_campaign_tracking(campaign_id, user_id)
    
    print("Tracking Data:")
    for d in data:
        print(d)
        assert d["click_count"] == 2
        assert len(d["clicks"]) == 2
        
    # Clean up
    database.delete_campaign(campaign_id, user_id)
    print("Database functions work!\n")

if __name__ == "__main__":
    test_sender_regex()
    test_database()
