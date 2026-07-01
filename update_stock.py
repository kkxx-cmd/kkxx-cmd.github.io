#!/usr/bin/env python3
"""
股票专区更新 - 工作日10:00运行
东方财富接口获取A股超卖 + 超买数据
"""
import os
import sys
import time
import requests
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kkxx_generate import update_list, git_push, send_tg

SITE_PATH = "/home/qgg/.openclaw/workspace/repo"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    body {{ font-family: -apple-system, sans-serif; background: #0a0a0f; color: #e0e0e0; padding: 20px; max-width: 800px; margin: 0 auto; }}
    h2 {{ font-size: 20px; margin-bottom: 16px; margin-top: 24px; }}
    .section-title.oversold {{ color: #e74c3c; }}
    .section-title.overbought {{ color: #27ae60; }}
    .back {{ color: #667eea; text-decoration: none; font-size: 14px; display: inline-block; margin-bottom: 16px; }}
    .card {{ background: #12121a; border-radius: 12px; padding: 16px; margin: 12px 0; border: 1px solid #1e1e2e; }}
    .card-title {{ font-size: 15px; color: #e0e0e0; line-height: 1.6; }}
    .source {{ color: #667eea; font-size: 12px; margin-top: 6px; }}
    .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }}
    .stock-code {{ color: #555; font-size: 12px; }}
    a {{ color: #667eea; text-decoration: none; }}
    .severity {{ padding: 2px 8px; border-radius: 4px; font-size: 11px; color: #fff; }}
    .sev-os-high {{ background: #e74c3c; }}
    .sev-os-mid {{ background: #e67e22; }}
    .sev-os-low {{ background: #f39c12; }}
    .sev-ob-high {{ background: #27ae60; }}
    .sev-ob-mid {{ background: #2ecc71; }}
    .sev-ob-low {{ background: #58d68d; color: #333; }}
    .change-down {{ color: #e74c3c; font-size: 14px; }}
    .change-up {{ color: #27ae60; font-size: 14px; }}
    .meta {{ color: #555; font-size: 12px; margin-top: 4px; }}
    .summary-text {{ color: #aaa; font-size: 13px; margin: 4px 0; }}
  </style>
</head>
<body>
  <a class="back" href="../stock.html">← 返回</a>
  <h2 class="section-title oversold">📉 超卖区域 ({oversold_count}只)</h2>
  {oversold_cards}
  <h2 class="section-title overbought">📈 超买区域 ({overbought_count}只)</h2>
  {overbought_cards}
  <div style="margin-top:30px;color:#555;font-size:12px;">
    数据来源：东方财富 | 更新时间：{update_time}<br>
    超卖 - 跌幅 ≥6%(红) / 4-6%(橙) / 3%+振幅≥6%(黄)<br>
    超买 - 涨幅 ≥6%(深绿) / 4-6%(绿) / 3%+振幅≥6%(浅绿)
  </div>
</body>
</html>"""


def fetch_eastmoney_data():
    """从东方财富获取全A股数据"""
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    # 获取所有A股数据：分涨序和跌序两次，每次取Top200
    all_stocks = []
    for sort_type in [1, -1]:  # 1=跌幅, -1=涨幅
        url = 'https://push2.eastmoney.com/api/qt/clist/get'
        params = {
            'pn': 1, 'pz': 200, 'po': sort_type, 'np': 1, 'fltt': 2, 'invt': 2,
            'fid': 'f3',
            'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
            'fields': 'f2,f3,f7,f8,f12,f14'
        }
        try:
            r = requests.get(url, params=params, timeout=20, headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://quote.eastmoney.com/'
            })
            items = r.json().get('data', {}).get('diff', []) or []
            for item in items:
                code = str(item.get('f12', ''))
                name = item.get('f14', '')
                price = item.get('f2')
                change = item.get('f3')
                amplitude = item.get('f7', 0) or 0
                turnover_rate = item.get('f8', 0) or 0
                if price is None or change is None or price == '-':
                    continue
                if not code or not name:
                    continue
                all_stocks.append({
                    'code': code, 'name': name,
                    'price': float(price), 'change': float(change),
                    'amplitude': float(amplitude), 'turnover_rate': float(turnover_rate)
                })
        except Exception as e:
            print(f'东方财富{sort_type}: {e}')
        
        import time
        time.sleep(1)
    return all_stocks


def classify_stocks(stocks):
    """分超卖/超买"""
    oversold = []
    overbought = []
    for s in stocks:
        if s['change'] <= -4:
            s['severity'] = 'os-high'; s['level'] = '严重超卖'
            oversold.append(s)
        elif s['change'] <= -2.5:
            s['severity'] = 'os-mid'; s['level'] = '中度超卖'
            oversold.append(s)
        elif s['change'] <= -2 and s['amplitude'] >= 5:
            s['severity'] = 'os-low'; s['level'] = '轻度超卖'
            oversold.append(s)
        elif s['change'] >= 4:
            s['severity'] = 'ob-high'; s['level'] = '严重超买'
            overbought.append(s)
        elif s['change'] >= 2.5:
            s['severity'] = 'ob-mid'; s['level'] = '中度超买'
            overbought.append(s)
        elif s['change'] >= 2 and s['amplitude'] >= 5:
            s['severity'] = 'ob-low'; s['level'] = '轻度超买'
            overbought.append(s)

    oversold.sort(key=lambda x: x['change'])
    overbought.sort(key=lambda x: x['change'], reverse=True)
    return oversold[:15], overbought[:15]


def make_cards(stocks, is_oversold=True):
    """生成卡片HTML"""
    html = ""
    for s in stocks:
        sev = s['severity']
        cls = f'sev-{sev}'
        change_sign = '-' if is_oversold else '+'
        cls_change = 'change-down' if is_oversold else 'change-up'
        exchange = 'sz' if s['code'].startswith(('0', '3')) else 'sh'
        link = f'https://quote.eastmoney.com/{exchange}{s["code"]}.html'
        html += f'''<div class="card">
  <div class="card-header">
    <span class="card-title">{s['name']} <span class="stock-code">({s['code']})</span></span>
    <span class="severity {cls}">{s['level']}</span>
  </div>
  <div class="{cls_change}">{change_sign} {abs(s['change']):.2f}%</div>
  <div class="source">🔗 <a href="{link}" target="_blank">东方财富</a></div>
  <div class="meta">最新价 {s['price']:.2f} | 振幅 {s['amplitude']:.2f}% | 换手 {s['turnover_rate']:.2f}%</div>
</div>\n'''
    return html if html else '<p style="color:#555;">今日暂无数据</p>'


def main():
    os.chdir(SITE_PATH)
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    date_cn = today.strftime("%Y年%m月%d日")
    time_str = today.strftime("%H:%M")

    report = f"📊 股票超卖/超买更新 {date_cn} {time_str}\n\n"

    stocks = fetch_eastmoney_data()
    oversold, overbought = classify_stocks(stocks)

    oversold_cards = make_cards(oversold, is_oversold=True)
    overbought_cards = make_cards(overbought, is_oversold=False)

    title = f"A股超买/超卖 · {date_cn}"
    html = HTML_TEMPLATE.format(
        title=title,
        oversold_count=len(oversold),
        overbought_count=len(overbought),
        oversold_cards=oversold_cards,
        overbought_cards=overbought_cards,
        update_time=time_str
    )

    with open(f"stock/{date_str}.html", 'w', encoding='utf-8') as f:
        f.write(html)

    with open("data/stock-data.json", 'w', encoding='utf-8') as f:
        json.dump({
            'date': date_str,
            'oversold': [{'code': s['code'], 'name': s['name'], 'change': s['change'], 'level': s['level']} for s in oversold],
            'overbought': [{'code': s['code'], 'name': s['name'], 'change': s['change'], 'level': s['level']} for s in overbought]
        }, f, ensure_ascii=False, indent=2)

    report += f"超卖: {len(oversold)}只 | 超买: {len(overbought)}只\n"
    for s in oversold[:5]:
        report += f"• {s['name']}({s['code']}) 跌{abs(s['change']):.1f}%\n"
    for s in overbought[:5]:
        report += f"• {s['name']}({s['code']}) 涨{s['change']:.1f}%\n"

    link = f'<a class="post" href="stock/{date_str}.html"><h3>📊 {date_cn}</h3><div class="meta">自动更新 · 超卖+超买</div><div class="summary-text">超卖{len(oversold)}只 · 超买{len(overbought)}只</div></a>'
    update_list("stock.html", link)

    git_push(f"stock: {date_str} {time_str}")
    print(report)
    send_tg(report)


if __name__ == "__main__":
    main()
