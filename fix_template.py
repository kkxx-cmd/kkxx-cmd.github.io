import re

with open('update_news.py', 'r') as f:
    content = f.read()

# Find the HTML_TEMPLATE string
match = re.search(r'HTML_TEMPLATE = \"\"\"([\s\S]*?)\"\"\"', content)
if match:
    template = match.group(1)
    # Split by <style> and </style> tags
    parts = re.split(r'(<style>|</style>)', template)
    if len(parts) >= 5:
        style_content = parts[2]
        # Escape the braces for the CSS: double them so that after string literal and .format we get single braces.
        # We want the output to have: body{ ... }
        # In the format string (after string literal) we need: body{{ ... }}
        # So in the source we need: body{{{{ ... }}}}
        style_content = style_content.replace('{{', '{{{{').replace('}}', '}}}}')
        # Reassemble
        new_template = ''.join([parts[0], parts[1], style_content, parts[3], parts[4]])
        # Replace the old template with the new one
        new_content = content[:match.start(1)] + new_template + content[match.end(1):]
        with open('update_news.py', 'w') as f:
            f.write(new_content)
        print("Template fixed.")
    else:
        print("Could not split template by style tags.")
else:
    print("Could not find HTML_TEMPLATE.")
