#!/usr/bin/env python3
"""
每日新闻更新 - 每天07:00运行
数据源：news-aggregator-skill（36氪、微博、V2EX、华尔街见闻、腾讯新闻）
"""
import os
import sys
import re
import json
import subprocess
import traceback
from datetime import datetime
import urllib.parse

SITE_PATH = "."
NEWS_SCRIPT = os.path.expanduser("~/.agents/skills/news-aggregator-skill/scripts/fetch_news.py")

TG_TOKEN = "867692…GtQ4"
TG_CHAT_ID = "5222823781"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    body{{ font-family: -apple-system, sans-serif; background: #0a0a0f; color: #e0e0e0; padding: 20px; max-width: 800px; margin: 0 auto; }}
    h1{{ background: linear-gradient(90deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px; font-size: 22px; }}
    .back{{ color: #667eea; text-decoration: none; font-size: 14px; display: inline-block; margin-bottom: 16px; }}
    .card{{ background: #12121a; border-radius: 12px; padding: 16px; margin: 12px 0; border: 1px solid #1e1e2e; }}
    .card-title{{ font-size: 15px; color: #e0e0e0; line-height: 1.6; }}
    .source{{ color: #667eea; font-size: 12px; margin-top: 6px; }}
    .card-summary{{ font-size: 13px; color: #888; margin-top: 8px; line-height: 1.5; }}
    a{{ color: #667eea; text-decoration: none; }}
  </style>
</head>
<body>
  <a class="back" href="../blog.html">← 返回</a>
  <h1>📰 每日新闻 · {date_cn}</h1>
  {cards}
  <script>
    // 投票功能
    function voteNews(url, type) {
      const voteKey = 'kkxx_news_vote_' + btoa(url).replace(/[+/=]/g, '');
      const votes = JSON.parse(localStorage.getItem(voteKey) || '{{"up":0,"down":0}}');
      
      if (type === 'up') {
        votes.up += 1;
      } else if (type === 'down') {
        votes.down += 1;
      }
      
      localStorage.setItem(voteKey, JSON.stringify(votes));
      
      // 更新显示
      const upSpan = document.querySelector(`[data-url="${url}"] .vote-count-up`);
      const downSpan = document.querySelector(`[data-url="${url}"] .vote-count-down`);
      if (upSpan) upSpan.textContent = votes.up;
      if (downSpan) downSpan.textContent = votes.down;
    }
    
    // 页面加载时初始化投票显示
    document.addEventListener('DOMContentLoaded', function() {
      // 由于每个新闻卡片有独立的URL，我们需要找到所有投票按钮并初始化
      // 但这里采用另一种方法：在每个卡片渲染时就设置初始值
      // 这个脚本会在页面加载后运行，但我们也会在服务器端设置初始值
    });
  </script>
</body>
</html>"""


def send_tg(msg):
    import requests
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"TG: {e}")


def send_alert(task, error_msg):
    """发送 CRITICAL 告警"""
    msg = f"🚨 <b>[CRITICAL] {task} 失败</b>\n\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n错误：<code>{error_msg}</code>"
    send_tg(msg)


def make_cards(news_list):
    html = ""
    for i, item in enumerate(news_list, 1):
        title = item.get("title", "")
        url = item.get("url", "")
        source = item.get("source", "")
        summary = item.get("summary", "")
        heat = item.get("heat", "")
        time_str = item.get("time", "")
        if not title:
            continue
        heat_text = f" · 🔥{heat}" if heat else ""
        time_text = f" · {time_str}" if time_str else ""
        source_text = f"{source}{heat_text}{time_text}"
        # URL encode for share links
        encoded_url = urllib.parse.quote(url, safe='')
        encoded_title = urllib.parse.quote(title, safe='')
        card = '<div class="card" data-url="'+url+'">\n'
        card += f'    <div class="card-title">{i}. {title}</div>\n'
        card += f'    <div class="source">🔗 <a href="{url}" target="_blank">{source_text}</a></div>'
        if summary:
            card += f'\n    <div class="card-summary">{summary[:120]}</div>'
        card += f'\n    <div class="share-buttons" style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #1e1e2e;">'
        card += f'        <a href="https://service.weibo.com/share/share.php?url={encoded_url}&title={encoded_title}" target="_blank" title="分享到微博" style="margin-right: 8px; font-size: 16px;">📤</a>'
        card += f'        <a href="https://twitter.com/intent/tweet?url={encoded_url}&text={encoded_title}" target="_blank" title="分享到Twitter" style="margin-right: 8px; font-size: 16px;">🐦</a>'
        card += f'        <a href="#" onclick="navigator.clipboard.writeText(window.location.href); alert(\'链接已复制！\'); return false;" title="复制链接" style="font-size: 16px;">🔗</a>'
        card += f'    </div>'
        card += f'\n    <div class="vote-buttons" style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #1e1e2e; display: flex; gap: 12px; align-items: center;">'
        card += f'        <button onclick="voteNews(\'{encoded_url}\', \'up\')" style="background: none; border: none; color: #4caf50; cursor: pointer; font-size: 16px; display: flex; align-items: center; gap: 4px;">'
        card += f'            👍 <span class="vote-count-up">0</span>'
        card += f'        </button>'
        card += f'        <button onclick="voteNews(\'{encoded_url}\', \'down\')" style="background: none; border: none; color: #f44336; cursor: pointer; font-size: 16px; display: flex; align-items: center; gap: 4px;">'
        card += f'            👎 <span class="vote-count-down">0</span>'
        card += f'        </button>'
        card += f'    </div>'
        card += '\n  </div>\n'
        html += card
    return html


def normalize_title(title):
    return re.sub(r'[\s\W_]+', '', title.lower())


def dedup_news(news_list, threshold=0.7):
    from difflib import SequenceMatcher
    unique = []
    seen_norms = []
    for item in news_list:
        title = item.get('title', '')
        norm = normalize_title(title)
        if not norm:
            continue
        is_dup = False
        for prev_norm in seen_norms:
            if SequenceMatcher(None, norm, prev_norm).ratio() >= threshold:
                is_dup = True
                break
        if not is_dup:
            unique.append(item)
            seen_norms.append(norm)
    return unique


def fetch_news_with_skill():
    cmd = [sys.executable, NEWS_SCRIPT, "--source", "36kr,weibo,v2ex,wallstreetcn,tencent", "--limit", "8", "--no-save"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=SITE_PATH)
        if result.returncode == 0:
            output = result.stdout.strip()
            json_start = output.find('[')
            if json_start >= 0:
                data = json.loads(output[json_start:])
                if isinstance(data, list):
                    return dedup_news(data)
                elif isinstance(data, dict) and "items" in data:
                    return dedup_news(data["items"])
    except Exception as e:
        print(f"Skill error: {e}")
    return []


def extract_date_from_href(href):
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', href)
    return f"{m.group(1)}{m.group(2)}{m.group(3)}" if m else "19700101"


def update_list(html_file, new_card):
    if not os.path.exists(html_file):
        return False
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    post_pattern = re.compile(r'(<a class="post"[^>]*>.*?</a>)', re.DOTALL)
    existing_posts = post_pattern.findall(content)
    all_posts = existing_posts + [new_card]
    seen = {}
    for post in all_posts:
        href_match = re.search(r'href="([^"]*)"', post)
        if href_match:
            seen[href_match.group(1)] = post
    unique_posts = list(seen.values())
    unique_posts.sort(key=lambda p: extract_date_from_href(re.search(r'href="([^"]*)"', p).group(1)) if re.search(r'href="([^"]*)"', p) else "19700101", reverse=True)
    first_match = post_pattern.search(content)
    if not first_match:
        return False
    last_match = None
    for m in post_pattern.finditer(content):
        last_match = m
    before = content[:first_match.start()]
    after = content[last_match.end():]
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(before + '\n'.join(unique_posts) + '\n' + after)
    return True


def git_push(msg):
    try:
        subprocess.run(["git", "add", "-A"], cwd=SITE_PATH, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"news: {msg}"], cwd=SITE_PATH, check=True, capture_output=True)
        r = subprocess.run(["git", "push", "origin", "main"], cwd=SITE_PATH, capture_output=True, text=True)
        return (r.returncode == 0, r.stderr or r.stdout if r.returncode != 0 else None)
    except Exception as e:
        return (False, str(e))


def main():
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    date_cn = today.strftime("%Y年%m月%d日")
    time_str = today.strftime("%H:%M")
    report = f"📰 每日新闻更新 {date_cn} {time_str}\n\n"

    news = fetch_news_with_skill()
    if news:
        cards = make_cards(news)
        html = HTML_TEMPLATE.format(title=f"每日新闻 · {date_cn}", date_cn=date_cn, cards=cards)
        with open(f"blog/news-{date_str}.html", "w", encoding="utf-8") as f:
            f.write(html)
        report += f"✅ 新闻: {len(news)}条\n"
        update_list("blog/news.html", f'<a class="post" href="news-{date_str}.html"><h3>📰 每日新闻 · {date_cn}</h3><div class="meta">全球热点 · {len(news)}条</div></a>')
    else:
        report += "⚠️ Skill获取失败，降级到纯爬虫模式\n"
        try:
            from kkxx_generate import fetch_news as fallback_fetch
            old_news = fallback_fetch()
            if old_news:
                cards = make_cards([{"title": n["title"], "url": n["link"], "source": n["source"]} for n in old_news])
                html = HTML_TEMPLATE.format(title=f"每日新闻 · {date_cn}", date_cn=date_cn, cards=cards)
                with open(f"blog/news-{date_str}.html", "w", encoding="utf-8") as f:
                    f.write(html)
                report += f"✅ 降级模式: {len(old_news)}条\n"
                update_list("blog/news.html", f'<a class="post" href="news-{date_str}.html"><h3>📰 每日新闻 · {date_cn}</h3><div class="meta">全球热点 · {len(old_news)}条</div></a>')
            else:
                report += "⚠️ 降级模式也失败\n"
                send_alert("每日新闻", "Skill 和降级模式均无数据")
        except Exception as e:
            report += f"⚠️ 降级报错: {e}\n"
            send_alert("每日新闻", f"降级异常: {e}")

    ok, err = git_push(f"{date_str} {time_str}")
    if ok:
        report += "\n✅ Git push 成功"
    else:
        report += f"\n⚠️ Git push 失败: {err}"
        send_alert("每日新闻", f"Git push 失败: {err}")

    print(report)
    send_tg(report)


if __name__ == "__main__":
    os.chdir(SITE_PATH)
    try:
        main()
    except Exception as e:
        send_alert("每日新闻", f"未捕获异常: {e}\n{traceback.format_exc()}")
        sys.exit(1)
