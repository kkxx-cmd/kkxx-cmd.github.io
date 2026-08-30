import os
import re

def add_lazy_loading_to_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Pattern to find img tags without loading attribute
    # We'll add loading="lazy" to every img tag that doesn't already have a loading attribute
    def repl(match):
        tag = match.group(0)
        if 'loading=' not in tag:
            # Insert loading="lazy" before the closing >
            if tag.endswith('/>'):
                return tag[:-2] + ' loading="lazy"/>'
            else:
                return tag[:-1] + ' loading="lazy">'
        return tag
    # This regex matches an img tag (simplified)
    new_content = re.sub(r'<img[^>]*>', repl, content)
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    base_dir = '.'
    excluded_dirs = {'.git', '__pycache__', 'node_modules'}
    count = 0
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                if add_lazy_loading_to_file(filepath):
                    print(f"Updated: {filepath}")
                    count += 1
    print(f"Total files updated: {count}")

if __name__ == '__main__':
    main()
