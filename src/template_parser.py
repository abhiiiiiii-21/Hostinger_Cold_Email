"""
template_parser.py

Responsible for parsing the subject line and email body from a rendered text template.
Follows the Single Responsibility Principle.
"""

import re
from typing import Tuple
from dataclasses import dataclass


@dataclass
class ParsedEmail:
    subject: str
    body: str


def parse_template(rendered_text: str) -> ParsedEmail:
    """
    Extracts the subject and body from the rendered text.
    Assumes the template format:
    Subject: <subject_line>
    <empty_line>
    <body>

    Args:
        rendered_text: The full text of the rendered template.

    Returns:
        A ParsedEmail dataclass containing subject and body.
    """
    lines = rendered_text.splitlines()

    subject = ""
    body_lines = []

    is_body = False

    for line in lines:
        if not is_body:
            match = re.match(r'(?i)^Subject\s*:\s*(.*)', line)
            if match:
                subject = match.group(1).strip()
                continue
            if line.strip() == "":
                # The first empty line after the subject marks the start of the body
                if subject:
                    is_body = True
                continue

        if is_body:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()

    # Fallback if there was no "Subject:" line
    if not subject:
        subject = "Website Review"
        body = rendered_text.strip()

    return ParsedEmail(subject=subject, body=body)
