#!/usr/bin/env python3
"""
KKXX 内容生成脚本 - 纯Python，无需模型
数据抓取 → HTML生成 → Git push → Telegram通知
"""
import sys
import os
import re
import json
import subprocess
from datetime import datetime

# ========== 配置 ==========
SITE_PATH = "/home/qgg/site"
TG_TOKEN = "8676921192:AAE9_TSFANr34-zM7Omnxrj8w1YGKhWGtQ4"
TG_CHAT_ID = "5222823781"
os.chdir(SITE_PATH)

# ========== Telegram 通知 ==========
def send_tg(msg):
    """发送 Telegram 消息"""
    import requests
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"TG failed: {e}")

# ========== 1. 新闻获取 ==========
def fetch_news():
    import requests
    from bs4 import BeautifulSoup
    
    news_items = []
    rss_urls = [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    ]
    
    for url in rss_urls:
        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(resp.text, "xml")
            for item in soup.find_all("item")[:5]:
                title = item.find("title")
                link = item.find("link")
                if title:
                    news_items.append({
                        "title": title.text.strip(),
                        "link": link.text.strip() if link else "",
                        "source": url.split("/")[2].split(".")[1].upper() if url else "RSS"
                    })
        except Exception as e:
            print(f"RSS {url}: {e}")
    
    return news_items

# ========== 2. 合肥新闻 ==========
def fetch_hefei():
    import requests
    from bs4 import BeautifulSoup
    
    try:
        resp = requests.get(
            "https://cn.bing.com/news/search?q=%E5%90%88%E8%82%A5%E6%96%B0%E9%97%BB&format=rss",
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        soup = BeautifulSoup(resp.text, "xml")
        items = soup.find_all("item")[:5]
        return [{"title": i.find("title").text.strip(), "link": (i.find("link") or i.find("url")).text.strip(), "source": "合肥"} for i in items if i.find("title")]
    except Exception as e:
        print(f"合肥: {e}")
        return []

# ========== 3. A股 ==========
def fetch_stocks():
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        df = df.sort_values('涨跌幅', ascending=True).head(10)
        return [{"title": f"{r['名称']} ({r['代码']}) 跌 {r['涨跌幅']:.2f}%", "link": f"https://quote.eastmoney.com/sz{r['代码']}.html", "source": "A股"} for _, r in df.iterrows()]
    except Exception as e:
        print(f"股票: {e}")
        return []

# ========== 4. HTML生成 ==========
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    body{{ font-family: -apple-system, sans-serif; background: #0a0a0f; color: #e0e0e0; padding: 20px; max-width: 800px; margin: 0 auto; }}
    h1{{ background: linear-gradient(90deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px; }}
    .back{{ color: #667eea; text-decoration: none; font-size: 14px; }}
    .card{{ background: #12121a; border-radius: 12px; padding: 16px; margin: 12px 0; }}
    .card-title{{ font-size: 15px; color: #e0e0e0; line-height: 1.6; }}
    .source{{ color: #667eea; font-size: 12px; margin-top: 6px; }}
    a{{ color: #667eea; text-decoration: none; }}
  </style>
</head>
<body>
  <a class="back" href="../{back}">← 返回</a>
  <h1>{heading}</h1>
  {cards}
</body>
</html>"""

def make_cards(items):
    html = ""
    for i, item in enumerate(items, 1):
        html += f"""  <div class="card">
    <div class="card-title">{i}. {item['title']}</div>
    <div class="source">🔗 <a href="{item['link']}" target="_blank">{item.get('source', '原文')}</a></div>
  </div>\n"""
    return html

# ========== 5. 列表页更新 ==========
def update_list(list_file, new_card, marker="<!-- INSERT_MARKER -->"):
    try:
        with open(list_file, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = re.compile(rf'({re.escape(marker)})', re.IGNORECASE)
        if pattern.search(content):
            content = pattern.sub(f'{new_card}\n  {marker}', content)
            with open(list_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"列表更新失败 {list_file}: {e}")
    return False

# ========== 6. Git push ==========
def git_push(msg):
    try:
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", msg], check=True, capture_output=True)
        result = subprocess.run(["git", "push"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Git: {e}")
        return False

# ========== 主流程 ==========
def main():
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    date_cn = today.strftime("%Y年%m月%d日")
    time_str = today.strftime("%H:%M")
    
    report = f"📊 KKXX 内容更新 {date_cn} {time_str}\n\n"
    
    # 1. 新闻
    news = fetch_news()
    if news:
        html = HTML_TEMPLATE.format(
            title=f"每日新闻 · {date_cn} · KKXX",
            heading=f"📰 每日新闻 · {date_cn}",
            back="blog.html",
            cards=make_cards(news)
        )
        path = f"blog/news-{date_str}.html"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        report += f"✅ 新闻: {len(news)}条 → {path}\n"
        update_list("blog.html", f'<a class="post" href="blog/news-{date_str}.html"><h3>📰 每日新闻 · {date_cn}</h3><div class="meta">全球热点 · {len(news)}条</div></a>')
    else:
        report += "⚠️ 新闻获取失败\n"
    
    # 2. 合肥
    hefei = fetch_hefei()
    if hefei:
        html = HTML_TEMPLATE.format(
            title=f"合肥城事 · {date_cn} · KKXX",
            heading=f"🌿 数字花园 · {date_cn}",
            back="../garden.html",
            cards=make_cards(hefei)
        )
        path = f"garden/{date_str}.html"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        report += f"✅ 合肥: {len(hefei)}条 → {path}\n"
        update_list("garden.html", f'<a class="post" href="garden/{date_str}.html"><h3>🌿 数字花园 · {date_cn}</h3><div class="meta">合肥城事 · {len(hefei)}条</div></a>')
    else:
        report += "⚠️ 合肥获取失败\n"
    
    # 3. 股票（只生成数据，不生成详情页）
    stocks = fetch_stocks()
    if stocks:
        report += f"✅ 股票: {len(stocks)}只超卖\n"
    else:
        report += "⚠️ 股票获取失败\n"
    
    # 4. Git push
    if git_push(f"update: {date_str} {time_str}"):
        report += "\n✅ Git push 成功"
    else:
        report += "\n⚠️ Git push 失败"
    
    # 5. 通知
    print(report)
    send_tg(report)

if __name__ == "__main__":
    main()