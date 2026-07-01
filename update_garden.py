#!/usr/bin/env python3
"""
数字花园更新 - 每天07:30运行，安徽省本地新闻
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kkxx_generate import fetch_hefei, update_list, git_push, send_tg, HTML_TEMPLATE, make_cards
from datetime import datetime

def main():
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    date_cn = today.strftime("%Y年%m月%d日")
    time_str = today.strftime("%H:%M")
    
    report = f"🌿 数字花园更新 {date_cn} {time_str}\n\n"
    
    items = fetch_hefei()
    if items:
        html = HTML_TEMPLATE.format(title=f"数字花园 · {date_cn}", heading=f"🌿 数字花园 · {date_cn}", back="../garden.html", cards=make_cards(items))
        with open(f"garden/{date_str}.html", 'w', encoding='utf-8') as f:
            f.write(html)
        report += f"✅ 安徽: {len(items)}条新闻\n"
        update_list("garden.html", f'<a class="post" href="garden/{date_str}.html"><h3>🌿 数字花园 · {date_cn}</h3><div class="meta">合肥城事 · {len(items)}条</div></a>')
    else:
        report += "⚠️ 安徽新闻获取失败\n"
    
    git_push(f"garden: {date_str} {time_str}")
    print(report)
    send_tg(report)

if __name__ == "__main__":
    main()
