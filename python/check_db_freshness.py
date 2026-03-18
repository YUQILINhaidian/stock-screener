#!/usr/bin/env python3
"""
检查数据库最新数据时间
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.expanduser("~"))

from vnpy.trader.database import get_database
from vnpy.trader.constant import Exchange, Interval


def check_database_latest_time():
    """检查数据库最新时间"""
    print("=" * 80)
    print("数据库数据新鲜度检查")
    print("=" * 80)
    
    db = get_database()
    
    # 获取所有股票概览
    symbols = db.get_bar_overview()
    
    print(f"\n总股票数: {len(symbols)}")
    
    # 统计各个交易所的最新时间
    latest_dates = {}
    
    for overview in symbols[:100]:  # 抽样检查前100只
        symbol = overview.symbol
        exchange = overview.exchange
        
        if exchange not in [Exchange.SSE, Exchange.SZSE]:
            continue
        
        # 获取最新的一根K线
        bars = db.load_bar_data(
            symbol=symbol,
            exchange=exchange,
            interval=Interval.DAILY,
            start=datetime(2026, 1, 1),
            end=datetime(2026, 12, 31)
        )
        
        if bars:
            latest_bar = bars[-1]
            latest_date = latest_bar.datetime.date()
            
            if exchange not in latest_dates:
                latest_dates[exchange] = []
            
            latest_dates[exchange].append((symbol, latest_date))
    
    # 显示结果
    print("\n" + "-" * 80)
    print("抽样检查结果（前100只股票）")
    print("-" * 80)
    
    for exchange, dates in latest_dates.items():
        if dates:
            latest = max(dates, key=lambda x: x[1])
            oldest = min(dates, key=lambda x: x[1])
            
            print(f"\n{exchange.value} 交易所:")
            print(f"  最新数据: {latest[1]} ({latest[0]})")
            print(f"  最旧数据: {oldest[1]} ({oldest[0]})")
            print(f"  样本数: {len(dates)}只")
    
    # 检查几只代表性股票
    print("\n" + "-" * 80)
    print("代表性股票数据检查")
    print("-" * 80)
    
    test_symbols = [
        ("600000", Exchange.SSE, "浦发银行"),
        ("000001", Exchange.SZSE, "平安银行"),
        ("688125", Exchange.SSE, "科创板样本"),
    ]
    
    for symbol, exchange, name in test_symbols:
        bars = db.load_bar_data(
            symbol=symbol,
            exchange=exchange,
            interval=Interval.DAILY,
            start=datetime(2026, 2, 1),
            end=datetime(2026, 12, 31)
        )
        
        if bars:
            latest = bars[-1].datetime.date()
            print(f"{symbol}.{exchange.value} ({name}): {latest} - {len(bars)}条记录")
        else:
            print(f"{symbol}.{exchange.value} ({name}): 无数据")
    
    # 当前日期
    today = datetime.now().date()
    print(f"\n当前日期: {today}")
    
    # 数据延迟
    if latest_dates:
        all_dates = []
        for dates in latest_dates.values():
            all_dates.extend([d[1] for d in dates])
        
        if all_dates:
            max_date = max(all_dates)
            delay = (today - max_date).days
            
            print(f"最新数据: {max_date}")
            print(f"数据延迟: {delay}天")
            
            if delay == 0:
                print("✅ 数据是最新的")
            elif delay == 1:
                print("✅ 数据延迟1天（正常，当日数据通常次日更新）")
            elif delay <= 3:
                print("⚠️  数据有{delay}天延迟，建议更新")
            else:
                print(f"❌ 数据严重过期（延迟{delay}天），需要更新")


if __name__ == "__main__":
    check_database_latest_time()
