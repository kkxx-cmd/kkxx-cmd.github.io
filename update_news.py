#!/usr/bin/env python3
"""
每日新闻更新 - 每天07:00运行
写入 blog/news.html
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kkxx_generate import fetch_news, update_list, git_push, send_tg, HTML_TEMPLATE, make_cards
from datetime import datetime

def main():
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    date_cn = today.strftime("%Y年%m月%d日")
    time_str = today.strftime("%H:%M")
    
    report = f"📰 每日新闻更新 {date_cn} {time_str}\n\n"
    
    news = fetch_news()
    if news:
        html = HTML_TEMPLATE.format(title=f"每日新闻 · {date_cn}", heading=f"📰 每日新闻 · {date_cn}", back="../blog.html", cards=make_cards(news))
        with open(f"blog/news-{date_str}.html", 'w', encoding='utf-8') as f:
            f.write(html)
        report += f"✅ 新闻: {len(news)}条\n"
        # 更新 blog/news.html，而不是 blog.html
        update_list("blog/news.html", f'<a class="post" href="news-{date_str}.html"><h3>📰 每日新闻 · {date_cn}</h3><div class="meta">全球热点 · {len(news)}条</div></a>')
    else:
        report += "⚠️ 新闻获取失败\n"
    
    git_push(f"news: {date_str} {time_str}")
    print(report)
    send_tg(report)

if __name__ == "__main__":
    main()
