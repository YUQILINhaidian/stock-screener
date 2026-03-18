#!/usr/bin/env python3
"""
火车头策略筛选股票深度分析

对筛选出的股票进行多维度分析：
1. 基本统计
2. RPS分析
3. 策略分组
4. 价格分布
5. 风险评估
6. 推荐排序
"""

import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.expanduser("~"))

from stock_name_manager import StockNameManager


def analyze_stocks(csv_file: str):
    """分析筛选出的股票"""
    
    print("=" * 80)
    print("火车头策略筛选股票深度分析")
    print("=" * 80)
    
    # 读取数据
    df = pd.read_csv(csv_file)
    
    # 添加股票名称
    name_manager = StockNameManager()
    df['name'] = df['symbol'].apply(name_manager.get_name)
    
    print(f"\n总股票数: {len(df)}")
    print(f"数据来源: {csv_file}")
    print()
    
    # === 1. 基本统计 ===
    print("-" * 80)
    print("1. 基本统计")
    print("-" * 80)
    
    print(f"\n价格统计:")
    print(f"  最高价: {df['price'].max():.2f} 元")
    print(f"  最低价: {df['price'].min():.2f} 元")
    print(f"  平均价: {df['price'].mean():.2f} 元")
    print(f"  中位数: {df['price'].median():.2f} 元")
    
    print(f"\nRPS120统计:")
    print(f"  最高: {df['rps_120'].max():.2f}")
    print(f"  最低: {df['rps_120'].min():.2f}")
    print(f"  平均: {df['rps_120'].mean():.2f}")
    
    print(f"\nRPS和统计:")
    print(f"  最高: {df['rps_sum'].max():.2f}")
    print(f"  最低: {df['rps_sum'].min():.2f}")
    print(f"  平均: {df['rps_sum'].mean():.2f}")
    
    print(f"\n回撤统计:")
    print(f"  最大回撤: {df['max_dd_120'].max():.2f}%")
    print(f"  最小回撤: {df['max_dd_120'].min():.2f}%")
    print(f"  平均回撤: {df['max_dd_120'].mean():.2f}%")
    
    # === 2. RPS分析 ===
    print("\n" + "-" * 80)
    print("2. RPS强度分析")
    print("-" * 80)
    
    # RPS和分组
    rps_groups = [
        (">195", df['rps_sum'] > 195),
        ("190-195", (df['rps_sum'] >= 190) & (df['rps_sum'] <= 195)),
        ("185-190", (df['rps_sum'] >= 185) & (df['rps_sum'] < 190)),
        ("<185", df['rps_sum'] < 185),
    ]
    
    print("\nRPS和分组:")
    for label, condition in rps_groups:
        count = condition.sum()
        pct = count / len(df) * 100
        print(f"  {label:10s}: {count:2d} 只 ({pct:5.1f}%)")
    
    # 短期RPS分析
    print("\n短期RPS强度（RPS5）:")
    rps5_strong = (df['rps_5'] > 90).sum()
    rps5_very_strong = (df['rps_5'] > 95).sum()
    print(f"  RPS5 > 90: {rps5_strong} 只 ({rps5_strong/len(df)*100:.1f}%)")
    print(f"  RPS5 > 95: {rps5_very_strong} 只 ({rps5_very_strong/len(df)*100:.1f}%)")
    
    # === 3. 策略分组分析 ===
    print("\n" + "-" * 80)
    print("3. 策略类型分析")
    print("-" * 80)
    
    # 简化策略分类
    df['strategy_simple'] = df['strategy'].apply(lambda x: 
        'XG1+双线红' if 'XG1' in x and 'SXHCG' in x
        else 'XG1创新高' if 'XG1' in x
        else 'XG3次强势' if 'XG3' in x
        else 'XG4低回撤' if 'XG4' in x
        else '双线红' if 'SXHCG' in x
        else 'XG2强势'
    )
    
    print("\n策略分布:")
    strategy_counts = df['strategy_simple'].value_counts()
    for strategy, count in strategy_counts.items():
        pct = count / len(df) * 100
        print(f"  {strategy:15s}: {count:2d} 只 ({pct:5.1f}%)")
    
    # === 4. 价格分布分析 ===
    print("\n" + "-" * 80)
    print("4. 价格分布分析")
    print("-" * 80)
    
    price_groups = [
        ("低价股(<10元)", df['price'] < 10),
        ("中低价(10-30元)", (df['price'] >= 10) & (df['price'] < 30)),
        ("中价股(30-50元)", (df['price'] >= 30) & (df['price'] < 50)),
        ("中高价(50-100元)", (df['price'] >= 50) & (df['price'] < 100)),
        ("高价股(>100元)", df['price'] >= 100),
    ]
    
    print("\n价格分组:")
    for label, condition in price_groups:
        count = condition.sum()
        pct = count / len(df) * 100
        avg_rps = df[condition]['rps_sum'].mean() if count > 0 else 0
        print(f"  {label:15s}: {count:2d} 只 ({pct:5.1f}%) - 平均RPS和: {avg_rps:.1f}")
    
    # === 5. 风险评估 ===
    print("\n" + "-" * 80)
    print("5. 风险评估")
    print("-" * 80)
    
    # 创新高股票（风险最低）
    new_high = df[df['max_dd_120'] == 0]
    print(f"\n创新高股票（回撤=0%）:")
    print(f"  数量: {len(new_high)} 只 ({len(new_high)/len(df)*100:.1f}%)")
    print(f"  平均RPS和: {new_high['rps_sum'].mean():.1f}")
    print(f"  平均价格: {new_high['price'].mean():.2f} 元")
    
    # 低回撤股票
    low_dd = df[(df['max_dd_120'] > 0) & (df['max_dd_120'] < 20)]
    print(f"\n低回撤股票（0-20%）:")
    print(f"  数量: {len(low_dd)} 只 ({len(low_dd)/len(df)*100:.1f}%)")
    print(f"  平均回撤: {low_dd['max_dd_120'].mean():.2f}%")
    print(f"  平均RPS和: {low_dd['rps_sum'].mean():.1f}")
    
    # 中等回撤
    mid_dd = df[(df['max_dd_120'] >= 20) & (df['max_dd_120'] < 30)]
    print(f"\n中等回撤股票（20-30%）:")
    print(f"  数量: {len(mid_dd)} 只 ({len(mid_dd)/len(df)*100:.1f}%)")
    print(f"  平均回撤: {mid_dd['max_dd_120'].mean():.2f}%")
    print(f"  平均RPS和: {mid_dd['rps_sum'].mean():.1f}")
    
    # 高回撤
    high_dd = df[df['max_dd_120'] >= 30]
    print(f"\n高回撤股票（>30%）:")
    print(f"  数量: {len(high_dd)} 只 ({len(high_dd)/len(df)*100:.1f}%)")
    print(f"  平均回撤: {high_dd['max_dd_120'].mean():.2f}%")
    print(f"  平均RPS和: {high_dd['rps_sum'].mean():.1f}")
    
    # === 6. 综合评分和推荐 ===
    print("\n" + "-" * 80)
    print("6. 综合评分和推荐")
    print("-" * 80)
    
    # 计算综合评分
    # 评分因素：RPS和（权重50%）、回撤（权重30%）、短期RPS5（权重20%）
    df['score'] = (
        df['rps_sum'] / 200 * 50 +  # RPS和归一化到0-50分
        (100 - df['max_dd_120']) / 100 * 30 +  # 回撤越小分数越高，0-30分
        df['rps_5'] / 100 * 20  # RPS5归一化到0-20分
    )
    
    # 排序
    df_sorted = df.sort_values('score', ascending=False)
    
    print("\nTop 15 推荐股票（按综合评分）:")
    print()
    print(f"{'排名':^4s} {'代码':^12s} {'名称':^10s} {'价格':^8s} {'RPS和':^8s} {'回撤%':^8s} {'评分':^6s}")
    print("-" * 100)
    
    for idx, row in df_sorted.head(15).iterrows():
        name = row['name'][:8] if len(row['name']) > 8 else row['name']  # 名称最长显示8个字符
        print(f"{idx+1:^4d} {row['symbol']:^12s} {name:^10s} {row['price']:>7.2f} "
              f"{row['rps_sum']:>7.1f} {row['max_dd_120']:>7.1f} "
              f"{row['score']:>5.1f}")
    
    # === 7. 细分推荐 ===
    print("\n" + "-" * 80)
    print("7. 细分推荐")
    print("-" * 80)
    
    # 最强势股票（RPS和>195）
    print("\n⭐ 最强势股票（RPS和>195）:")
    ultra_strong = df_sorted[df_sorted['rps_sum'] > 195].head(5)
    for _, row in ultra_strong.iterrows():
        print(f"  {row['symbol']:12s} {row['name']:<8s} {row['price']:>7.2f}元 "
              f"RPS和:{row['rps_sum']:>6.1f} 回撤:{row['max_dd_120']:>5.1f}% "
              f"{row['strategy_simple']}")
    
    # 创新高股票
    print("\n⭐ 创新高股票（回撤=0%）:")
    new_high_sorted = df_sorted[df_sorted['max_dd_120'] == 0].head(5)
    for _, row in new_high_sorted.iterrows():
        print(f"  {row['symbol']:12s} {row['name']:<8s} {row['price']:>7.2f}元 "
              f"RPS和:{row['rps_sum']:>6.1f} RPS5:{row['rps_5']:>5.1f} "
              f"{row['strategy_simple']}")
    
    # 低价潜力股
    print("\n⭐ 低价潜力股（<15元且RPS和>185）:")
    low_price = df_sorted[(df_sorted['price'] < 15) & (df_sorted['rps_sum'] > 185)].head(5)
    for _, row in low_price.iterrows():
        print(f"  {row['symbol']:12s} {row['name']:<8s} {row['price']:>7.2f}元 "
              f"RPS和:{row['rps_sum']:>6.1f} 回撤:{row['max_dd_120']:>5.1f}% "
              f"{row['strategy_simple']}")
    
    # === 8. 行业分布（如果有） ===
    print("\n" + "-" * 80)
    print("8. 交易所分布")
    print("-" * 80)
    
    df['exchange'] = df['symbol'].apply(lambda x: 'SSE上交所' if 'SSE' in x else 'SZSE深交所')
    exchange_counts = df['exchange'].value_counts()
    print()
    for exchange, count in exchange_counts.items():
        pct = count / len(df) * 100
        print(f"  {exchange:12s}: {count:2d} 只 ({pct:5.1f}%)")
    
    # === 9. 关键发现和建议 ===
    print("\n" + "=" * 80)
    print("关键发现和投资建议")
    print("=" * 80)
    
    print("\n✅ 关键发现:")
    print(f"  1. 筛选出{len(df)}只优质股票，平均RPS和{df['rps_sum'].mean():.1f}")
    print(f"  2. {len(new_high)}只创新高股票（{len(new_high)/len(df)*100:.0f}%），风险最低")
    print(f"  3. {len(df[df['rps_sum']>190])}只股票RPS和>190，属于极强势")
    print(f"  4. 平均回撤{df['max_dd_120'].mean():.1f}%，整体风险可控")
    
    # 短期动能分析
    strong_momentum = (df['rps_5'] > 90).sum()
    print(f"  5. {strong_momentum}只股票短期RPS5>90，短期动能强")
    
    print("\n💡 投资建议:")
    print("  优先级1: 创新高+双线红（最高优先级）")
    print("  优先级2: 创新高+XG1（次优先级）")
    print("  优先级3: 低回撤+XG4（稳健型）")
    print("  优先级4: 次强势+XG3（潜力型）")
    
    print("\n⚠️ 风险提示:")
    print(f"  1. 市场筛选通过率极低（0.79%），市场环境偏弱")
    print(f"  2. 建议控制总仓位≤50%，单只≤10%")
    print(f"  3. 严格执行止损（-5%）")
    print(f"  4. {len(high_dd)}只股票回撤>30%，需谨慎对待")
    
    # 保存分析结果
    output_file = csv_file.replace('.csv', '_analysis.csv')
    df_sorted[['symbol', 'price', 'rps_5', 'rps_50', 'rps_120', 'rps_250', 
               'rps_sum', 'max_dd_120', 'strategy_simple', 'score']].to_csv(
        output_file, index=False, encoding='utf-8-sig'
    )
    print(f"\n✅ 分析结果已保存: {output_file}")


if __name__ == "__main__":
    import glob
    
    # 查找最新的筛选结果（排除分析结果文件）
    pattern = os.path.expanduser("~/.vntrader/train_daily_advanced_*.csv")
    files = glob.glob(pattern)
    
    # 排除分析结果文件
    files = [f for f in files if '_analysis.csv' not in f]
    
    if files:
        latest_file = max(files, key=os.path.getmtime)
        analyze_stocks(latest_file)
    else:
        print("未找到筛选结果文件")
