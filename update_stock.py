#!/usr/bin/env python3
"""
股票专区更新 - 工作日10:00运行
东方财富 + 新浪财经 双数据源，获取A股超卖 + 超买数据
"""
import os
import sys
import time
import requests
import json
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kkxx_generate import update_list, git_push, send_tg, HTML_TEMPLATE, make_cards

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


def fetch_eastmoney():
    """从东方财富获取A股数据"""
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params_base = {
        'np': 1, 'fltt': 2, 'invt': 2, 'fid': 'f3',
        'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
        'fields': 'f2,f3,f7,f8,f12,f14'
    }
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://quote.eastmoney.com/'
    })
    all_stocks = []
    for pn in [1, 2]:
        params = dict(params_base)
        params['pn'] = pn
        params['pz'] = 100
        params['po'] = 1
        try:
            r = s.get(url, params=params, timeout=20)
            if r.status_code != 200:
                break
            data = r.json()
            if data.get('rc') != 0:
                break
            items = data.get('data', {}).get('diff', []) or []
            if not items:
                break
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
            print(f"EastMoney pn={pn}: {e}")
            break
        time.sleep(0.5)
    return all_stocks


def fetch_sina():
    """从新浪财经获取A股数据（降级方案）"""
    url = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.sina.com.cn/'
    })
    all_stocks = []
    for page in range(1, 4):
        try:
            r = s.get(url, params={
                'page': page, 'num': 200, 'sort': 'changepercent', 'asc': 0, 'node': 'hs_a'
            }, timeout=20)
            data = r.json()
            if not data:
                break
            for item in data:
                code = str(item.get('code', ''))
                name = item.get('name', '')
                price = item.get('trade')
                change = item.get('changepercent')
                turnover = item.get('turnoverratio', 0) or 0
                high = item.get('high', 0) or 0
                low = item.get('low', 0) or 0
                settlement = item.get('settlement', 0) or 0
                if price is None or change is None:
                    continue
                if not code or not name:
                    continue
                amplitude = 0
                if settlement > 0:
                    amplitude = (high - low) / settlement * 100
                all_stocks.append({
                    'code': code, 'name': name,
                    'price': float(price), 'change': float(change),
                    'amplitude': float(amplitude), 'turnover_rate': float(turnover)
                })
        except Exception as e:
            print(f"Sina page{page}: {e}")
            break
        time.sleep(0.5)
    return all_stocks


def fetch_stock_data():
    """获取股票数据，东方财富优先，失败降级新浪"""
    stocks = fetch_eastmoney()
    source_name = "东方财富"
    if len(stocks) < 50:
        print(f"东方财富仅{len(stocks)}条，降级到新浪财经...")
        stocks = fetch_sina()
        source_name = "新浪财经"
    if len(stocks) < 50:
        print(f"新浪也仅{len(stocks)}条，尝试合并...")
        eastmoney = fetch_eastmoney()
        sina = fetch_sina()
        seen = set()
        merged = []
        for s in eastmoney + sina:
            if s['code'] not in seen:
                seen.add(s['code'])
                merged.append(s)
        stocks = merged
        source_name = "东方财富+新浪"
    return stocks, source_name


def classify_stocks(stocks):
    """分超卖/超买"""
    oversold = []
    overbought = []
    for s in stocks:
        if s['change'] <= -4:
            s['severity'] = 'os-high'; s['level'] = '严重超卖'
            oversold.append(s)
        elif s['change'] <= -2:
            s['severity'] = 'os-mid'; s['level'] = '中度超卖'
            oversold.append(s)
        elif s['change'] <= -1 and s['amplitude'] >= 4:
            s['severity'] = 'os-low'; s['level'] = '轻度超卖'
            oversold.append(s)
        elif s['change'] >= 4:
            s['severity'] = 'ob-high'; s['level'] = '严重超买'
            overbought.append(s)
        elif s['change'] >= 2:
            s['severity'] = 'ob-mid'; s['level'] = '中度超买'
            overbought.append(s)
        elif s['change'] >= 1 and s['amplitude'] >= 4:
            s['severity'] = 'ob-low'; s['level'] = '轻度超买'
            overbought.append(s)

    oversold.sort(key=lambda x: x['change'])
    overbought.sort(key=lambda x: x['change'], reverse=True)
    return oversold[:30], overbought[:30]


def make_stock_cards(stocks, is_oversold=True):
    """生成股票卡片HTML"""
    html = ""
    sev_high, sev_mid, sev_low = ('os-high','os-mid','os-low') if is_oversold else ('ob-high','ob-mid','ob-low')
    for s in stocks:
        if s['severity'] == sev_high:
            cls = sev_high
        elif s['severity'] == sev_mid:
            cls = sev_mid
        else:
            cls = sev_low
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

    stocks, source_name = fetch_stock_data()
    oversold, overbought = classify_stocks(stocks)

    if len(oversold) == 0 and len(overbought) == 0:
        report += "⚠️ 今日未筛选到超买/超卖数据\n"

    oversold_cards = make_stock_cards(oversold, is_oversold=True)
    overbought_cards = make_stock_cards(overbought, is_oversold=False)

    title = f"A股超买/超卖 · {date_cn}"
    html = f'''<!DOCTYPE html>
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
  <h2 class="section-title oversold">📉 超卖区域 ({len(oversold)}只)</h2>
  {oversold_cards}
  <h2 class="section-title overbought">📈 超买区域 ({len(overbought)}只)</h2>
  {overbought_cards}
  <div style="margin-top:30px;color:#555;font-size:12px;">
    数据来源：{source_name} | 更新时间：{time_str}<br>
    超卖 - 跌幅 ≥4%(红) / 2-4%(橙) / 1%+振幅≥4%(黄)<br>
    超买 - 涨幅 ≥4%(深绿) / 2-4%(绿) / 1%+振幅≥4%(浅绿)
  </div>
</body>
</html>'''

    with open(f"stock/{date_str}.html", 'w', encoding='utf-8') as f:
        f.write(html)

    with open("data/stock-data.json", 'w', encoding='utf-8') as f:
        json.dump({
            'date': date_str,
            'source': source_name,
            'oversold': [{'code': s['code'], 'name': s['name'], 'change': s['change'], 'level': s['level']} for s in oversold],
            'overbought': [{'code': s['code'], 'name': s['name'], 'change': s['change'], 'level': s['level']} for s in overbought]
        }, f, ensure_ascii=False, indent=2)

    report += f"数据源: {source_name}\n"
    report += f"超卖: {len(oversold)}只 | 超买: {len(overbought)}只\n"
    for s in oversold[:5]:
        report += f"• {s['name']}({s['code']}) 跌{abs(s['change']):.1f}%\n"
    for s in overbought[:5]:
        report += f"• {s['name']}({s['code']}) 涨{s['change']:.1f}%\n"

    link = f'<a class="post" href="stock/{date_str}.html"><h3>📊 {date_cn}</h3><div class="meta">自动更新 · 超卖+超买 · {source_name}</div><div class="summary-text">超卖{len(oversold)}只 · 超买{len(overbought)}只</div></a>'
    update_list("stock.html", link)

    ok, err = git_push(f"stock: {date_str} {time_str}")
    if not ok:
        report += f"\n⚠️ Git push 失败: {err}"
        send_alert("股票更新", f"Git push 失败: {err}")
    else:
        report += "\n✅ Git push 成功"

    print(report)
    send_tg(report)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        tb = traceback.format_exc()
        send_alert("股票更新", f"未捕获异常: {e}\n{tb}")
        sys.exit(1)
