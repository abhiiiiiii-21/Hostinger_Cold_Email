"""
html_renderer.py

Responsible for converting plain text email bodies into styled HTML.
Follows the Single Responsibility Principle.
"""

import re


def convert_to_html(text_body: str) -> str:
    """
    Converts plain text to a styled HTML email.

    Args:
        text_body: The plain text email body.

    Returns:
        The fully formatted HTML email string.
    """



    bold_pattern = r'\*\*(.*?)\*\*'
    text_body = re.sub(bold_pattern, r'<strong>\1</strong>', text_body)

    # 4. Preserve paragraphs and convert remaining URLs
    # Split by double newline to form paragraphs
    paragraphs = [p.strip() for p in text_body.split('\n\n') if p.strip()]
    
    html_paragraphs = []
    url_pattern = r'(?<!href=")(https?://[^\s<]+)'
    
    for p in paragraphs:
        # Replace single newlines with <br> inside standard paragraphs
        p = p.replace('\n', '<br>')
        
        # Convert remaining URLs into clickable links (avoiding ones already in href)
        p = re.sub(url_pattern, r'<a href="\1" style="color: #2563EB; text-decoration: none;">\1</a>', p)
        
        html_paragraphs.append(f'<p style="margin: 0 0 16px 0;">{p}</p>')



    body_content = "\n".join(html_paragraphs)

    # 5. Wrap in modern business email structure (simple text format)
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, Helvetica, sans-serif; font-size: 16px; line-height: 1.7; color: #333333; margin: 0; padding: 0;">
    {body_content}
</body>
</html>"""

    return html_template
