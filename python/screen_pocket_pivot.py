#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
口袋支点选股策略
根据陶博士改进版的9条标准筛选股票

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
    stocks = []
    cursor = conn.cursor()
    
    # 查询所有A股股票（SSE和SZSE交易所）
    query = """
        SELECT DISTINCT symbol, exchange 
        FROM dbbardata 
        WHERE exchange IN ('SSE', 'SZSE') 
        AND interval = 'd'
        AND symbol GLOB '[0-9][0-9][0-9][0-9][0-9][0-9]'
    """
    cursor.execute(query)
    stocks = cursor.fetchall()
    
    return stocks

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
    except Exception as e:
        return None

def check_pocket_pivot(df):
    """
    检查股票是否符合口袋支点条件
    
    返回: (is_pocket_pivot, details)
    """
    if len(df) < 250:
        return False, {}
    
    # 获取最新数据
    latest = df.iloc[-1]
    close = latest['close']
    high = latest['high']
    low = latest['low']
    volume = latest['volume']
    turnover = latest.get('turnover', volume * close)
    prev_close = df['close'].iloc[-2]
    
    # 计算均线
    df = df.copy()
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['ma50'] = df['close'].rolling(window=50).mean()
    df['ma90'] = df['close'].rolling(window=90).mean()
    df['ma100'] = df['close'].rolling(window=100).mean()
    df['ma120'] = df['close'].rolling(window=120).mean()
    df['ma250'] = df['close'].rolling(window=250).mean()
    
    # 计算高低点
    df['hhv_90'] = df['high'].rolling(window=90).max()
    df['hhv_100'] = df['high'].rolling(window=100).max()
    df['hhv_120'] = df['high'].rolling(window=120).max()
    df['hhv_250'] = df['high'].rolling(window=250).max()
    df['llv_15'] = df['low'].rolling(window=15).min()
    df['llv_50'] = df['low'].rolling(window=50).min()
    df['llv_100'] = df['low'].rolling(window=100).min()
    df['llv_40'] = df['low'].rolling(window=40).min()
    df['llv_120'] = df['low'].rolling(window=120).min()
    
    # 成交量和成交额均线
    df['amo_ma10'] = df['turnover'].rolling(window=10).mean()
    
    details = {}
    
    # 条件1: RPS强度（简化处理，使用估算值）
    details['kd1_rps'] = True  # 简化处理，默认通过
    
    # 条件2: 成交量放大
    amo_10 = df['turnover'].iloc[-10:].values
    amo_latest = df['turnover'].iloc[-1]
    amo_ma10 = df['amo_ma10'].iloc[-1]
    
    fkd21 = amo_latest == amo_10.max() and amo_latest > 0  # 创10日最高成交金额
    fkd22 = close / prev_close > 1.099  # 当日涨幅>9.9%
    fkd23 = amo_ma10 > 0 and amo_latest / amo_ma10 > 2  # 成交金额是10天平均的2倍
    
    details['kd2_volume'] = fkd21 or fkd22 or fkd23
    details['fkd21'] = fkd21
    details['fkd22'] = fkd22
    details['fkd23'] = fkd23
    
    # 条件3: 均线突破
    ma90 = df['ma90'].iloc[-1]
    ma90_prev5 = df['ma90'].iloc[-6] if len(df) > 5 else ma90
    ma100 = df['ma100'].iloc[-1]
    ma100_prev5 = df['ma100'].iloc[-6] if len(df) > 5 else ma100
    ma120 = df['ma120'].iloc[-1]
    ma120_prev2 = df['ma120'].iloc[-3] if len(df) > 2 else ma120
    
    hhv_90 = df['hhv_90'].iloc[-1]
    hhv_100 = df['hhv_100'].iloc[-1]
    
    fkd31 = close > ma90 and ma90 >= ma90_prev5 and high >= hhv_90
    fkd32 = close > ma100 and ma100 >= ma100_prev5 and high >= hhv_100 and ma90 >= ma90_prev5
    fkd33 = close > ma120 and ma120 >= ma120_prev2
    
    details['kd3_ma_breakout'] = fkd31 or fkd32 or fkd33
    details['fkd31'] = fkd31
    details['fkd32'] = fkd32
    details['fkd33'] = fkd33
    
    # 条件4: 结构紧凑
    llv_15 = df['llv_15'].iloc[-1]
    llv_50 = df['llv_50'].iloc[-1]
    hhv_250 = df['hhv_250'].iloc[-1]
    
    fkd250 = high >= hhv_250
    
    details['kd4_structure'] = llv_15 > llv_50 * 0.995 or fkd250
    details['fkd250'] = fkd250
    
    # 条件5: 调整幅度限制
    hhv_120 = df['hhv_120'].iloc[-1]
    llv_40 = df['llv_40'].iloc[-1]
    llv_120 = df['llv_120'].iloc[-1]
    
    fkd51 = hhv_120 > 0 and llv_40 / hhv_120 > 0.5
    fkd5 = fkd51 or fkd250
    
    # 计算120日内最高点到最低点的幅度
    h120_idx = df['high'].iloc[-120:].idxmax()
    l120_after_h = df['low'].iloc[h120_idx:].min() if h120_idx < len(df) else llv_120
    l120_ratio = l120_after_h / hhv_120 if hhv_120 > 0 else 0
    
    details['kd5_drawdown'] = l120_ratio > 0.54 and fkd5
    details['drawdown_ratio'] = l120_ratio
    
    # 条件6: 结构紧凑条件
    llv_100 = df['llv_100'].iloc[-1]
    
    fkd41 = fkd250 or llv_15 > llv_50
    fkd42 = abs(llv_15 - llv_50) < 0.01 and llv_15 > llv_100 and high / hhv_250 > 0.88
    hhv_40 = df['high'].iloc[-40:].max()
    fkd43 = (abs(llv_15 - llv_50) < 0.01 and llv_15 > llv_100 and 
             high / hhv_250 > 0.75 and high >= hhv_40 and close / prev_close > 1.07)
    
    details['kd6_compact'] = fkd41 or fkd42 or fkd43
    
    # 条件7: 涨幅要求
    details['kd7_price_change'] = close / prev_close >= 1.05
    details['price_change'] = close / prev_close - 1
    
    # 条件8: 换手率稳定（简化处理）
    details['kd8_turnover'] = True  # 简化处理
    
    # 条件9: 价格偏离限制
    ma50_prev = df['ma50'].iloc[-2]
    ma10_prev = df['ma10'].iloc[-2]
    low_prev = df['low'].iloc[-2]
    
    details['kd9_deviation'] = low_prev <= ma50_prev * 1.24 or low_prev <= ma10_prev * 1.03
    
    # 最终判断
    is_pocket_pivot = (
        details['kd2_volume'] and
        details['kd3_ma_breakout'] and
        details['kd4_structure'] and
        details['kd5_drawdown'] and
        details['kd6_compact'] and
        details['kd7_price_change'] and
        details['kd9_deviation']
    )
    
    return is_pocket_pivot, details

def screen_pocket_pivot():
    """执行口袋支点筛选"""
    print("=" * 80)
    print("口袋支点策略筛选")
    print("=" * 80)
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    
    # 加载股票名称缓存
    names_cache = load_stock_names()
    
    # 获取所有股票
    stocks = get_all_stocks(conn)
    print(f"共找到 {len(stocks)} 只股票")
    
    # 筛选结果
    results = []
    
    for i, (symbol, exchange) in enumerate(stocks):
        if (i + 1) % 500 == 0:
            print(f"处理进度: {i + 1}/{len(stocks)}")
        
        # 获取数据
        df = get_stock_data(conn, symbol, exchange)
        if df is None:
            continue
        
        # 检查口袋支点条件
        is_pocket_pivot, details = check_pocket_pivot(df)
        
        if is_pocket_pivot:
            # 获取股票名称
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
                'price_change': details.get('price_change', 0),
                'trade_date': latest['trade_date'],
                'details': details
            })
    
    # 保存名称缓存
    save_stock_names(names_cache)
    
    conn.close()
    
    # 输出结果
    print(f"\n筛选结果: 共 {len(results)} 只股票符合口袋支点条件")
    
    if results:
        # 创建输出目录
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # 转换为DataFrame
        df_results = pd.DataFrame(results)
        
        # 按涨幅排序
        df_results = df_results.sort_values('price_change', ascending=False)
        
        # 保存到CSV
        date_str = datetime.now().strftime('%Y%m%d')
        output_file = OUTPUT_DIR / f'pocket_pivot_{date_str}.csv'
        
        # 选择输出列
        output_cols = ['symbol', 'name', 'exchange', 'close', 'high_250', 
                       'price_change', 'volume', 'turnover', 'trade_date']
        df_results[output_cols].to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n结果已保存到: {output_file}")
        
        # 显示前20只股票
        print("\n" + "=" * 80)
        print("Top 20 股票:")
        print("=" * 80)
        print(f"{'代码':<8} {'名称':<12} {'收盘价':>8} {'涨幅%':>8} {'成交额':>12}")
        print("-" * 60)
        
        for _, row in df_results.head(20).iterrows():
            print(f"{row['symbol']:<8} {row['name']:<12} {row['close']:>8.2f} "
                  f"{row['price_change']*100:>7.2f}% {row['turnover']:>12.0f}")
        
        return df_results
    else:
        print("\n未找到符合条件的股票")
        return pd.DataFrame()

if __name__ == '__main__':
    screen_pocket_pivot()
