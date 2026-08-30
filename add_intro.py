import sys
import os

def add_intro_to_file(filepath, title, intro_text):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the line with the heading
    for i, line in enumerate(lines):
        if title in line.strip():
            # Insert after this line
            # We'll insert two lines: the intro paragraph and a blank line before the links?
            # Actually we want: heading, then intro paragraph, then blank line, then links.
            # But we need to preserve existing blank lines? We'll just insert after the heading.
            # Insert the intro paragraph as a new line, and ensure there is a blank line after it if not already.
            # Let's construct new lines.
            new_lines = lines[:i+1]  # up to and including the heading line
            new_lines.append('  <p>' + intro_text + '</p>\n')
            # Now we need to skip any existing blank lines? We'll just continue with the rest.
            # But we should avoid duplicate blank lines. We'll just append the rest.
            new_lines.extend(lines[i+1:])
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True
    return False

if __name__ == '__main__':
    # For blog.html
    add_intro_to_file('blog.html', '📝 博客文章', '这里是KKXX的技术博客和新闻更新，记录每日的学习、发现和项目进展。')
    # For news.html (already done but ensure)
    add_intro_to_file('blog/news.html', '📰 每日新闻', '这里是KKXX的每日新闻摘要，提供全球热点新闻的简要概述。')
    print('Done')
