#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
老鸭头形态识别策略

形态特征:
1. 建仓期:股价沿5日、10日、60日均线缓慢上升
2. 鸭头形成:股价向上拉升后回调,形成"鸭头"
3. 鸭颈:股价跌破5日线和10日线,但不破60日均线
4. 鸭嘴张开:股价重新向上突破前期高点
"""

import os
import sqlite3
import pandas as pd
import json
from datetime import datetime
from stock_name_manager import StockNameManager

# 数据库路径
DB_PATH = os.path.expanduser('~/.vntrader/database.db')

# 缓存目录
CACHE_DIR = os.path.expanduser('~/.vntrader')
INDUSTRY_CACHE = os.path.join(CACHE_DIR, 'stock_industries.json')

# 参数配置
DUCK_HEAD_DAYS_MIN = 20  # 鸭头最小距离(天)
DUCK_HEAD_DAYS_MAX = 50  # 鸭头最大距离(天)
DROP_RATE_MIN = 0.08     # 最小回调幅度 8%
DROP_RATE_MAX = 0.30     # 最大回调幅度 30%
MA60_DEVIATION = 0.95    # 60日线允许偏差
VOLUME_RATIO_MIN = 1.1   # 成交量放大倍数
BREAKOUT_THRESHOLD = 0.95 # 突破前高阈值


def get_stock_data(symbol, exchange, days=90):
    """
    获取股票K线数据
    
    Args:
        symbol: 股票代码(不带交易所后缀)
        exchange: 交易所代码(SSE/SZSE)
        days: 获取天数
    
    Returns:
        DataFrame: K线数据
    """
    conn = sqlite3.connect(DB_PATH)
    
    query = f"""
        SELECT datetime, open_price, high_price, low_price, close_price, volume
        FROM dbbardata
        WHERE symbol = '{symbol}'
        AND exchange = '{exchange}'
        AND interval = 'd'
        ORDER BY datetime DESC
        LIMIT {days}
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return None
    
    # 重命名列
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    
    # 反转顺序(从旧到新)
    df = df.iloc[::-1].reset_index(drop=True)
    
    return df


def calculate_indicators(df):
    """
    计算技术指标
    
    Args:
        df: K线数据
    
    Returns:
        DataFrame: 添加了指标的数据
    """
    if df is None or len(df) < 60:
        return None
    
    # 计算均线
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['ma60'] = df['close'].rolling(window=60).mean()
    
    # 计算成交量均线
    df['volume_ma10'] = df['volume'].rolling(window=10).mean()
    
    return df


def find_duck_head(df):
    """
    识别鸭头位置
    
    Returns:
        (idx, price) or (None, None)
    """
    if len(df) < 60:
        return None, None
    
    # 获取最近60天数据
    recent_60 = df.iloc[-60:]
    
    # 找到最高点
    high_idx = recent_60['high'].idxmax()
    high_price = recent_60.loc[high_idx, 'high']
    
    # 计算鸭头距离当前的天数
    days_ago = len(df) - 1 - high_idx
    
    # 检查鸭头是否在合理范围内(20-50天前)
    if DUCK_HEAD_DAYS_MIN <= days_ago <= DUCK_HEAD_DAYS_MAX:
        return high_idx, high_price
    
    return None, None


def find_duck_neck(df, duck_head_idx):
    """
    识别鸭颈位置
    
    Args:
        df: K线数据
        duck_head_idx: 鸭头位置索引
    
    Returns:
        (idx, price, is_valid) 
    """
    if duck_head_idx is None:
        return None, None, False
    
    # 获取鸭头之后的数据
    after_head = df.iloc[duck_head_idx:]
    
    if len(after_head) < 10:  # 至少需要10天数据
        return None, None, False
    
    # 找到最低点
    neck_idx = after_head['low'].idxmin()
    neck_price = after_head.loc[neck_idx, 'low']
    
    # 检查鸭颈条件
    
    # 1. 必须跌破5日线和10日线
    if pd.isna(df.loc[neck_idx, 'ma5']) or pd.isna(df.loc[neck_idx, 'ma10']):
        return neck_idx, neck_price, False
    
    close_at_neck = df.loc[neck_idx, 'close']
    ma5_at_neck = df.loc[neck_idx, 'ma5']
    ma10_at_neck = df.loc[neck_idx, 'ma10']
    
    if not (close_at_neck < ma5_at_neck and close_at_neck < ma10_at_neck):
        return neck_idx, neck_price, False
    
    # 2. 不能深度跌破60日线
    if pd.isna(df.loc[neck_idx, 'ma60']):
        return neck_idx, neck_price, False
    
    ma60_at_neck = df.loc[neck_idx, 'ma60']
    if close_at_neck < ma60_at_neck * MA60_DEVIATION:
        return neck_idx, neck_price, False
    
    return neck_idx, neck_price, True


def check_duck_mouth(df, duck_head_price):
    """
    检查鸭嘴是否张开(突破形态)
    
    Args:
        df: K线数据
        duck_head_price: 鸭头价格
    
    Returns:
        (is_valid, details)
    """
    if len(df) < 5:
        return False, {}
    
    # 获取最新数据
    latest = df.iloc[-1]
    
    # 1. 检查是否接近或突破前高
    if latest['close'] < duck_head_price * BREAKOUT_THRESHOLD:
        return False, {'reason': '未接近前高'}
    
    # 2. 检查是否重新站上5日线和10日线
    if pd.isna(latest['ma5']) or pd.isna(latest['ma10']):
        return False, {'reason': '均线数据不足'}
    
    if not (latest['close'] > latest['ma5'] and latest['close'] > latest['ma10']):
        return False, {'reason': '未站上短期均线'}
    
    # 3. 检查成交量是否放大
    if pd.isna(latest['volume_ma10']):
        return False, {'reason': '成交量数据不足'}
    
    volume_ratio = latest['volume'] / latest['volume_ma10']
    if volume_ratio < VOLUME_RATIO_MIN:
        return False, {'reason': f'成交量未放大({volume_ratio:.2f})'}
    
    # 4. 检查均线多头排列
    if pd.isna(latest['ma60']):
        return False, {'reason': '60日线数据不足'}
    
    if not (latest['ma5'] > latest['ma10'] > latest['ma60']):
        return False, {'reason': '均线未多头排列'}
    
    return True, {
        'volume_ratio': volume_ratio,
        'breakout_rate': latest['close'] / duck_head_price
    }


def identify_old_duck_head(df):
    """
    识别老鸭头形态
    
    Returns:
        (is_duck_head, details)
    """
    if df is None or len(df) < 60:
        return False, {}
    
    # 1. 识别鸭头
    duck_head_idx, duck_head_price = find_duck_head(df)
    if duck_head_idx is None:
        return False, {'reason': '未找到鸭头'}
    
    # 2. 识别鸭颈
    duck_neck_idx, duck_neck_price, neck_valid = find_duck_neck(df, duck_head_idx)
    if not neck_valid:
        return False, {'reason': '鸭颈不符合条件'}
    
    # 3. 计算回调幅度
    drop_rate = (duck_head_price - duck_neck_price) / duck_head_price
    if not (DROP_RATE_MIN <= drop_rate <= DROP_RATE_MAX):
        return False, {'reason': f'回调幅度不符({drop_rate:.1%})'}
    
    # 4. 检查鸭嘴张开
    mouth_valid, mouth_details = check_duck_mouth(df, duck_head_price)
    if not mouth_valid:
        return False, mouth_details
    
    # 形态识别成功
    latest = df.iloc[-1]
    details = {
        'duck_head_price': duck_head_price,
        'duck_neck_price': duck_neck_price,
        'drop_rate': drop_rate,
        'current_price': latest['close'],
        'volume_ratio': mouth_details.get('volume_ratio', 0),
        'breakout_rate': mouth_details.get('breakout_rate', 0),
        'trade_date': latest['date']
    }
    
    return True, details


# 加载中文名称和行业信息
name_manager = StockNameManager()


def load_industry_cache():
    """加载行业信息缓存"""
    if os.path.exists(INDUSTRY_CACHE):
        with open(INDUSTRY_CACHE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_stock_industry(symbol, industry_cache):
    """获取股票行业"""
    if symbol in industry_cache:
        return industry_cache[symbol].get('industry', '')
    return ''


def get_stock_name(symbol):
    """获取股票中文名称"""
    return name_manager.get_name(symbol)


def screen_old_duck_head():
    """
    老鸭头形态筛选主函数
    """
    print("=" * 80)
    print("老鸭头形态识别策略")
    print("=" * 80)
    
    # 加载行业缓存
    industry_cache = load_industry_cache()
    
    # 获取所有股票列表
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT DISTINCT symbol, exchange
        FROM dbbardata
        WHERE interval = 'd'
        AND exchange IN ('SSE', 'SZSE')
    """
    df_symbols = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"共找到 {len(df_symbols)} 只股票")
    
    results = []
    
    for idx, row in df_symbols.iterrows():
        symbol = row['symbol']
        exchange = row['exchange']
        
        # 显示进度
        if (idx + 1) % 500 == 0:
            print(f"处理进度: {idx + 1}/{len(df_symbols)}")
        
        # 获取K线数据
        df = get_stock_data(symbol, exchange, days=90)
        if df is None:
            continue
        
        # 计算指标
        df = calculate_indicators(df)
        if df is None:
            continue
        
        # 识别老鸭头形态
        is_duck_head, details = identify_old_duck_head(df)
        
        if is_duck_head:
            # 获取中文名称
            name = get_stock_name(symbol)
            
            # 获取行业信息
            industry = get_stock_industry(symbol, industry_cache)
            
            results.append({
                'symbol': symbol,
                'name': name,
                'industry': industry,
                'exchange': exchange,
                'close': details['current_price'],
                'duck_head_price': details['duck_head_price'],
                'duck_neck_price': details['duck_neck_price'],
                'drop_rate': details['drop_rate'],
                'volume_ratio': details['volume_ratio'],
                'breakout_rate': details['breakout_rate'],
                'trade_date': details['trade_date']
            })
    
    # 输出结果
    if results:
        df_results = pd.DataFrame(results)
        
        # 按量比排序
        df_results = df_results.sort_values('volume_ratio', ascending=False)
        
        # 保存到CSV
        output_dir = os.path.expanduser('~/.vntrader/screen_results')
        os.makedirs(output_dir, exist_ok=True)
        
        today = datetime.now().strftime('%Y%m%d')
        output_file = os.path.join(output_dir, f'old_duck_head_{today}.csv')
        df_results.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n筛选结果: 共 {len(df_results)} 只股票符合老鸭头形态")
        print(f"\n结果已保存到: {output_file}")
        
        print("\n" + "=" * 100)
        print("Top 20 股票:")
        print("=" * 100)
        print(f"{'代码':<8} {'名称':<10} {'行业':<12} {'收盘价':>8} {'鸭头价':>8} {'回调幅度':>9} {'量比':>6}")
        print("-" * 100)
        
        for _, row in df_results.head(20).iterrows():
            industry = str(row.get('industry', ''))[:10] if row.get('industry') else ''
            print(f"{row['symbol']:<8} {row['name']:<10} {industry:<12} "
                  f"{row['close']:>8.2f} {row['duck_head_price']:>8.2f} "
                  f"{row['drop_rate']:>8.1%} {row['volume_ratio']:>6.2f}")
        
        return df_results
    else:
        print("\n未找到符合条件的股票")
        return pd.DataFrame()


if __name__ == '__main__':
    screen_old_duck_head()
