"""
html_renderer.py

Responsible for converting plain text email bodies into styled HTML.
Follows the Single Responsibility Principle.
"""

import re


def convert_to_html(text_body: str) -> str:
    """
    Converts plain text to a styled HTML email that perfectly mimics a hand-typed Gmail message.
    """
    # 1. Convert bold markdown
    bold_pattern = r'\*\*(.*?)\*\*'
    text_body = re.sub(bold_pattern, r'<strong>\1</strong>', text_body)

    # 2. Convert URLs into clickable links (avoiding ones already in href)
    url_pattern = r'(?<!href=")(https?://[^\s<]+)'
    text_body = re.sub(url_pattern, r'<a href="\1">\1</a>', text_body)

    # 3. Convert all newlines to <br> to mimic native email client spacing perfectly
    text_body = text_body.replace('\n', '<br>')

    # 4. Wrap in native-looking container (14px/15px Arial is Gmail default)
    html_template = f"""<div dir="ltr" style="font-family: Arial, Helvetica, sans-serif; font-size: small; color: #222222;">
{text_body}
</div>"""

    return html_template
