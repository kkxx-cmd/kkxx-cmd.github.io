#!/usr/bin/env python3
"""
每日新闻更新 - 每天07:00运行
数据源：news-aggregator-skill（36氪、微博、V2EX、华尔街见闻、腾讯新闻）
"""
import os
import sys
import json
import subprocess
from datetime import datetime

SITE_PATH = "/home/qgg/.openclaw/workspace/repo"
NEWS_SCRIPT = os.path.expanduser("~/.agents/skills/news-aggregator-skill/scripts/fetch_news.py")

# Telegram config
TG_TOKEN = "867692HF2MTpb2BtYzZvZp1aDNAwqLR0GtQ4"
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
    a{{ color: #667eea; text-decoration: none; }}
  </style>
</head>
<body>
  <a class="back" href="../blog.html">← 返回</a>
  <h1>📰 每日新闻 · {date_cn}</h1>
  {cards}
</body>
</html>"""


def make_cards(news_list):
    """从 JSON 数据生成新闻卡片"""
    html = ""
    for i, item in enumerate(news_list, 1):
        title = item.get("title", "")
        url = item.get("url", "")
        source = item.get("source", "")
        heat = item.get("heat", "")
        time_str = item.get("time", "")
        # 跳过空标题
        if not title:
            continue
        heat_text = f" · 🔥{heat}" if heat else ""
        time_text = f" · {time_str}" if time_str else ""
        source_text = f"{source}{heat_text}{time_text}"
        html += f"""<div class="card">
    <div class="card-title">{i}. {title}</div>
    <div class="source">🔗 <a href="{url}" target="_blank">{source_text}</a></div>
  </div>\n"""
    return html


def fetch_news_with_skill():
    """通过 news-aggregator-skill 获取新闻"""
    cmd = [
        sys.executable, NEWS_SCRIPT,
        "--source", "36kr,weibo,v2ex,wallstreetcn,tencent",
        "--limit", "8",
        "--no-save"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=SITE_PATH)
        if result.returncode == 0:
            # 解析 JSON 输出
            output = result.stdout.strip()
            # 跳过非 JSON 的行（比如进度提示）
            json_start = output.find('[')
            if json_start >= 0:
                json_str = output[json_start:]
                data = json.loads(json_str)
                # 兼容 fetch_news.py 返回的不同格式
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "items" in data:
                    return data["items"]
        print(f"Skill stderr: {result.stderr[:500] if result.stderr else '(empty)'}")
        print(f"Skill stdout: {result.stdout[:500] if result.stdout else '(empty)'}")
    except Exception as e:
        print(f"Skill error: {e}")
    return []


def update_list(html_file, link_html):
    """向列表页追加链接（在 </body> 前）"""
    path = os.path.join(SITE_PATH, html_file)
    if not os.path.exists(path):
        print(f"文件不存在: {html_file}")
        return False
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # 在 </body> 前插入
    content = content.replace("</body>", link_html + "\n</body>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def git_push(msg):
    """提交并推送"""
    try:
        subprocess.run(["git", "add", "-A"], cwd=SITE_PATH, check=True)
        subprocess.run(["git", "commit", "-m", f"news: {msg}"], cwd=SITE_PATH, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=SITE_PATH, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Git: {e}")


def send_tg(msg):
    """Telegram 通知"""
    import requests
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"TG: {e}")


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
        report += f"✅ 新闻: {len(news)}条（36氪/微博/V2EX/华尔街见闻/腾讯）\n"
        update_list("blog/news.html",
                    f'<a class="post" href="news-{date_str}.html">'
                    f'<h3>📰 每日新闻 · {date_cn}</h3>'
                    f'<div class="meta">全球热点 · {len(news)}条</div></a>')
    else:
        report += "⚠️ Skill获取失败，降级到纯爬虫模式\n"
        # 降级：如果 skill 失败，尝试旧模式
        try:
            from kkxx_generate import fetch_news as fallback_fetch
            old_news = fallback_fetch()
            if old_news:
                cards = make_cards([{"title": n["title"], "url": n["link"], "source": n["source"]} for n in old_news])
                html = HTML_TEMPLATE.format(title=f"每日新闻 · {date_cn}", date_cn=date_cn, cards=cards)
                with open(f"blog/news-{date_str}.html", "w", encoding="utf-8") as f:
                    f.write(html)
                report += f"✅ 降级模式: {len(old_news)}条\n"
                update_list("blog/news.html",
                            f'<a class="post" href="news-{date_str}.html">'
                            f'<h3>📰 每日新闻 · {date_cn}</h3>'
                            f'<div class="meta">全球热点 · {len(old_news)}条</div></a>')
            else:
                report += "⚠️ 降级模式也失败\n"
        except Exception as e:
            report += f"⚠️ 降级报错: {e}\n"

    git_push(f"{date_str} {time_str}")
    print(report)
    send_tg(report)


if __name__ == "__main__":
    os.chdir(SITE_PATH)
    main()
