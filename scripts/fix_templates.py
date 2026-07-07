import os
import re

def fix_templates(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Split by double newlines to preserve paragraphs
                paragraphs = content.split('\n\n')
                
                # For each paragraph, replace single newlines with a space
                cleaned_paragraphs = []
                for p in paragraphs:
                    # Don't join if it's the subject line
                    if p.startswith('Subject:'):
                        cleaned_paragraphs.append(p.replace('\n', ' '))
                    elif p.startswith('Website:'):
                        cleaned_paragraphs.append(p)
                    else:
                        # Replace single newlines with space, but preserve bullet points or specific links if they existed?
                        # Actually, just replace \n with space and collapse double spaces
                        cleaned = p.replace('\n', ' ').strip()
                        cleaned = re.sub(r'  +', ' ', cleaned)
                        cleaned_paragraphs.append(cleaned)
                
                # Rejoin with double newlines
                new_content = '\n\n'.join(cleaned_paragraphs)
                
                # Fix any cases where Website: is merged into previous line (if any)
                new_content = new_content.replace('Website: http', '\nWebsite: http')
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)

fix_templates('templates/USA')
fix_templates('templates/UK')
fix_templates('templates/UAE')
print("Templates fixed!")
