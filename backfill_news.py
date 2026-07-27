#!/usr/bin/env python3
"""
补全缺失日期的新闻文件
"""
import os
import sys

SITE_PATH = "/home/qgg/.openclaw/workspace/repo"
os.chdir(SITE_PATH)

# 导入现有模块的函数
sys.path.insert(0, SITE_PATH)
from update_news import (
    fetch_news_with_skill, make_cards, HTML_TEMPLATE,
    update_list, git_push, send_alert, send_tg
)

# 缺失的日期
MISSING_DATES = ['2026-07-18', '2026-07-19', '2026-07-20']

def date_cn(date_str):
    """2026-07-18 -> 2026年07月18日"""
    y, m, d = date_str.split('-')
    return f"{y}年{m}月{d}日"

def main():
    import datetime
    now = datetime.datetime.now()
    report = "📰 补全缺失新闻\n\n"
    
    # 获取一次新闻数据
    news = fetch_news_with_skill()
    if not news:
        report += "⚠️ 无法获取新闻数据\n"
        send_alert("补全新闻", "无法获取新闻数据")
        print(report)
        return
    
    report += f"✅ 获取新闻: {len(news)}条\n"
    
    for date_str in MISSING_DATES:
        dc = date_cn(date_str)
        cards = make_cards(news)
        html = HTML_TEMPLATE.format(title=f"每日新闻 · {dc}", date_cn=dc, cards=cards)
        
        filepath = f"blog/news-{date_str}.html"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        
        card_html = f'<a class="post" href="news-{date_str}.html"><h3>📰 每日新闻 · {dc}</h3><div class="meta">全球热点 · {len(news)}条</div></a>'
        update_list("blog/news.html", card_html)
        report += f"✅ 已生成: news-{date_str}.html\n"
    
    # Git push
    ok, err = git_push(f"backfill news: {', '.join(MISSING_DATES)}")
    if ok:
        report += "\n✅ Git push 成功"
    else:
        report += f"\n⚠️ Git push 失败: {err}"
    
    print(report)
    send_tg(report)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        send_alert("补全新闻", f"异常: {e}")
        sys.exit(1)
