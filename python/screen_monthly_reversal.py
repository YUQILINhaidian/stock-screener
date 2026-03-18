#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
月线反转6.5选股策略
根据陶博士改进版的7条标准筛选股票

参考：https://mp.weixin.qq.com/s/JnTeY7T0rPcWXE3NeHRb7Q
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

# 数据库路径
DB_PATH = Path.home() / '.vntrader' / 'database.db'
OUTPUT_DIR = Path.home() / '.vntrader' / 'screen_results'
NAMES_CACHE = Path.home() / '.vntrader' / 'stock_names.json'

def load_stock_names():
    """加载股票名称缓存"""
    if NAMES_CACHE.exists():
        with open(NAMES_CACHE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_stock_names(names):
    """保存股票名称缓存"""
    with open(NAMES_CACHE, 'w', encoding='utf-8') as f:
        json.dump(names, f, ensure_ascii=False, indent=2)

def get_stock_name(symbol, names_cache):
    """获取股票名称"""
    key = f"股票.{symbol}"
    if key in names_cache:
        return names_cache[key]
    return symbol

def get_all_stocks(conn):
    """获取所有A股股票代码"""
    cursor = conn.cursor()
    query = """
        SELECT DISTINCT symbol, exchange 
        FROM dbbardata 
        WHERE exchange IN ('SSE', 'SZSE') 
        AND interval = 'd'
        AND symbol GLOB '[0-9][0-9][0-9][0-9][0-9][0-9]'
    """
    cursor.execute(query)
    return cursor.fetchall()

def get_stock_data(conn, symbol, exchange, days=300):
    """获取股票日线数据"""
    try:
        query = """
            SELECT datetime as trade_date, 
                   open_price as open, 
                   high_price as high, 
                   low_price as low, 
                   close_price as close, 
                   volume, 
                   turnover
            FROM dbbardata
            WHERE symbol = ? AND exchange = ? AND interval = 'd'
            ORDER BY datetime DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(symbol, exchange, days))
        if len(df) < 250:
            return None
        df = df.sort_values('trade_date').reset_index(drop=True)
        return df
    except:
        return None

def check_monthly_reversal(df):
    """
    检查股票是否符合月线反转条件
    
    返回: (is_reversal, details)
    """
    if len(df) < 250:
        return False, {}
    
    df = df.copy()
    
    # 计算均线
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma50'] = df['close'].rolling(window=50).mean()
    df['ma120'] = df['close'].rolling(window=120).mean()
    df['ma200'] = df['close'].rolling(window=200).mean()
    df['ma250'] = df['close'].rolling(window=250).mean()
    
    # 计算高低点
    df['llv_20'] = df['low'].rolling(window=20).min()
    df['llv_30'] = df['low'].rolling(window=30).min()
    df['llv_50'] = df['low'].rolling(window=50).min()
    df['llv_120'] = df['low'].rolling(window=120).min()
    df['llv_200'] = df['low'].rolling(window=200).min()
    df['hhv_5'] = df['high'].rolling(window=5).max()
    df['hhv_10'] = df['high'].rolling(window=10).max()
    df['hhv_50'] = df['high'].rolling(window=50).max()
    df['hhv_70'] = df['high'].rolling(window=70).max()
    df['hhv_80'] = df['high'].rolling(window=80).max()
    df['hhv_120'] = df['high'].rolling(window=120).max()
    df['hhv_250'] = df['high'].rolling(window=250).max()
    
    # 获取最新数据
    latest = df.iloc[-1]
    close = latest['close']
    high = latest['high']
    
    details = {}
    
    # 条件1: RPS强度（简化处理）
    # 实际应该计算全市场排名，这里简化为True
    details['fyx1_rps'] = True
    
    # 条件2: 结构紧凑
    llv_50 = df['llv_50'].iloc[-1]
    llv_200 = df['llv_200'].iloc[-1]
    llv_30 = df['llv_30'].iloc[-1]
    llv_120 = df['llv_120'].iloc[-1]
    llv_20 = df['llv_20'].iloc[-1]
    hhv_70 = df['hhv_70'].iloc[-1]
    
    fyx130 = True  # 简化RPS条件
    fyx13 = fyx130 and close >= hhv_70  # 创70日新高
    
    fyx21 = llv_50 > llv_200 and fyx13
    fyx22 = llv_30 > llv_120 and fyx13
    fyx23 = llv_20 > llv_50
    
    details['fyx2_compact'] = fyx21 or fyx22 or fyx23
    details['fyx21'] = fyx21
    details['fyx22'] = fyx22
    details['fyx23'] = fyx23
    details['fyx13'] = fyx13
    
    # 条件3: 创新高
    hhv_80 = df['hhv_80'].iloc[-1]
    hhv_50 = df['hhv_50'].iloc[-1]
    
    # 10天内是否创过80日新高
    nh80_recent = (df['high'].iloc[-10:] >= df['hhv_80'].iloc[-10:].shift(1)).any()
    fyx31 = nh80_recent
    fyx32 = (close >= df['close'].iloc[-50:].max() or high >= hhv_50) and fyx130
    
    details['fyx3_new_high'] = fyx31 or fyx32
    details['fyx31'] = fyx31
    details['fyx32'] = fyx32
    
    # 条件4: 均线支撑
    ma20 = latest['ma20']
    ma120 = latest['ma120']
    ma200 = latest['ma200']
    
    details['fyx4_ma_support'] = close > ma20 and close > ma200 and ma120 / ma200 > 0.9
    
    # 条件5: 均线靠近（45天内的情况）
    if len(df) >= 45:
        df_45 = df.iloc[-45:]
        ma200_45 = df_45['ma200']
        close_45 = df_45['close']
        low_45 = df_45['low']
        
        # 站上200天线的天数
        above_200_count = (close_45 > ma200_45).sum()
        # 低于200天线的天数
        below_200_low = (low_45 < ma200_45).sum()
        
        # 250日线
        ma250_45 = df_45['ma250']
        below_250_low = (low_45 < ma250_45).sum()
        above_250_count = (close_45 > ma250_45).sum()
        
        fyx51 = above_200_count >= 2 and above_200_count < 45
        fyx52 = below_200_low > 0 and above_200_count > 2
        fyx53 = below_250_low > 0 and above_250_count > 2
        
        details['fyx5_ma_near'] = fyx51 or fyx52 or fyx53
        details['above_200_days'] = above_200_count
    else:
        details['fyx5_ma_near'] = True  # 数据不足时默认通过
    
    # 条件6: 均线趋势
    if len(df) >= 15:
        ma120_now = df['ma120'].iloc[-1]
        ma120_10 = df['ma120'].iloc[-11]
        ma120_15 = df['ma120'].iloc[-16]
        ma200_now = df['ma200'].iloc[-1]
        ma200_10 = df['ma200'].iloc[-11]
        ma200_15 = df['ma200'].iloc[-16]
        
        fyx601 = ma120_now >= ma120_10 or ma200_now >= ma200_10
        fyx602 = ma120_now >= ma120_10 and ma200_now >= ma200_10
        fyx603 = ma120_now > ma200_now and fyx601
        
        hhv_30 = df['high'].iloc[-30:].max()
        llv_120 = df['low'].iloc[-120:].min()
        ratio = hhv_30 / llv_120 if llv_120 > 0 else 2
        
        fyx61 = ratio < 1.50 and fyx601
        fyx62 = ratio < 1.55 and fyx602
        fyx63 = ratio < 1.65 and fyx603 and fyx13
        
        details['fyx6_ma_trend'] = fyx61 or fyx62 or fyx63
        details['ratio_30_120'] = ratio
    else:
        details['fyx6_ma_trend'] = True
    
    # 条件7: 价格位置
    hhv_5 = df['hhv_5'].iloc[-1]
    hhv_120 = df['hhv_120'].iloc[-1]
    hhv_10 = df['hhv_10'].iloc[-1]
    
    fyx71 = hhv_5 / hhv_120 > 0.85 if hhv_120 > 0 else False
    fyx72 = hhv_5 / hhv_120 > 0.80 and fyx13 if hhv_120 > 0 else False
    fyx73 = close / hhv_10 > 0.90 if hhv_10 > 0 else False
    
    details['fyx7_position'] = (fyx71 or fyx72) and fyx73
    details['position_ratio'] = close / hhv_10 if hhv_10 > 0 else 0
    
    # 最终判断
    is_reversal = (
        details['fyx2_compact'] and
        details['fyx3_new_high'] and
        details['fyx4_ma_support'] and
        details['fyx5_ma_near'] and
        details['fyx6_ma_trend'] and
        details['fyx7_position']
    )
    
    return is_reversal, details

def screen_monthly_reversal():
    """执行月线反转筛选"""
    print("=" * 80)
    print("月线反转6.5策略筛选")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    names_cache = load_stock_names()
    
    stocks = get_all_stocks(conn)
    print(f"共找到 {len(stocks)} 只股票")
    
    results = []
    
    for i, (symbol, exchange) in enumerate(stocks):
        if (i + 1) % 500 == 0:
            print(f"处理进度: {i + 1}/{len(stocks)}")
        
        df = get_stock_data(conn, symbol, exchange)
        if df is None:
            continue
        
        is_reversal, details = check_monthly_reversal(df)
        
        if is_reversal:
            name = get_stock_name(symbol, names_cache)
            latest = df.iloc[-1]
            
            results.append({
                'symbol': symbol,
                'name': name,
                'exchange': exchange,
                'close': latest['close'],
                'high_250': df['high'].iloc[-250:].max(),
                'volume': latest['volume'],
                'turnover': latest.get('turnover', 0),
                'ratio_30_120': details.get('ratio_30_120', 0),
                'trade_date': latest['trade_date'],
                'details': details
            })
    
    save_stock_names(names_cache)
    conn.close()
    
    print(f"\n筛选结果: 共 {len(results)} 只股票符合月线反转条件")
    
    if results:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values('ratio_30_120')
        
        date_str = datetime.now().strftime('%Y%m%d')
        output_file = OUTPUT_DIR / f'monthly_reversal_{date_str}.csv'
        
        output_cols = ['symbol', 'name', 'exchange', 'close', 'high_250', 
                       'ratio_30_120', 'volume', 'turnover', 'trade_date']
        df_results[output_cols].to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n结果已保存到: {output_file}")
        
        print("\n" + "=" * 80)
        print("Top 20 股票:")
        print("=" * 80)
        print(f"{'代码':<8} {'名称':<12} {'收盘价':>8} {'30/120比':>8} {'成交额':>12}")
        print("-" * 60)
        
        for _, row in df_results.head(20).iterrows():
            print(f"{row['symbol']:<8} {row['name']:<12} {row['close']:>8.2f} "
                  f"{row['ratio_30_120']:>7.2f} {row['turnover']:>12.0f}")
        
        return df_results
    else:
        print("\n未找到符合条件的股票")
        return pd.DataFrame()

if __name__ == '__main__':
    screen_monthly_reversal()
