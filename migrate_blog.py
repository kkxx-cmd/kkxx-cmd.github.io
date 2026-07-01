#!/usr/bin/env python3
"""修复：正确提取标题，处理带 front matter 的文件"""
import os
import re

SITE_PATH = "/home/qgg/.openclaw/workspace/repo"
BLOG_HTML = os.path.join(SITE_PATH, "blog.html")

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
    
    # 提取标题（多种方式）
    title = None
    # 方式1: HTML heading 标签
    title_match = re.search(r"<h[123][^>]*>([^<]+)</h[123]>", content)
    if title_match:
        title = title_match.group(1).strip()
    
    # 方式2: 正文第一行（排除 front matter）
    if not title:
        # 去掉 front matter 后的第一行
        text = re.sub(r"^---[\s\S]*?---\s*", "", content).strip()
        first_line = text.split("\n")[0].strip()
        if first_line:
            # 去掉 markdown heading 符号
            title = re.sub(r"^#+\s*", "", first_line).strip()
    
    # 兜底：使用文件名
    if not title:
        title = f.replace(".html", "")
    
    posts.append({"date": date, "title": title, "file": f})

posts.sort(key=lambda x: x["date"], reverse=True)

links_html = ""
for p in posts:
    links_html += f'  <a class="post" href="blog/{p["file"]}"><h3>{p["title"]}</h3><div class="meta">{p["date"]}</div></a>\n'

# 重新生成 blog.html
html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>博客文章 · KKXX</title>
  <meta name="description" content="KKXX技术博客">
  <meta name="robots" content="index, follow">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0a0a0f; color: #e0e0e0; min-height: 100vh; padding: 40px 20px; max-width: 800px; margin: 0 auto; }
    .back { display: inline-block; color: #667eea; text-decoration: none; font-size: 13px; margin-bottom: 30px; }
    .back:hover { text-decoration: underline; }
    .rss-link { margin-left: 16px; } 
    h2 { font-size: 20px; margin-bottom: 24px; color: #e0e0e0; }
    .post { background: #12121a; border: 1px solid #1e1e2e; border-radius: 12px; padding: 20px 24px; margin-bottom: 14px; text-decoration: none; color: #e0e0e0; display: block; transition: border-color 0.2s, transform 0.2s; }
    .post:hover { border-color: #667eea; transform: translateY(-2px); }
    .post h3 { font-size: 16px; font-weight: 500; margin-bottom: 6px; }
    .post .meta { font-size: 12px; color: #555; margin-bottom: 4px; }
  </style>
</head>
<body>
  <a class="back" href="index.html">← 返回导航</a>
  <a class="back rss-link" href="blog/rss.xml">📡 RSS订阅</a>

  <h2>📝 博客文章</h2>

''' + links_html + '''
</body>
</html>'''

with open(BLOG_HTML, "w", encoding="utf-8") as f:
    f.write(html)

print(f"已迁移 {len(posts)} 篇文章到 blog.html")
for p in posts[:10]:
    print(f"  {p['date']} | {p['title']}")
