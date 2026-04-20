#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
老鸭头策略回测工具

通过滑动窗口方式，扫描历史上所有触发老鸭头信号的时点，
计算未来N天的收益率，统计策略的成功率和收益分布。
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import json

# 导入策略识别函数
from screen_old_duck_head import (
    calculate_indicators,
    identify_old_duck_head,
    DB_PATH
)

# 回测参数
HOLDING_PERIODS = [5, 10, 20]  # 持仓周期（天）
BACKTEST_START_DATE = '2023-01-01'  # 回测开始日期
BACKTEST_END_DATE = '2026-04-20'     # 回测结束日期
MIN_DATA_DAYS = 90                    # 最少需要的历史数据天数


def get_all_trading_dates(start_date=None, end_date=None):
    """
    获取所有交易日列表
    
    Returns:
        list: 交易日期列表 ['2023-01-01', '2023-01-02', ...]
    """
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT DISTINCT datetime
        FROM dbbardata
        WHERE interval = 'd'
    """
    
    if start_date:
        query += f" AND datetime >= '{start_date}'"
    if end_date:
        query += f" AND datetime <= '{end_date}'"
    
    query += " ORDER BY datetime"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # 提取日期（去掉时间部分）
    dates = [d.split()[0] for d in df['datetime'].tolist()]
    return dates


def get_stock_list():
    """
    获取所有股票列表
    
    Returns:
        list: [(symbol, exchange), ...]
    """
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT DISTINCT symbol, exchange
        FROM dbbardata
        WHERE interval = 'd'
        AND exchange IN ('SSE', 'SZSE')
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return [(row['symbol'], row['exchange']) for _, row in df.iterrows()]


def get_historical_data(symbol, exchange, end_date, days=120):
    """
    获取截止到指定日期的历史数据
    
    Args:
        symbol: 股票代码
        exchange: 交易所
        end_date: 截止日期
        days: 获取天数
    
    Returns:
        DataFrame or None
    """
    conn = sqlite3.connect(DB_PATH)
    
    query = f"""
        SELECT datetime, open_price, high_price, low_price, close_price, volume
        FROM dbbardata
        WHERE symbol = '{symbol}'
        AND exchange = '{exchange}'
        AND interval = 'd'
        AND datetime <= '{end_date}'
        ORDER BY datetime DESC
        LIMIT {days}
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty or len(df) < MIN_DATA_DAYS:
        return None
    
    # 重命名列
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    
    # 反转顺序（从旧到新）
    df = df.iloc[::-1].reset_index(drop=True)
    
    return df


def get_future_data(symbol, exchange, start_date, days):
    """
    获取指定日期之后的数据
    
    Args:
        symbol: 股票代码
        exchange: 交易所
        start_date: 起始日期（不包含）
        days: 获取天数
    
    Returns:
        DataFrame or None
    """
    conn = sqlite3.connect(DB_PATH)
    
    query = f"""
        SELECT datetime, open_price, high_price, low_price, close_price, volume
        FROM dbbardata
        WHERE symbol = '{symbol}'
        AND exchange = '{exchange}'
        AND interval = 'd'
        AND datetime > '{start_date}'
        ORDER BY datetime ASC
        LIMIT {days}
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return None
    
    # 重命名列
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    
    return df


def calculate_returns(buy_price, future_data):
    """
    计算收益指标
    
    Args:
        buy_price: 买入价格
        future_data: 未来数据
    
    Returns:
        dict: 收益指标
    """
    if future_data is None or len(future_data) == 0:
        return None
    
    # 最高收益（期间最高价）
    max_gain = (future_data['high'].max() - buy_price) / buy_price * 100
    
    # 最低价（期间最低价）
    max_drawdown = (future_data['low'].min() - buy_price) / buy_price * 100
    
    # 最终收益（持仓期结束时的收盘价）
    final_return = (future_data['close'].iloc[-1] - buy_price) / buy_price * 100
    
    # 达到最高收益的天数
    max_gain_day = future_data['high'].idxmax() + 1  # +1因为从0开始
    
    return {
        'max_gain': max_gain,
        'max_drawdown': max_drawdown,
        'final_return': final_return,
        'max_gain_day': max_gain_day,
        'holding_days': len(future_data)
    }


def classify_market_env(date, trading_dates):
    """
    简单的市场环境分类
    基于日期范围粗略判断（实际应该用指数数据）
    
    Args:
        date: 交易日期
        trading_dates: 所有交易日列表
    
    Returns:
        str: 'bull', 'consolidation', 'bear'
    """
    # 这里简化处理，实际应该根据大盘指数走势判断
    # 可以用沪深300或上证指数的MA120斜率等指标
    
    year = int(date[:4])
    month = int(date[5:7])
    
    # 示例分类（需要根据实际市场情况调整）
    if (year == 2023 and month <= 6) or (year == 2024 and month >= 10):
        return 'bull'
    elif year == 2024 and 4 <= month <= 9:
        return 'bear'
    else:
        return 'consolidation'


def scan_historical_signals(stock_list, trading_dates, holding_period=10, 
                           sample_rate=0.1, max_stocks=100):
    """
    扫描历史信号
    
    Args:
        stock_list: 股票列表
        trading_dates: 交易日列表
        holding_period: 持仓周期
        sample_rate: 采样率（0-1），用于加快回测速度
        max_stocks: 最多测试的股票数量
    
    Returns:
        list: 信号列表
    """
    signals = []
    
    # 限制股票数量和采样
    if len(stock_list) > max_stocks:
        stock_list = stock_list[:max_stocks]
    
    # 计算需要扫描的日期范围
    # 至少留出holding_period天用于计算未来收益
    scan_dates = trading_dates[:-holding_period]
    
    # 采样交易日以加快速度
    if sample_rate < 1.0:
        sample_size = int(len(scan_dates) * sample_rate)
        scan_dates = scan_dates[::int(1/sample_rate)] if sample_rate > 0 else scan_dates[:sample_size]
    
    total_tasks = len(stock_list) * len(scan_dates)
    processed = 0
    
    print(f"开始回测...")
    print(f"股票数量: {len(stock_list)}")
    print(f"扫描日期: {len(scan_dates)} 天")
    print(f"总任务数: {total_tasks}")
    print(f"持仓周期: {holding_period} 天")
    print("-" * 80)
    
    for stock_idx, (symbol, exchange) in enumerate(stock_list):
        for date_idx, scan_date in enumerate(scan_dates):
            processed += 1
            
            # 显示进度
            if processed % 1000 == 0 or processed == total_tasks:
                progress = processed / total_tasks * 100
                print(f"进度: {processed}/{total_tasks} ({progress:.1f}%) - "
                      f"已找到 {len(signals)} 个信号")
            
            # 获取截止到scan_date的历史数据
            df_history = get_historical_data(symbol, exchange, scan_date, days=120)
            if df_history is None:
                continue
            
            # 计算指标
            df_history = calculate_indicators(df_history)
            if df_history is None:
                continue
            
            # 判断是否触发老鸭头信号
            is_signal, details = identify_old_duck_head(df_history)
            
            if is_signal:
                # 获取未来数据计算收益
                future_data = get_future_data(symbol, exchange, scan_date, holding_period)
                
                if future_data is None or len(future_data) < holding_period:
                    continue
                
                buy_price = df_history['close'].iloc[-1]
                returns = calculate_returns(buy_price, future_data)
                
                if returns is None:
                    continue
                
                # 判断市场环境
                market_env = classify_market_env(scan_date, trading_dates)
                
                # 记录信号
                signals.append({
                    'symbol': symbol,
                    'exchange': exchange,
                    'signal_date': scan_date,
                    'buy_price': buy_price,
                    'market_env': market_env,
                    'duck_head_price': details.get('duck_head_price', 0),
                    'duck_neck_price': details.get('duck_neck_price', 0),
                    'drop_rate': details.get('drop_rate', 0),
                    'volume_ratio': details.get('volume_ratio', 0),
                    **returns
                })
    
    print(f"\n扫描完成! 共找到 {len(signals)} 个历史信号")
    
    return signals


def analyze_signals(signals, holding_period):
    """
    分析信号统计数据
    
    Args:
        signals: 信号列表
        holding_period: 持仓周期
    
    Returns:
        dict: 统计结果
    """
    if not signals:
        return None
    
    df = pd.DataFrame(signals)
    
    # 总体统计
    total_signals = len(df)
    success_signals = len(df[df['final_return'] > 0])
    success_rate = success_signals / total_signals * 100 if total_signals > 0 else 0
    
    avg_return = df['final_return'].mean()
    median_return = df['final_return'].median()
    max_return = df['final_return'].max()
    min_return = df['final_return'].min()
    
    max_gain_avg = df['max_gain'].mean()
    max_dd_avg = df['max_drawdown'].mean()
    
    # 找出最佳和最差案例
    best_case = df.loc[df['final_return'].idxmax()].to_dict()
    worst_case = df.loc[df['final_return'].idxmin()].to_dict()
    
    # 收益分布
    bins = [-100, -10, -5, 0, 5, 10, 20, 100]
    labels = ['< -10%', '-10% ~ -5%', '-5% ~ 0%', '0% ~ 5%', 
              '5% ~ 10%', '10% ~ 20%', '> 20%']
    df['return_bin'] = pd.cut(df['final_return'], bins=bins, labels=labels)
    return_dist = df['return_bin'].value_counts().sort_index()
    
    # 按市场环境分析
    env_stats = {}
    for env in ['bull', 'consolidation', 'bear']:
        df_env = df[df['market_env'] == env]
        if len(df_env) > 0:
            env_stats[env] = {
                'count': len(df_env),
                'success_rate': len(df_env[df_env['final_return'] > 0]) / len(df_env) * 100,
                'avg_return': df_env['final_return'].mean(),
                'median_return': df_env['final_return'].median()
            }
    
    return {
        'holding_period': holding_period,
        'total_signals': total_signals,
        'success_signals': success_signals,
        'success_rate': success_rate,
        'avg_return': avg_return,
        'median_return': median_return,
        'max_return': max_return,
        'min_return': min_return,
        'max_gain_avg': max_gain_avg,
        'max_dd_avg': max_dd_avg,
        'best_case': best_case,
        'worst_case': worst_case,
        'return_dist': return_dist.to_dict(),
        'env_stats': env_stats
    }


def print_backtest_report(analysis, signals_df=None):
    """
    打印回测报告
    
    Args:
        analysis: 分析结果
        signals_df: 信号DataFrame（可选）
    """
    if analysis is None:
        print("无回测数据")
        return
    
    print("\n" + "=" * 80)
    print("老鸭头策略回测报告")
    print("=" * 80)
    print(f"回测周期: {BACKTEST_START_DATE} ~ {BACKTEST_END_DATE}")
    print(f"持仓周期: {analysis['holding_period']} 个交易日")
    print()
    
    print("总体表现:")
    print("-" * 80)
    print(f"总信号数:          {analysis['total_signals']}")
    print(f"成功信号:          {analysis['success_signals']} ({analysis['success_rate']:.2f}%)")
    print(f"失败信号:          {analysis['total_signals'] - analysis['success_signals']} "
          f"({100 - analysis['success_rate']:.2f}%)")
    print("-" * 80)
    print(f"平均收益:          {analysis['avg_return']:+.2f}%")
    print(f"中位数收益:        {analysis['median_return']:+.2f}%")
    print(f"最大收益:          {analysis['max_return']:+.2f}% "
          f"({analysis['best_case']['symbol']} {analysis['best_case']['signal_date']})")
    print(f"最大亏损:          {analysis['min_return']:+.2f}% "
          f"({analysis['worst_case']['symbol']} {analysis['worst_case']['signal_date']})")
    print(f"期间最高平均:      {analysis['max_gain_avg']:+.2f}%")
    print(f"最大回撤平均:      {analysis['max_dd_avg']:+.2f}%")
    print("-" * 80)
    
    print("\n收益分布:")
    print("-" * 80)
    for bin_label, count in analysis['return_dist'].items():
        percentage = count / analysis['total_signals'] * 100
        bar = '█' * int(percentage / 2)
        print(f"{bin_label:>12}: {count:>4} ({percentage:>5.1f}%) {bar}")
    print("-" * 80)
    
    if analysis['env_stats']:
        print("\n按市场环境分析:")
        print("-" * 80)
        
        env_names = {
            'bull': '牛市',
            'consolidation': '震荡市',
            'bear': '熊市'
        }
        
        for env, stats in analysis['env_stats'].items():
            print(f"\n{env_names.get(env, env)}:")
            print(f"  信号数: {stats['count']:<6}  "
                  f"成功率: {stats['success_rate']:.1f}%  "
                  f"平均收益: {stats['avg_return']:+.2f}%  "
                  f"中位数: {stats['median_return']:+.2f}%")
        
        print("-" * 80)
    
    # 结论
    print("\n策略评估:")
    print("-" * 80)
    
    bull_rate = analysis['env_stats'].get('bull', {}).get('success_rate', 0)
    cons_rate = analysis['env_stats'].get('consolidation', {}).get('success_rate', 0)
    bear_rate = analysis['env_stats'].get('bear', {}).get('success_rate', 0)
    
    if bull_rate >= 70:
        print(f"✅ 牛市表现优异 ({bull_rate:.1f}%胜率) - 推荐使用")
    elif bull_rate >= 60:
        print(f"⚠️  牛市表现一般 ({bull_rate:.1f}%胜率) - 谨慎使用")
    else:
        print(f"❌ 牛市表现不佳 ({bull_rate:.1f}%胜率)")
    
    if cons_rate >= 60:
        print(f"✅ 震荡市可用 ({cons_rate:.1f}%胜率)")
    elif cons_rate >= 50:
        print(f"⚠️  震荡市需谨慎 ({cons_rate:.1f}%胜率) - 精选信号")
    else:
        print(f"❌ 震荡市不推荐 ({cons_rate:.1f}%胜率)")
    
    if bear_rate >= 50:
        print(f"⚠️  熊市勉强可用 ({bear_rate:.1f}%胜率) - 严格筛选")
    else:
        print(f"❌ 熊市不建议使用 ({bear_rate:.1f}%胜率) - 保持空仓")
    
    print("-" * 80)
    
    # 策略建议
    print("\n参数优化建议:")
    print("-" * 80)
    if analysis['avg_return'] < 5:
        print("• 平均收益偏低，考虑:")
        print("  - 提高成交量放大倍数(如1.1→1.5)以过滤假突破")
        print("  - 增加RPS强度筛选(如RPS50>85)")
    
    if analysis['max_dd_avg'] < -8:
        print("• 平均最大回撤较大，考虑:")
        print("  - 缩紧止损位(如鸭颈下方3-5%)")
        print("  - 增加市场环境过滤")
    
    if bear_rate > 0 and bear_rate < 45:
        print("• 熊市胜率低，建议:")
        print("  - 熊市暂停使用该策略")
        print("  - 或仅选择行业龙头+RPS>90的标的")
    
    print("=" * 80)


def save_backtest_results(signals, analysis, holding_period):
    """
    保存回测结果
    
    Args:
        signals: 信号列表
        analysis: 分析结果
        holding_period: 持仓周期
    """
    output_dir = os.path.expanduser('~/.vntrader/backtest_results')
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存信号CSV
    df_signals = pd.DataFrame(signals)
    timestamp = datetime.now().strftime('%Y%m%d')
    csv_file = os.path.join(output_dir, 
                            f'old_duck_head_backtest_{holding_period}d_{timestamp}.csv')
    df_signals.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"\n详细信号已保存到: {csv_file}")
    
    # 保存分析结果JSON
    json_file = os.path.join(output_dir, 
                            f'old_duck_head_analysis_{holding_period}d_{timestamp}.json')
    
    # 转换return_dist为可序列化格式
    analysis_copy = analysis.copy()
    analysis_copy['return_dist'] = {str(k): int(v) for k, v in analysis['return_dist'].items()}
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_copy, f, ensure_ascii=False, indent=2)
    print(f"分析结果已保存到: {json_file}")


def backtest_old_duck_head(holding_period=10, sample_rate=0.1, max_stocks=100):
    """
    老鸭头策略回测主函数
    
    Args:
        holding_period: 持仓周期（天）
        sample_rate: 采样率（0-1），0.1表示采样10%的交易日
        max_stocks: 最多测试的股票数
    """
    print("\n" + "=" * 80)
    print("老鸭头策略回测 - 开始")
    print("=" * 80)
    
    # 1. 获取交易日列表
    print("正在获取交易日列表...")
    trading_dates = get_all_trading_dates(BACKTEST_START_DATE, BACKTEST_END_DATE)
    print(f"找到 {len(trading_dates)} 个交易日")
    
    # 2. 获取股票列表
    print("正在获取股票列表...")
    stock_list = get_stock_list()
    print(f"找到 {len(stock_list)} 只股票")
    
    if len(stock_list) > max_stocks:
        print(f"限制股票数量为 {max_stocks} 只（加快回测速度）")
    
    # 3. 扫描历史信号
    signals = scan_historical_signals(
        stock_list, 
        trading_dates, 
        holding_period=holding_period,
        sample_rate=sample_rate,
        max_stocks=max_stocks
    )
    
    if not signals:
        print("\n未找到任何历史信号，请检查数据或调整参数")
        return
    
    # 4. 分析信号
    print("\n正在分析信号...")
    analysis = analyze_signals(signals, holding_period)
    
    # 5. 打印报告
    print_backtest_report(analysis, pd.DataFrame(signals))
    
    # 6. 保存结果
    save_backtest_results(signals, analysis, holding_period)
    
    print("\n" + "=" * 80)
    print("回测完成!")
    print("=" * 80)
    
    return signals, analysis


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='老鸭头策略回测工具')
    parser.add_argument('--holding-period', type=int, default=10,
                       help='持仓周期（天），默认10天')
    parser.add_argument('--sample-rate', type=float, default=0.1,
                       help='采样率（0-1），默认0.1（10%%的交易日）')
    parser.add_argument('--max-stocks', type=int, default=100,
                       help='最多测试的股票数，默认100只')
    
    args = parser.parse_args()
    
    backtest_old_duck_head(
        holding_period=args.holding_period,
        sample_rate=args.sample_rate,
        max_stocks=args.max_stocks
    )
