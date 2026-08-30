import os
import re

def add_link_if_missing(html, link_tag, attr_name, attr_value):
    # Check if the link already exists
    pattern = re.compile(r'<link\s+[^>]*'+attr_name+r'\s*=\s*["\']'+re.escape(attr_value)+r'["\'][^>]*>', re.IGNORECASE)
    if pattern.search(html):
        return html
    # Insert before </head>
    if '</head>' in html:
        html = html.replace('</head>', f'  {link_tag}\n</head>', 1)
    else:
        # fallback: insert after <head> if no </head>
        html = re.sub(r'(<head[^>]*>)', r'\1\n  '+link_tag, html, count=1, flags=re.IGNORECASE)
    return html

def add_script_if_missing(html, script_tag):
    # Check if the script already exists
    pattern = re.compile(r'<script\s+[^>]*src\s*=\s*["\']'+re.escape('main.js')+r'["\'][^>]*>', re.IGNORECASE)
    if pattern.search(html):
        return html
    # Insert before </body>
    if '</body>' in html:
        html = html.replace('</body>', f'  {script_tag}\n</body>', 1)
    else:
        html = html + '\n  '+script_tag
    return html

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    # Add stylesheet link
    content = add_link_if_missing(content, '<link rel="stylesheet" href="styles.css">', 'href', 'styles.css')
    # Add script link
    content = add_script_if_missing(content, '<script src="main.js"></script>')
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {filepath}")
    else:
        print(f"No change: {filepath}")

def main():
    base_dir = '.'
    exclude_dirs = {'.git', '__pycache__', 'node_modules', 'venv'}
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                process_file(filepath)

if __name__ == '__main__':
    main()
