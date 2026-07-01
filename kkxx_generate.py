#!/usr/bin/env python3
"""
KKXX 内容生成脚本 - 纯Python，无需模型
数据抓取 → HTML生成 → Git push → Telegram通知
"""
import os
import re
import subprocess
from datetime import datetime

SITE_PATH = "/home/qgg/.openclaw/workspace/repo"
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

def fetch_hefei():
    """抓取安徽省本地新闻，来源：安徽新闻网（中安在线）"""
    import requests
    import re
    
    news = []
    
    # 安徽新闻网（中安在线）
    sources = [
        ('http://ah.anhuinews.com/szxw/', '安徽新闻'),
        ('http://ah.anhuinews.com/rs/', '人事任免'),
        ('http://ah.anhuinews.com/lsa/', '政策法规'),
        ('http://ah.anhuinews.com/ahtopic/', '专题'),
    ]
    
    for url, cat in sources:
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            r.encoding = r.apparent_encoding or 'gbk'
            html = r.text
            
            # 提取链接和标题
            links = re.findall(r'<a[^>]*href=["\'](http://ah\.anhuinews\.com/[^"\']*\.html?)["\'][^>]*>([^<]+)</a>', html)
            
            for href, title in links:
                title = title.strip()
                # 过滤：标题长度合理 + 含年份
                if not title or len(title) < 6 or len(title) > 60:
                    continue
                if not re.search(r'202[6-9]', href):
                    continue
                # 去重
                    if not any(n['link'] == href for n in news):
                        # 从 URL 分类
                        cat_class = cat
                        if '/rs/' in href:
                            cat_class = '人事任免'
                        elif '/lsa/' in href:
                            cat_class = '政策法规'
                        elif '/ahtopic/' in href:
                            cat_class = '专题'
                        elif '/szxw/' in href:
                            cat_class = '安徽新闻'
                        news.append({'title': f'[{cat_class}] {title}', 'link': href, 'source': '安徽新闻网'})
        except Exception as e:
            print(f"安徽新闻网{cat}: {e}")
        if len(news) >= 10:
            break
    
    return news[:10]

def fetch_stocks():
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot()  # 腾讯接口
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