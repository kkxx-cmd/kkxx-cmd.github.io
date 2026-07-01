#!/usr/bin/env python3
"""
数字花园更新 - 每天07:30运行，安徽省本地新闻
"""
import os
import sys
import traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kkxx_generate import fetch_hefei, update_list, git_push, send_tg, HTML_TEMPLATE, make_cards
from datetime import datetime

SITE_PATH = "/home/qgg/.openclaw/workspace/repo"
TG_TOKEN = "867692…GtQ4"
TG_CHAT_ID = "5222823781"


def send_alert(task, error_msg):
    """发送 CRITICAL 告警"""
    import requests
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        msg = f"🚨 <b>[CRITICAL] {task} 失败</b>\n\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n错误：<code>{error_msg}</code>"
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Alert TG: {e}")


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
        send_alert("数字花园", "安徽新闻网无数据")
    
    ok, err = git_push(f"garden: {date_str} {time_str}")
    if ok:
        report += "\n✅ Git push 成功"
    else:
        report += f"\n⚠️ Git push 失败: {err}"
        send_alert("数字花园", f"Git push 失败: {err}")
    
    print(report)
    send_tg(report)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        tb = traceback.format_exc()
        send_alert("数字花园", f"未捕获异常: {e}\n{tb}")
        sys.exit(1)
