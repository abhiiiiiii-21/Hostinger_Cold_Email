"""
template_renderer.py

Responsible for replacing placeholders in email templates with actual lead data.
Follows the Single Responsibility Principle — only handles rendering, nothing else.
"""

import re
from typing import Dict


# Maps CSV column names → template placeholder names.
# This keeps the mapping in one place, making it easy to update
# when new columns or placeholders are added.
PLACEHOLDER_MAP: Dict[str, str] = {
    "first name": "first_name",
    "company name": "company_name",
    "city": "city",
    "website": "website",
    "email": "email",
}


def _build_context(lead: Dict[str, str]) -> Dict[str, str]:
    """
    Transform a raw CSV lead dict into a placeholder context dict.

    Converts CSV column names (e.g. 'First Name') to the placeholder
    names used inside templates (e.g. 'first_name').

    Args:
        lead: A single row from the CSV as a dictionary.

    Returns:
        A dictionary mapping placeholder names to their values.
    """
    context: Dict[str, str] = {}

    for csv_column, placeholder_name in PLACEHOLDER_MAP.items():
        value = lead.get(csv_column, "")
        # Handle NaN / None values from pandas
        context[placeholder_name] = str(value) if value == value and value is not None else ""

    return context


def render_template(template: str, lead: Dict[str, str]) -> str:
    """
    Replace all {placeholder} tokens in the template with values from the lead.

    Missing placeholders are silently replaced with an empty string
    instead of raising an exception — this prevents partial sends from
    breaking the entire pipeline.

    Args:
        template: The raw email template string containing {placeholder} tokens.
        lead:     A single lead row from the CSV as a dictionary.

    Returns:
        The fully rendered email body with all placeholders substituted.
    """
    context = _build_context(lead)
    
    # Capitalize first name and company name if present
    if context.get("first_name"):
        context["first_name"] = context["first_name"].strip().title()
    if context.get("company_name"):
        context["company_name"] = context["company_name"].strip().title()

    # Smart fallback for missing company name to prevent grammar errors (e.g. "'s website")
    if not context.get("company_name"):
        # Fix Subject lines
        template = re.sub(r"^Subject:\s*\{company_name\}'s", "Subject: Your", template, flags=re.IGNORECASE | re.MULTILINE)
        template = re.sub(r"^Subject:\s*\{company_name\}:", "Subject: Your website:", template, flags=re.IGNORECASE | re.MULTILINE)
        template = re.sub(r"^Subject:\s*\{company_name\}", "Subject: Your website", template, flags=re.IGNORECASE | re.MULTILINE)
        
        # Fix body grammar
        template = re.sub(r"\{company_name\}'s", "your", template, flags=re.IGNORECASE)
        template = re.sub(r"for \{company_name\}", "for you", template, flags=re.IGNORECASE)
        template = re.sub(r"\{company_name\}", "your agency", template, flags=re.IGNORECASE)

    # Smart fallback for missing city to prevent grammar errors (e.g. "realtors in .")
    if not context.get("city"):
        template = re.sub(r"in \{city\}", "in your area", template, flags=re.IGNORECASE)
        template = re.sub(r"around \{city\}", "around your area", template, flags=re.IGNORECASE)
        template = re.sub(r"\{city\}", "your local area", template, flags=re.IGNORECASE)

    def _replacer(match: re.Match) -> str:
        """Return the placeholder value, or empty string if missing."""
        key = match.group(1)
        return context.get(key, "")

    # Match any {placeholder_name} token in the template
    rendered = re.sub(r"\{(\w+)\}", _replacer, template)

    # Fix greeting if first_name was empty (e.g. "Hi ," -> "Hi,")
    rendered = re.sub(r"Hi\s+,", "Hi,", rendered)
    
    # Clean up any double spaces caused by missing variables
    rendered = re.sub(r"  +", " ", rendered)

    return rendered

