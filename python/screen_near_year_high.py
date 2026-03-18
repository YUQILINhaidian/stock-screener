#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
接近一年新高选股策略
根据陶博士2006的方法：CLOSE/HHV(HIGH,250) > 0.9

使用方法：
    python3 ~/screen_near_year_high.py
    python3 ~/screen_near_year_high.py --threshold 0.95
    python3 ~/screen_near_year_high.py --output results.csv
"""

import sqlite3
import pandas as pd
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

# 数据库路径
DB_PATH = Path.home() / '.vntrader' / 'database.db'

# 股票名称缓存路径
STOCK_NAMES_FILE = Path.home() / '.vntrader' / 'stock_names.json'

# 输出目录
OUTPUT_DIR = Path.home() / '.vntrader' / 'screen_results'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_stock_names():
    """加载股票名称缓存"""
    if STOCK_NAMES_FILE.exists():
        with open(STOCK_NAMES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_stock_name(symbol, stock_names):
    """获取股票名称"""
    return stock_names.get(symbol, '')


def get_all_stocks(conn):
    """获取所有股票列表"""
    query = """
    SELECT DISTINCT symbol, exchange 
    FROM dbbardata 
    WHERE interval = 'd'
    ORDER BY symbol
    """
    df = pd.read_sql_query(query, conn)
    return df


def get_stock_data(conn, symbol, days=400):
    """获取单只股票的历史数据"""
    query = """
    SELECT 
        datetime as trade_date,
        open_price as open,
        high_price as high,
        low_price as low,
        close_price as close,
        volume,
        turnover
    FROM dbbardata
    WHERE symbol = ? AND interval = 'd'
    ORDER BY datetime DESC
    LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(symbol, days))
    df = df.sort_values('trade_date').reset_index(drop=True)
    return df


def screen_near_year_high(conn, threshold=0.9, min_days=100):
    """
    筛选接近一年新高的股票
    
    参数:
        conn: 数据库连接
        threshold: 阈值，默认0.9表示90%
        min_days: 最少需要的数据天数
    
    返回:
        DataFrame: 符合条件的股票列表
    """
    stocks = get_all_stocks(conn)
    results = []
    
    # 加载股票名称
    stock_names = load_stock_names()
    
    total = len(stocks)
    print(f"正在扫描 {total} 只股票...")
    
    for idx, row in stocks.iterrows():
        symbol = row['symbol']
        exchange = row['exchange']
        
        if idx % 500 == 0:
            print(f"进度: {idx}/{total} ({idx*100/total:.1f}%)")
        
        try:
            df = get_stock_data(conn, symbol, days=300)
            
            if len(df) < min_days:
                continue
            
            # 计算过去250个交易日的最高价
            window = min(250, len(df))
            df['high_250'] = df['high'].rolling(window=window).max()
            
            # 获取最新数据
            latest = df.iloc[-1]
            close = latest['close']
            high_250 = latest['high_250']
            
            if pd.isna(high_250) or high_250 <= 0:
                continue
            
            # 计算位置比率
            position_ratio = close / high_250
            
            # 检查是否达到一年新高
            is_new_high = latest['high'] >= high_250
            
            if position_ratio >= threshold:
                results.append({
                    'symbol': symbol,
                    'name': get_stock_name(symbol, stock_names),
                    'exchange': exchange,
                    'close': close,
                    'high_250': high_250,
                    'position_ratio': round(position_ratio, 4),
                    'is_new_high': is_new_high,
                    'trade_date': latest['trade_date'],
                    'volume': latest['volume'],
                    'turnover': latest['turnover']
                })
        except Exception as e:
            continue
    
    print(f"进度: {total}/{total} (100%)")
    
    # 转换为DataFrame并排序
    result_df = pd.DataFrame(results)
    if len(result_df) > 0:
        result_df = result_df.sort_values('position_ratio', ascending=False)
    
    return result_df


def save_results(df, output_file=None):
    """保存筛选结果"""
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = OUTPUT_DIR / f'near_year_high_{timestamp}.csv'
    
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n结果已保存到: {output_file}")
    return output_file


def print_results(df, top_n=30):
    """打印筛选结果"""
    if len(df) == 0:
        print("\n没有找到符合条件的股票")
        return
    
    print(f"\n{'='*90}")
    print(f"接近一年新高筛选结果")
    print(f"{'='*90}")
    print(f"筛选条件: 收盘价 >= 250日最高价 × 90%")
    print(f"筛选结果: 共 {len(df)} 只股票")
    print(f"{'='*90}")
    
    # 打印前N个
    print(f"\nTop {min(top_n, len(df))} 股票:\n")
    
    header = f"{'代码':<8} {'名称':<8} {'收盘价':>8} {'250日高':>8} {'位置%':>7} {'新高':>4} {'日期':<12}"
    print(header)
    print('-' * len(header))
    
    for idx, row in df.head(top_n).iterrows():
        new_high_mark = '★' if row['is_new_high'] else ' '
        name = row.get('name', '')[:6] if row.get('name') else ''
        print(f"{row['symbol']:<8} {name:<8} {row['close']:>8.2f} {row['high_250']:>8.2f} {row['position_ratio']*100:>6.1f}% {new_high_mark:>4} {row['trade_date']:<12}")
    
    # 统计信息
    print(f"\n{'='*90}")
    print("统计信息:")
    print(f"  - 创一年新高股票: {df['is_new_high'].sum()} 只")
    print(f"  - 位置90%-95%: {len(df[(df['position_ratio'] >= 0.9) & (df['position_ratio'] < 0.95)])} 只")
    print(f"  - 位置95%-99%: {len(df[(df['position_ratio'] >= 0.95) & (df['position_ratio'] < 0.99)])} 只")
    print(f"  - 位置99%-100%: {len(df[(df['position_ratio'] >= 0.99) & (df['position_ratio'] < 1.0)])} 只")
    print(f"  - 创新高(>=100%): {len(df[df['position_ratio'] >= 1.0])} 只")


def main():
    parser = argparse.ArgumentParser(description='接近一年新高选股策略')
    parser.add_argument('--threshold', type=float, default=0.9, 
                        help='筛选阈值，默认0.9 (90%%)')
    parser.add_argument('--min-days', type=int, default=100,
                        help='最少数据天数，默认100天')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='输出文件路径')
    parser.add_argument('--top', type=int, default=30,
                        help='显示前N个结果，默认30')
    
    args = parser.parse_args()
    
    # 连接数据库
    print(f"连接数据库: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # 执行筛选
        results = screen_near_year_high(
            conn, 
            threshold=args.threshold,
            min_days=args.min_days
        )
        
        # 打印结果
        print_results(results, top_n=args.top)
        
        # 保存结果
        if len(results) > 0:
            save_results(results, args.output)
    
    finally:
        conn.close()


if __name__ == '__main__':
    main()
