import os
import re
from bs4 import BeautifulSoup

# Define directories to process
dirs = ['.', 'blog', 'garden', 'stock']
# We'll process all HTML files in these directories

css_collected = []

for directory in dirs:
    dir_path = os.path.join(directory)
    if not os.path.isdir(dir_path):
        continue
    for filename in os.listdir(dir_path):
        if filename.endswith('.html'):
            filepath = os.path.join(dir_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
                continue

            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            style_tag = soup.find('style')
            if style_tag and style_tag.string:
                css_text = style_tag.string.strip()
                if css_text:
                    # Remove the style tag
                    style_tag.decompose()
                    # Collect CSS with a comment
                    css_collected.append(f"/* From {filepath} */\n{css_text}\n")
                    # Write back the HTML without the style tag
                    try:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(str(soup))
                        print(f"Extracted CSS from {filepath}")
                    except Exception as e:
                        print(f"Error writing {filepath}: {e}")
            else:
                # No style tag or empty
                pass

# Append collected CSS to styles.css
if css_collected:
    try:
        with open('styles.css', 'a', encoding='utf-8') as f:
            f.write("\n/* ==== Externalized CSS from individual pages ==== */\n")
            f.write("\n".join(css_collected))
        print(f"Appended {len(css_collected)} CSS blocks to styles.css")
    except Exception as e:
        print(f"Error appending to styles.css: {e}")
else:
    print("No CSS found to externalize.")
