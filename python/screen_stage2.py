#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二阶段选股策略
根据Mark Minervini的8条标准筛选处于第二阶段的股票

使用方法：
    python3 ~/screen_stage2.py
    python3 ~/screen_stage2.py --min-low-ratio 1.3
    python3 ~/screen_stage2.py --output results.csv
"""

import sqlite3
import pandas as pd
import numpy as np
import argparse
import json
from datetime import datetime
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


def get_stock_data(conn, symbol, days=350):
    """获取股票历史数据"""
    query = """
    SELECT 
        datetime as trade_date,
        open_price as open,
        high_price as high,
        low_price as low,
        close_price as close,
        volume
    FROM dbbardata
    WHERE symbol = ? AND interval = 'd'
    ORDER BY datetime DESC
    LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(symbol, days))
    
    if len(df) == 0:
        return None
    
    df = df.sort_values('trade_date').reset_index(drop=True)
    return df


def check_stage2(df, min_low_ratio=1.25, min_high_ratio=0.75, ma200_up_days=20):
    """
    检查股票是否处于第二阶段
    
    参数:
        df: 股票历史数据
        min_low_ratio: 股价与52周最低点的最小比率，默认1.25（即高出25%）
        min_high_ratio: 股价与52周最高点的最小比率，默认0.75（即75%以内）
        ma200_up_days: 200日均线持续上涨的天数，默认20天
    
    返回: (is_stage2, details)
    """
    if df is None or len(df) < 250:
        return False, {}
    
    # 计算均线
    df['ma50'] = df['close'].rolling(window=50).mean()
    df['ma150'] = df['close'].rolling(window=150).mean()
    df['ma200'] = df['close'].rolling(window=200).mean()
    
    # 获取最新数据
    latest = df.iloc[-1]
    close = latest['close']
    ma50 = latest['ma50']
    ma150 = latest['ma150']
    ma200 = latest['ma200']
    
    # 检查均线是否有值
    if pd.isna(ma50) or pd.isna(ma150) or pd.isna(ma200):
        return False, {}
    
    # 计算52周高低点
    high_250 = df['high'].rolling(window=250).max().iloc[-1]
    low_250 = df['low'].rolling(window=250).min().iloc[-1]
    
    if pd.isna(high_250) or pd.isna(low_250):
        return False, {}
    
    # 检查条件
    conditions = {}
    
    # 条件1: 股价高于150日和200日均线
    conditions['c1_price_above_ma150_ma200'] = close > ma150 and close > ma200
    
    # 条件2: 150日均线高于200日均线
    conditions['c2_ma150_above_ma200'] = ma150 > ma200
    
    # 条件3: 200日均线上涨至少1个月（20个交易日）
    ma200_recent = df['ma200'].iloc[-ma200_up_days:]
    ma200_diff = ma200_recent.diff().dropna()
    conditions['c3_ma200_rising'] = len(ma200_diff) >= ma200_up_days - 1 and all(ma200_diff >= 0)
    
    # 条件4: 50日均线高于150日和200日均线
    conditions['c4_ma50_above_ma150_ma200'] = ma50 > ma150 and ma50 > ma200
    
    # 条件5: 股价高于50日均线
    conditions['c5_price_above_ma50'] = close > ma50
    
    # 条件6: 股价比52周最低点高出指定比例以上
    conditions['c6_price_above_low'] = close / low_250 > min_low_ratio
    
    # 条件7: 股价在52周高点的指定比例以内
    conditions['c7_price_near_high'] = close / high_250 > min_high_ratio
    
    # 所有条件满足
    is_stage2 = all(conditions.values())
    
    # 计算位置比率
    position_ratio = close / high_250 if high_250 > 0 else 0
    
    details = {
        'close': close,
        'ma50': ma50,
        'ma150': ma150,
        'ma200': ma200,
        'low_250': low_250,
        'high_250': high_250,
        'position_ratio': position_ratio,
        'low_ratio': close / low_250,
        'conditions': conditions,
        'trade_date': latest['trade_date'],
        'volume': latest['volume']
    }
    
    return is_stage2, details


def screen_stage2(conn, min_low_ratio=1.25, min_high_ratio=0.75, min_days=250):
    """
    筛选处于第二阶段的股票
    
    参数:
        conn: 数据库连接
        min_low_ratio: 股价与52周最低点的最小比率
        min_high_ratio: 股价与52周最高点的最小比率
        min_days: 最少数据天数
    
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
            df = get_stock_data(conn, symbol, days=350)
            
            if df is None or len(df) < min_days:
                continue
            
            is_stage2, details = check_stage2(df, min_low_ratio, min_high_ratio)
            
            if is_stage2:
                results.append({
                    'symbol': symbol,
                    'name': get_stock_name(symbol, stock_names),
                    'exchange': exchange,
                    'close': details['close'],
                    'ma50': details['ma50'],
                    'ma150': details['ma150'],
                    'ma200': details['ma200'],
                    'high_250': details['high_250'],
                    'low_250': details['low_250'],
                    'position_ratio': details['position_ratio'],
                    'low_ratio': details['low_ratio'],
                    'trade_date': details['trade_date'],
                    'volume': details['volume']
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
        output_file = OUTPUT_DIR / f'stage2_{timestamp}.csv'
    
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n结果已保存到: {output_file}")
    return output_file


def print_results(df, top_n=30):
    """打印筛选结果"""
    if len(df) == 0:
        print("\n没有找到符合条件的股票")
        return
    
    print(f"\n{'='*100}")
    print(f"第二阶段筛选结果")
    print(f"{'='*100}")
    print(f"筛选条件: Mark Minervini 8条标准")
    print(f"筛选结果: 共 {len(df)} 只股票")
    print(f"{'='*100}")
    
    # 打印前N个
    print(f"\nTop {min(top_n, len(df))} 股票:\n")
    
    header = f"{'代码':<8} {'名称':<8} {'收盘价':>8} {'MA50':>8} {'位置%':>7} {'涨幅%':>7} {'成交量':>10}"
    print(header)
    print('-' * len(header))
    
    for idx, row in df.head(top_n).iterrows():
        vol = row['volume'] / 10000 if row['volume'] > 0 else 0
        low_change = (row['low_ratio'] - 1) * 100
        name = row.get('name', '')[:6] if row.get('name') else ''
        print(f"{row['symbol']:<8} {name:<8} {row['close']:>8.2f} {row['ma50']:>8.2f} {row['position_ratio']*100:>6.1f}% {low_change:>6.1f}% {vol:>8.0f}万")
    
    # 统计信息
    print(f"\n{'='*100}")
    print("统计信息:")
    print(f"  - 位置95%-100%: {len(df[(df['position_ratio'] >= 0.95) & (df['position_ratio'] < 1.0)])} 只")
    print(f"  - 位置90%-95%: {len(df[(df['position_ratio'] >= 0.90) & (df['position_ratio'] < 0.95)])} 只")
    print(f"  - 位置75%-90%: {len(df[(df['position_ratio'] >= 0.75) & (df['position_ratio'] < 0.90)])} 只")
    print(f"  - 从低点涨幅50%-100%: {len(df[(df['low_ratio'] >= 1.5) & (df['low_ratio'] < 2.0)])} 只")
    print(f"  - 从低点涨幅100%-200%: {len(df[(df['low_ratio'] >= 2.0) & (df['low_ratio'] < 3.0)])} 只")
    print(f"  - 从低点涨幅200%以上: {len(df[df['low_ratio'] >= 3.0])} 只")


def main():
    parser = argparse.ArgumentParser(description='第二阶段选股策略')
    parser.add_argument('--min-low-ratio', type=float, default=1.25,
                        help='股价与52周最低点的最小比率，默认1.25 (高出25%%)')
    parser.add_argument('--min-high-ratio', type=float, default=0.75,
                        help='股价与52周最高点的最小比率，默认0.75 (75%%以内)')
    parser.add_argument('--min-days', type=int, default=250,
                        help='最少数据天数，默认250天')
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
        results = screen_stage2(
            conn,
            min_low_ratio=args.min_low_ratio,
            min_high_ratio=args.min_high_ratio,
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
