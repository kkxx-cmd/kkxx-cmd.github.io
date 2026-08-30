import os
import re

def add_stylesheet_and_script_yaml(content):
    # Split by '---' with maxsplit=2
    parts = content.split('---', 2)
    if len(parts) != 3:
        return content  # Not a YAML front matter file, return as is
    before, front_matter, rest = parts
    # We'll ignore 'before' (should be empty)
    # Check and add stylesheet link
    stylesheet_tag = '<link rel="stylesheet" href="styles.css">'
    # Case-insensitive check for stylesheet link
    if not re.search(r'<link\s+[^>]*href\s*=\s*["\']styles\.css["\'][^>]*>', rest, re.IGNORECASE):
        rest = stylesheet_tag + '\n' + rest
    # Check and add main.js script tag
    script_tag = '<script src="main.js"></script>'
    if not re.search(r'<script\s+[^>]*src\s*=\s*["\']main\.js["\'][^>]*>', rest, re.IGNORECASE):
        rest = rest + '\n' + script_tag
    # Reassemble
    return '---' + front_matter + '---' + rest

def add_stylesheet_and_script_regular(content):
    # For regular HTML files
    # Add stylesheet link if missing
    if not re.search(r'<link\s+[^>]*href\s*=\s*["\']styles\.css["\'][^>]*>', content, re.IGNORECASE):
        # Insert before </head>
        if '</head>' in content:
            content = content.replace('</head>', '  <link rel="stylesheet" href="styles.css">\n</head>', 1)
        else:
            # fallback: insert after <head>
            content = re.sub(r'(<head[^>]*>)', r'\1\n  <link rel="stylesheet" href="styles.css">', content, count=1, flags=re.IGNORECASE)
    # Add main.js script if missing
    if not re.search(r'<script\s+[^>]*src\s*=\s*["\']main\.js["\'][^>]*>', content, re.IGNORECASE):
        if '</body>' in content:
            content = content.replace('</body>', '  <script src="main.js"></script>\n</body>', 1)
        else:
            content = content + '\n<script src="main.js"></script>'
    return content

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    # Determine if it's a YAML front matter file
    if content.strip().startswith('---'):
        content = add_stylesheet_and_script_yaml(content)
    else:
        content = add_stylesheet_and_script_regular(content)
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
