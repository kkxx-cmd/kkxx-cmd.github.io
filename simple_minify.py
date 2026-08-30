import os
import re

def minify_css(content):
    # Remove comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove extra whitespace: replace multiple spaces/newlines with single space
    content = re.sub(r'\s+', ' ', content)
    # Remove spaces around { } : ; ,
    content = re.sub(r'\s*([{}:;,])\s*', r'\1', content)
    # Remove leading/trailing space
    return content.strip()

def minify_js(content):
    # Remove single line comments
    content = re.sub(r'//.*', '', content)
    # Remove multi-line comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove extra whitespace
    content = re.sub(r'\s+', ' ', content)
    # Remove spaces around operators? Keep simple.
    content = re.sub(r'\s*([{}:;,=])\s*', r'\1', content)
    return content.strip()

def minify_html(content):
    # Very basic: remove comments, collapse whitespace, but avoid breaking script/style
    # We'll skip for safety; just return original for now.
    return content

def process_file(filepath):
    if filepath.endswith('.css'):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        minified = minify_css(content)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(minified)
        print(f"Minified CSS: {filepath}")
    elif filepath.endswith('.js'):
        # Skip search-index.json
        if os.path.basename(filepath) == 'search-index.json':
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        minified = minify_js(content)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(minified)
        print(f"Minified JS: {filepath}")
    elif filepath.endswith('.html'):
        # We'll skip HTML minification for safety
        pass

def main():
    base_dir = '.'
    excluded_dirs = {'.git', '__pycache__', 'node_modules'}
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for file in files:
            if file.endswith('.css') or file.endswith('.js') or file.endswith('.html'):
                filepath = os.path.join(root, file)
                process_file(filepath)

if __name__ == '__main__':
    main()
