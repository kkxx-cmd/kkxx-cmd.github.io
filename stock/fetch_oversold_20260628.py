#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股超卖股票筛选脚本
生成日期：2026-06-28
"""

import akshare as ak
import pandas as pd
import os
import traceback
from datetime import datetime, timedelta

OUTPUT_FILE = "/home/qgg/site/stock/2026-06-28.html"
LOG_FILE = "/home/qgg/site/stock/2026-06-28.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def safe_get_spot():
    """获取全市场A股实时行情"""
    log("开始获取全市场A股实时行情...")
    df = ak.stock_zh_a_spot_em()
    log(f"获取到 {len(df)} 条股票数据")
    return df

def get_60day_decline(code, name):
    """获取60日累计跌幅"""
    try:
        end = datetime.today()
        start = end - timedelta(days=120)  # 多取一些天数确保有足够数据
        
        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            adjust="qfq"
        )
        
        if df is None or len(df) < 60:
            return None
        
        # 取最近60个交易日
        df = df.tail(60).reset_index(drop=True)
        
        # 收盘价列名可能是"收盘"或"close"
        close_col = None
        for col in ["收盘", "close", "收盘价"]:
            if col in df.columns:
                close_col = col
                break
        
        if close_col is None:
            log(f"[{code}] 找不到收盘价列: {df.columns.tolist()}")
            return None
        
        start_price = float(df.iloc[0][close_col])
        end_price = float(df.iloc[-1][close_col])
        
        if start_price <= 0:
            return None
        
        decline_pct = (end_price - start_price) / start_price * 100
        return round(decline_pct, 2)
    except Exception as e:
        log(f"[{code}] 获取历史数据失败: {e}")
        return None

def generate_html(stocks, date_str):
    """生成HTML文件"""
    date_display = f"{date_str[:4]}年{date_str[5:7]}月{date_str[8:]}日"
    
    rows = ""
    for s in stocks:
        code = s["code"]
        name = s["name"]
        price = s["price"]
        change_pct = s["change_pct"]
        decline_60d = s["decline_60d"]
        turnover = s["turnover"]
        amount = s["amount"]
        
        # 判断是否ST
        name_html = f'{name}<span class="tag-st">ST</span>' if s.get("is_st") else name
        
        # 涨跌颜色：下跌显示红色(up)，上涨显示绿色(dn)
        # change_pct为负表示下跌，为正表示上涨
        if change_pct < 0:
            change_class = "up"
            change_sign = ""
        else:
            change_class = "dn"
            change_sign = "+"
        
        # 60日跌幅始终红色（表示跌幅）
        rows += f"""      <tr>
        <td>{code}</td>
        <td>{name_html}</td>
        <td>{price}</td>
        <td class="{change_class}">{change_sign}{change_pct:.2f}%</td>
        <td class="up">{decline_60d:.2f}%</td>
        <td>{turnover:.2f}%</td>
        <td>{amount:.2f}</td>
      </tr>
"""
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>📉 A股超卖精选 · {date_display}</title>
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:-apple-system,sans-serif;background:#0a0a0f;color:#e0e0e0;padding:20px;max-width:800px;margin:0 auto}}
    .back{{color:#667eea;text-decoration:none;font-size:14px;display:inline-block;margin-bottom:20px}}
    h1{{background:linear-gradient(90deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:6px;font-size:22px}}
    .subtitle{{color:#555;font-size:13px;margin-bottom:24px}}
    .warning{{background:#1a1206;border:1px solid #5a400a;border-radius:8px;padding:12px 16px;margin-bottom:24px;font-size:13px;color:#f0a500;line-height:1.7}}
    table{{width:100%;border-collapse:collapse;font-size:13px}}
    th{{text-align:left;padding:10px 8px;background:#12121a;color:#667eea;border-bottom:1px solid #1e1e2e;font-weight:600;font-size:11px;text-transform:uppercase}}
    td{{padding:10px 8px;border-bottom:1px solid #1a1a28;color:#ccc}}
    tr:hover td{{background:#12121a}}
    .up{{color:#ff4757}}
    .dn{{color:#2ed573}}
    .tag-st{{background:#ff4757;color:#fff;font-size:10px;padding:1px 5px;border-radius:3px;margin-left:4px}}
    .note{{color:#555;font-size:12px;margin-top:24px;line-height:1.8}}
    footer{{margin-top:40px;color:#333;font-size:12px;text-align:center}}
    footer a{{color:#555;text-decoration:none}}
  </style>
</head>
<body>
  <a class="back" href="../stock.html">← 返回股票专区</a>
  <h1>📉 A股超卖精选 · {date_display}</h1>
  <div class="subtitle">基于60日累计跌幅筛选，成交量 > 3000万 · 共 {len(stocks)} 只</div>
  <div class="warning">⚠️ 数据仅供参考，不构成投资建议。市场有风险，投资需谨慎。</div>
  <table>
    <thead>
      <tr>
        <th>代码</th>
        <th>名称</th>
        <th>最新价</th>
        <th>今日涨跌</th>
        <th>60日跌幅</th>
        <th>换手率</th>
        <th>成交额(亿)</th>
      </tr>
    </thead>
    <tbody>
{rows}    </tbody>
  </table>
  <div class="note">
    筛选条件：60日累计跌幅超过30%、日成交额超过3000万、换手率超过0.3%<br>
    颜色说明：<span class="up">红色</span> = 今日下跌（价格下行）；<span class="dn">绿色</span> = 今日上涨（反弹迹象）
  </div>
  <footer>
    <a href="../stock.html">← 返回股票专区</a> · 数据来源：AkShare · 生成于 {datetime.now().strftime("%Y-%m-%d %H:%M")}
  </footer>
</body>
</html>'''
    
    return html

def main():
    log("=" * 60)
    log("开始执行A股超卖筛选任务")
    
    # 清空日志
    open(LOG_FILE, "w", encoding="utf-8").close()
    
    date_str = "2026-06-28"
    
    try:
        # 1. 获取全市场A股实时行情
        df_spot = safe_get_spot()
        
        # 2. 找出需要的列
        col_map = {}
        for col in df_spot.columns:
            col_lower = col.lower()
            if "代码" in col or col_lower == "code":
                col_map["code"] = col
            elif "名称" in col or col_lower == "name":
                col_map["name"] = col
            elif "最新价" in col or "现价" in col or col_lower == "price":
                col_map["price"] = col
            elif "涨跌幅" in col or "涨跌额" in col:
                col_map["change_pct"] = col
            elif "换手率" in col:
                col_map["turnover"] = col
            elif "成交额" in col or "成交额" in col:
                col_map["amount"] = col
        
        log(f"列映射: {col_map}")
        
        # 3. 基础筛选：成交额>3000万，换手率>0.3%
        # 成交额列单位通常是元，需转换为亿
        amount_col = col_map.get("amount", "")
        turnover_col = col_map.get("turnover", "")
        
        # 预筛选
        candidates = []
        for idx, row in df_spot.iterrows():
            try:
                code = str(row.get(col_map.get("code", ""), ""))
                name = str(row.get(col_map.get("name", ""), ""))
                price_val = row.get(col_map.get("price", ""), 0)
                change_pct_val = row.get(col_map.get("change_pct", ""), 0)
                turnover_val = row.get(turnover_col, 0)
                amount_val = row.get(amount_col, 0)
                
                if not code or len(code) != 6:
                    continue
                
                # 基础数值校验
                try:
                    price = float(price_val)
                    change_pct = float(change_pct_val)
                    turnover = float(turnover_val)
                    amount = float(amount_val)
                except (ValueError, TypeError):
                    continue
                
                if price <= 0:
                    continue
                
                # 成交额转亿：/ 100000000
                amount_yi = amount / 100000000
                
                # 预筛选条件：成交额>3000万(0.3亿)，换手率>0.3%
                if amount_yi < 0.3 or turnover < 0.3:
                    continue
                
                # 判断是否ST
                is_st = "ST" in name or "*ST" in name
                
                candidates.append({
                    "code": code,
                    "name": name,
                    "price": price,
                    "change_pct": change_pct,
                    "turnover": turnover,
                    "amount": amount_yi,
                    "is_st": is_st
                })
                
            except Exception as e:
                log(f"行处理错误: {e}")
                continue
        
        log(f"预筛选候选股票: {len(candidates)} 只")
        
        # 4. 对候选股票获取60日历史数据计算跌幅
        results = []
        total = len(candidates)
        
        for i, c in enumerate(candidates):
            log(f"[{i+1}/{total}] 处理 {c['code']} {c['name']}...")
            
            decline = get_60day_decline(c["code"], c["name"])
            
            if decline is not None and decline <= -30:
                c["decline_60d"] = decline
                results.append(c)
                log(f"  → 60日跌幅 {decline:.2f}%，符合条件！")
            
            # 避免请求过快
            import time
            time.sleep(0.3)
        
        log(f"符合60日跌幅>30%的股票: {len(results)} 只")
        
        # 5. 按60日跌幅降序排列，取前20
        results.sort(key=lambda x: x["decline_60d"])
        results = results[:20]
        
        log(f"最终筛选结果: {len(results)} 只")
        
        # 6. 生成HTML
        html_content = generate_html(results, date_str)
        
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        log(f"HTML文件已生成: {OUTPUT_FILE}")
        
        # 打印结果摘要
        print("\n筛选结果：")
        print(f"{'代码':<8} {'名称':<10} {'最新价':<8} {'今日涨跌':<10} {'60日跌幅':<10} {'换手率':<8} {'成交额(亿)':<10}")
        print("-" * 80)
        for s in results:
            print(f"{s['code']:<8} {s['name']:<10} {s['price']:<8.2f} {s['change_pct']:<+10.2f} {s['decline_60d']:<10.2f} {s['turnover']:<8.2f} {s['amount']:<10.2f}")
        
    except Exception as e:
        log(f"执行出错: {e}")
        log(traceback.format_exc())
        raise

if __name__ == "__main__":
    main()