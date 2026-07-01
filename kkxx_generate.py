#!/usr/bin/env python3
"""
KKXX 内容生成脚本 - 纯Python，无需模型
数据抓取 → HTML生成 → Git push → Telegram通知
"""
import os
import re
import subprocess
import json
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


def extract_date_from_href(href):
    """从链接提取日期，如 'news-2026-07-01.html' → '2026-07-01'"""
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', href)
    if m:
        return f"{m.group(1)}{m.group(2)}{m.group(3)}"
    return "19700101"


def update_list(list_file, new_card, marker="<!-- INSERT_MARKER -->"):
    """全量重建列表页：提取所有文章链接 → 去重 → 按日期倒序 → 重写文件"""
    try:
        with open(list_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        post_pattern = re.compile(r'(\s*\n\s*)?(<a class="post"[^>]*>.*?</a>)', re.DOTALL)
        existing_posts = post_pattern.findall(content)
        existing_posts = [m[1] for m in existing_posts if m[1]]
        
        all_posts = existing_posts + [new_card]
        
        # 去重：按 href，保留最后出现的
        seen = {}
        for post in all_posts:
            href_match = re.search(r'href="([^"]*)"', post)
            if href_match:
                seen[href_match.group(1)] = post
        
        # 按日期倒序排列
        unique_posts = list(seen.values())
        unique_posts.sort(
            key=lambda p: extract_date_from_href(re.search(r'href="([^"]*)"', p).group(1)) if re.search(r'href="([^"]*)"', p) else "19700101",
            reverse=True
        )
        
        # 找到第一个 post 的开始位置和最后一个 post 的结束位置
        first_match = post_pattern.search(content)
        if not first_match:
            return False
        
        last_match = None
        for m in post_pattern.finditer(content):
            last_match = m
        
        before = content[:first_match.start()]
        after = content[last_match.end():]
        
        new_content = before + '\n'.join(unique_posts) + '\n' + after
        
        with open(list_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
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


# ==============================================

def fetch_hefei():
    """抓取安徽省本地新闻，来源：安徽新闻网（中安在线）全频道"""
    import requests
    import re
    
    channels = [
        ('http://ah.anhuinews.com/szxw/', '时政新闻'),
        ('http://ah.anhuinews.com/rs/', '人事任免'),
        ('http://ah.anhuinews.com/lsa/', '政策法规'),
        ('http://ah.anhuinews.com/ahtopic/', '专题报道'),
        ('http://ah.anhuinews.com/gnxw/', '国内新闻'),
        ('http://ah.anhuinews.com/shxw/', '社会新闻'),
        ('http://ah.anhuinews.com/shfz/', '社会发展'),
        ('http://ah.anhuinews.com/cjxw/', '财经新闻'),
        ('http://ah.anhuinews.com/kjxw/', '科技新闻'),
        ('http://ah.anhuinews.com/jyxw/', '教育新闻'),
        ('http://ah.anhuinews.com/jkq/', '健康圈'),
        ('http://ah.anhuinews.com/', '综合'),
    ]
    
    all_news = []
    for url, category in channels:
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            r.encoding = r.apparent_encoding or 'utf-8'
            html = r.text
            
            links = re.findall(r'<a[^>]*href=["\'](http://ah\.anhuinews\.com/[^"\']*\.html?)["\'][^>]*>([^<]+)</a>', html)
            
            for href, title in links:
                title = title.strip()
                if not title or len(title) < 8 or len(title) > 50:
                    continue
                if not re.search(r'2025|2026', href):
                    continue
                if not any(n['link'] == href for n in all_news):
                    cat = category
                    if '/rs/' in href: cat = '人事任免'
                    elif '/lsa/' in href: cat = '政策法规'
                    elif '/ahtopic/' in href: cat = '专题报道'
                    elif '/szxw/' in href: cat = '时政新闻'
                    elif '/gnxw/' in href: cat = '国内新闻'
                    elif '/shxw/' in href: cat = '社会新闻'
                    elif '/shfz/' in href: cat = '社会发展'
                    elif '/cjxw/' in href: cat = '财经新闻'
                    elif '/kjxw/' in href: cat = '科技新闻'
                    elif '/jyxw/' in href: cat = '教育新闻'
                    elif '/jkq/' in href: cat = '健康圈'
                    all_news.append({'title': f'[{cat}] {title}', 'link': href, 'source': '安徽新闻网'})
        except Exception as e:
            print(f"安徽新闻网{category}: {e}")
    
    # 按日期倒序
    for n in all_news:
        m = re.search(r'(\d{4})-(\d{2})-(\d{2})', n['link'])
        if m:
            n['_date'] = f'{m.group(1)}{m.group(2)}{m.group(3)}'
        else:
            n['_date'] = '20200101'
    
    all_news.sort(key=lambda x: x['_date'], reverse=True)
    return all_news[:30]


def fetch_stocks():
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot()
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


def main():
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    date_cn = today.strftime("%Y年%m月%d日")
    time_str = today.strftime("%H:%M")
    report = f"📊 KKXX 内容更新 {date_cn} {time_str}\n\n"
    
    hefei = fetch_hefei()
    if hefei:
        html = HTML_TEMPLATE.format(title=f"合肥城事 · {date_cn}", heading=f"🌿 数字花园 · {date_cn}", back="../garden.html", cards=make_cards(hefei))
        with open(f"garden/{date_str}.html", 'w', encoding='utf-8') as f:
            f.write(html)
        report += f"✅ 合肥: {len(hefei)}条\n"
        update_list("garden.html", f'<a class="post" href="garden/{date_str}.html"><h3>🌿 数字花园 · {date_cn}</h3><div class="meta">合肥城事 · {len(hefei)}条</div></a>')
    else:
        report += "⚠️ 合肥获取失败\n"
    
    stocks = fetch_stocks()
    if stocks:
        report += f"✅ 股票: {len(stocks)}只超卖\n"
    else:
        report += "⚠️ 股票获取失败\n"
    
    if git_push(f"update: {date_str} {time_str}"):
        report += "\n✅ Git push 成功"
    else:
        report += "\n⚠️ Git push 失败"
    
    print(report)
    send_tg(report)


if __name__ == "__main__":
    main()
