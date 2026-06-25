#!/usr/bin/env python3
"""
KKXX 内容生成脚本 - 纯Python，无需模型
数据抓取 → HTML生成 → Git push → Telegram通知
"""
import os
import re
import subprocess
from datetime import datetime

SITE_PATH = "/home/qgg/site"
TG_TOKEN = "8676921192:AAE9_TSFANr34-zM7Omnxr8w1YGKhWGtQ4"
TG_CHAT_ID = "5222823781"
os.chdir(SITE_PATH)

def send_tg(msg):
    import requests
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"TG: {e}")

def fetch_news():
    import requests
    from bs4 import BeautifulSoup
    news = []
    # 中文新闻源
    sources = [
        ("https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=10&page=1&r=", "新浪", "json"),
        ("https://www.thepaper.cn/rss/rss.xml", "澎湃", "xml"),
        ("https://www.sina.com.cn/rss.xml", "新浪财经", "xml"),
    ]
    for url, name, fmt in sources:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            if fmt == "json" or "json" in r.headers.get("content-type", ""):
                import json
                data = r.json()
                for item in data.get("result", {}).get("data", [])[:5]:
                    title = item.get("title", "")
                    if title and len(title) > 5:
                        news.append({"title": title, "link": item.get("url", ""), "source": name})
            else:
                soup = BeautifulSoup(r.text, "xml")
                for item in soup.find_all("item")[:5]:
                    t = item.find("title")
                    l = item.find("link")
                    if t:
                        title = t.text.strip()
                        link = l.text.strip() if l else ""
                        if title and len(title) > 5:
                            news.append({"title": title, "link": link, "source": name})
            if len(news) >= 10:
                break
        except Exception as e:
            print(f"新闻 {name}: {e}")
    return news[:10]

def fetch_hefei():
    import requests
    from bs4 import BeautifulSoup
    for url in [
        "https://www.sohu.com/tag/2446954827/",
        "https://news.baidu.com/ns?word=%E5%90%88%E8%82%A5%E6%96%B0%E9%97%BB",
    ]:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"}, proxies={"http": None, "https": None})
            soup = BeautifulSoup(r.text, "html.parser")
            items = []
            for a in soup.find_all("a", href=True)[:15]:
                t = a.get_text(strip=True)
                if t and 5 < len(t) < 80 and "合肥" in t:
                    href = a["href"]
                    if href.startswith("//"):
                        href = "https:" + href
                    elif href.startswith("/"):
                        href = "https://www.sohu.com" + href
                    items.append({"title": t, "link": href, "source": "合肥"})
            if items:
                return items[:5]
        except Exception as e:
            print(f"合肥 {url[:30]}: {e}")
    return [{"title": "合肥城事更新", "link": "https://www.hefei.gov.cn/", "source": "合肥市政府"}]

def fetch_stocks():
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        df = df[df["涨跌幅"] < 0].sort_values("涨跌幅", ascending=True).head(10)
        return [{"title": f"{r['名称']} ({r['代码']}) 跌 {r['涨跌幅']:.2f}% 现价 {r['最新价']:.2f}", "link": f"https://quote.eastmoney.com/sz{r['代码']}.html", "source": "A股"} for _, r in df.iterrows()]
    except Exception as e:
        print(f"股票: {e}")
        return []

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
  <a class="back" href="{back}">← 返回</a>
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

def update_list(list_file, new_card, marker="<!-- INSERT_MARKER -->"):
    try:
        with open(list_file, 'r', encoding='utf-8') as f:
            content = f.read()
        # 防重复：先检查是否已存在今日链接（精确匹配）
        if new_card.strip() in content.strip():
            print(f"列表已存在，跳过: {list_file}")
            return True
        pattern = re.compile(rf'{re.escape(marker)}', re.IGNORECASE)
        if pattern.search(content):
            content = pattern.sub(f'{new_card}\n  {marker}', content, count=1)
            with open(list_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"列表更新失败 {list_file}: {e}")
    return False

def git_push(msg):
    try:
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", msg], check=True, capture_output=True)
        r = subprocess.run(["git", "push"], capture_output=True, text=True)
        return r.returncode == 0
    except Exception as e:
        print(f"Git: {e}")
        return False

def main():
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    date_cn = today.strftime("%Y年%m月%d日")
    time_str = today.strftime("%H:%M")
    report = f"📊 KKXX 内容更新 {date_cn} {time_str}\n\n"
    
    # 新闻
    news = fetch_news()
    if news:
        html = HTML_TEMPLATE.format(title=f"每日新闻 · {date_cn}", heading=f"📰 每日新闻 · {date_cn}", back="../blog.html", cards=make_cards(news))
        with open(f"blog/news-{date_str}.html", 'w', encoding='utf-8') as f:
            f.write(html)
        report += f"✅ 新闻: {len(news)}条\n"
        update_list("blog.html", f'<a class="post" href="blog/news-{date_str}.html"><h3>📰 每日新闻 · {date_cn}</h3><div class="meta">全球热点 · {len(news)}条</div></a>')
    else:
        report += "⚠️ 新闻获取失败\n"
    
    # 合肥
    hefei = fetch_hefei()
    if hefei:
        html = HTML_TEMPLATE.format(title=f"合肥城事 · {date_cn}", heading=f"🌿 数字花园 · {date_cn}", back="../garden.html", cards=make_cards(hefei))
        with open(f"garden/{date_str}.html", 'w', encoding='utf-8') as f:
            f.write(html)
        report += f"✅ 合肥: {len(hefei)}条\n"
        update_list("garden.html", f'<a class="post" href="garden/{date_str}.html"><h3>🌿 数字花园 · {date_cn}</h3><div class="meta">合肥城事 · {len(hefei)}条</div></a>')
    else:
        report += "⚠️ 合肥获取失败\n"
    
    # 股票
    stocks = fetch_stocks()
    if stocks:
        report += f"✅ 股票: {len(stocks)}只超卖\n"
    else:
        report += "⚠️ 股票获取失败\n"
    
    # Git push
    if git_push(f"update: {date_str} {time_str}"):
        report += "\n✅ Git push 成功"
    else:
        report += "\n⚠️ Git push 失败"
    
    print(report)
    send_tg(report)

if __name__ == "__main__":
    main()