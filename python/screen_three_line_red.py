#!/usr/bin/env python3
"""
三线红筛选脚本
筛选 RPS5>90, RPS120>90, RPS250>90 的股票
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.expanduser("~"))
sys.path.insert(0, os.path.join(os.path.expanduser("~"), "fundamentals"))

from fundamentals.rps_fundamental_screener import RPSFundamentalScreener


def main():
    """筛选三线红股票"""
    print("=" * 80)
    print("三线红筛选策略")
    print("条件: RPS5>90, RPS120>90, RPS250>90")
    print("=" * 80)
    
    # 创建筛选器
    screener = RPSFundamentalScreener()
    
    # 加载数据
    print("\n加载RPS数据...")
    screener.load_rps_data()
    
    # 执行筛选
    print("\n执行筛选...")
    stocks = screener.screen(
        rps_5_min=90,
        rps_120_min=90,
        rps_250_min=90,
        sort_by='rps_120',
        top_n=200  # 不限制数量，显示所有符合条件的
    )
    
    # 显示结果
    if stocks.empty:
        print("\n⚠️  没有找到符合条件的股票")
        return
    
    print(f"\n✅ 找到 {len(stocks)} 只符合条件的股票")
    
    # 显示详细列表
    display_cols = ['symbol', 'latest_price', 'rps_5', 'rps_10', 'rps_50', 'rps_120', 'rps_250', 'rps_sum']
    available_cols = [col for col in display_cols if col in stocks.columns]
    
    print("\n符合条件的股票列表:")
    print(stocks[available_cols].to_string(index=False))
    
    # 统计信息
    print("\n" + "=" * 80)
    print("统计信息:")
    print("=" * 80)
    
    if 'latest_price' in stocks.columns:
        print(f"价格范围: {stocks['latest_price'].min():.2f} - {stocks['latest_price'].max():.2f}")
        print(f"平均价格: {stocks['latest_price'].mean():.2f}")
    
    if 'rps_sum' in stocks.columns:
        print(f"RPS之和范围: {stocks['rps_sum'].min():.2f} - {stocks['rps_sum'].max():.2f}")
        print(f"平均RPS之和: {stocks['rps_sum'].mean():.2f}")
    
    # 导出到CSV
    output_file = os.path.expanduser(f"~/.vntrader/three_line_red_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    stocks[available_cols].to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n结果已导出到: {output_file}")
    
    print("\n" + "=" * 80)
    print("✅ 筛选完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
