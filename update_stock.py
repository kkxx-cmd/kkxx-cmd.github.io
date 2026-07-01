#!/usr/bin/env python3
"""
股票专区更新 - 工作日10:00运行
东方财富接口获取A股超卖数据
"""
import os
import sys
import requests
import json
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kkxx_generate import update_list, git_push, send_tg, HTML_TEMPLATE, make_cards

SITE_PATH = "/home/qgg/.openclaw/workspace/repo"

HTML_TEMPLATE_STOCK = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, sans-serif; background: #0a0a0f; color: #e0e0e0; min-height: 100vh; padding: 40px 20px; }}
    .back {{ display: inline-block; color: #667eea; text-decoration: none; font-size: 13px; margin-bottom: 30px; }}
    .back:hover {{ text-decoration: underline; }}
    h2 {{ font-size: 20px; margin-bottom: 24px; color: #e0e0e0; }}
    .card {{ background: #12121a; border-radius: 12px; padding: 16px; margin: 12px 0; border: 1px solid #1e1e2e; }}
    .card-title {{ font-size: 15px; color: #e0e0e0; line-height: 1.6; }}
    .source {{ color: #667eea; font-size: 12px; margin-top: 6px; }}
    .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }}
    .stock-code {{ color: #555; font-size: 12px; }}
    a {{ color: #667eea; text-decoration: none; }}
    .severity {{ padding: 2px 8px; border-radius: 4px; font-size: 11px; }}
    .sev-high {{ background: #e74c3c; color: #fff; }}
    .sev-mid {{ background: #e67e22; color: #fff; }}
    .sev-low {{ background: #f39c12; color: #fff; }}
    .update-time {{ color: #555; font-size: 12px; margin-top: 4px; }}
  </style>
</head>
<body>
  <a class="back" href="../stock.html">← 返回</a>
  <h2>{heading}</h2>
  {cards}
  <div style="margin-top:30px;color:#555;font-size:12px;">
    数据来源：东方财富 | 更新时间：{update_time}<br>
    超卖标准：跌幅 ≥ 6%（红色）/ 4-6%（橙色）/ 3-4%+振幅≥6%（黄色）
  </div>
</body>
</html>"""


def fetch_oversold_eastmoney():
    """从东方财富获取A股超卖数据，返回超卖股票列表"""
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    all_stocks = []

    for page in range(1, 6):
        params = {
            'pn': page, 'pz': 100, 'po': 1, 'np': 1, 'fltt': 2, 'invt': 2,
            'fid': 'f3',
            'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
            'fields': 'f2,f3,f7,f8,f12,f14'
        }
        try:
            r = requests.get(url, params=params, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://quote.eastmoney.com/'
            })
            items = r.json().get('data', {}).get('diff', [])
            if not items:
                break
            for item in items:
                code = str(item.get('f12', ''))
                name = item.get('f14', '')
                price = item.get('f2')
                change = item.get('f3')
                amplitude = item.get('f7', 0)
                turnover_rate = item.get('f8', 0)
                if price is None or change is None or price == '-':
                    continue
                if not code or not name:
                    continue
                all_stocks.append({
                    'code': code, 'name': name, 'price': float(price),
                    'change': float(change), 'amplitude': float(amplitude) if amplitude else 0,
                    'turnover_rate': float(turnover_rate) if turnover_rate else 0
                })
        except Exception as e:
            print(f"东方财富page{page}: {e}")
            break

    # 筛选超卖
    oversold = []
    for s in all_stocks:
        if s['change'] <= -6:
            s['severity'] = 'high'
            s['level'] = '严重超卖'
        elif s['change'] <= -4:
            s['severity'] = 'mid'
            s['level'] = '中度超卖'
        elif s['change'] <= -3 and s['amplitude'] >= 6:
            s['severity'] = 'low'
            s['level'] = '轻度超卖'
        else:
            continue
        oversold.append(s)

    oversold.sort(key=lambda x: x['change'])
    return oversold[:10]


def make_stock_cards(stocks):
    """生成股票卡片 HTML"""
    html = ""
    for s in stocks:
        sev = s['severity']
        cls = 'sev-high' if sev == 'high' else 'sev-mid' if sev == 'mid' else 'sev-low'
        html += f"""<div class="card">
  <div class="card-header">
    <span class="card-title">{s['name']} <span class="stock-code">({s['code']})</span></span>
    <span class="severity {cls}">{s['level']}</span>
  </div>
  <div style="color:#e74c3c;font-size:14px;">跌 {abs(s['change']):.2f}%</div>
  <div class="source">🔗 <a href="https://quote.eastmoney.com/{'sz' if s['code'].startswith(('0','3')) else 'sh'}{s['code']}.html" target="_blank">东方财富</a></div>
  <div class="update-time">最新价 {s['price']:.2f} | 振幅 {s['amplitude']:.2f}% | 换手 {s['turnover_rate']:.2f}%</div>
</div>\n"""
    return html


def main():
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    date_cn = today.strftime("%Y年%m月%d日")
    time_str = today.strftime("%H:%M")

    os.chdir(SITE_PATH)
    report = f"📊 股票超卖更新 {date_cn} {time_str}\n\n"

    stocks = fetch_oversold_eastmoney()

    if stocks:
        # 生成详情页
        cards = make_stock_cards(stocks)
        html = HTML_TEMPLATE_STOCK.format(
            title=f"A股超卖 · {date_cn}",
            heading=f"📉 A股超卖精选 · {date_cn}",
            cards=cards,
            update_time=time_str
        )
        with open(f"stock/{date_str}.html", 'w', encoding='utf-8') as f:
            f.write(html)

        # 保存JSON备份
        with open("data/oversold.json", 'w', encoding='utf-8') as f:
            json.dump([{
                'code': s['code'], 'name': s['name'], 'price': s['price'],
                'change': s['change'], 'level': s['level']
            } for s in stocks], f, ensure_ascii=False, indent=2)

        report += f"✅ 超卖: {len(stocks)}只\n"
        for s in stocks:
            report += f"• {s['name']}({s['code']}) 跌{abs(s['change']):.1f}% {s['level']}\n"

        # 更新列表页
        link = f'<a class="post" href="stock/{date_str}.html"><h3>📊 {date_cn}</h3><div class="meta">自动更新 · A股超卖</div><div class="summary">共{len(stocks)}只超卖股</div></a>'
        if update_list("stock.html", link):
            report += "\n✅ 列表页已更新"
        else:
            report += "\n⚠️ 列表页更新失败"
    else:
        report += "⚠️ 今日无超卖数据或获取失败"

    git_push(f"stock: {date_str} {time_str}")
    print(report)
    send_tg(report)


if __name__ == "__main__":
    main()
