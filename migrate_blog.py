#!/usr/bin/env python3
"""一次性迁移脚本：把现有博客文章写入 blog.html"""
import os
import re
from datetime import datetime

SITE_PATH = "/home/qgg/.openclaw/workspace/repo"
BLOG_HTML = os.path.join(SITE_PATH, "blog.html")

# 读取现有 blog/ 下的博客文章（排除 news-*）
posts = []
for f in sorted(os.listdir(os.path.join(SITE_PATH, "blog"))):
    if not f.endswith(".html") or f.startswith("news-") or f == "news.html" or f == "rss.xml":
        continue
    path = os.path.join(SITE_PATH, "blog", f)
    with open(path, "r", encoding="utf-8") as fp:
        content = fp.read()
    
    # 提取日期
    date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", f) or re.search(r"(\d{4})-(\d{2})-(\d{2})", content)
    date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}" if date_match else "2026-01-01"
    
    # 提取标题
    title_match = re.search(r"<h[123][^>]*>([^<]+)</h[123]>", content)
    title = title_match.group(1).strip() if title_match else f
    
    posts.append({"date": date, "title": title, "file": f})

# 按日期倒序排列
posts.sort(key=lambda x: x["date"], reverse=True)

# 生成链接 HTML
links_html = ""
for p in posts:
    links_html += f'  <a class="post" href="blog/{p["file"]}"><h3>{p["title"]}</h3><div class="meta">{p["date"]}</div></a>\n'

# 更新 blog.html
with open(BLOG_HTML, "r", encoding="utf-8") as f:
    content = f.read()

content = re.sub(r'<!-- BLOG_POSTS_MARKER -->', links_html.strip() + '\n  <!-- BLOG_POSTS_MARKER -->', content)

with open(BLOG_HTML, "w", encoding="utf-8") as f:
    f.write(content)

print(f"已迁移 {len(posts)} 篇文章到 blog.html")
for p in posts[:5]:
    print(f"  {p['date']} | {p['title']}")
