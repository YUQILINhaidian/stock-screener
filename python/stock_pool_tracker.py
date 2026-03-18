#!/usr/bin/env python3
"""
股票池管理和价格跟踪系统

功能：
1. 创建和管理股票池
2. 跟踪股票池价格变化
3. 计算收益率和排名
4. 生成跟踪报告
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

sys.path.insert(0, os.path.expanduser("~"))

from vnpy.trader.database import get_database
from vnpy.trader.constant import Exchange, Interval


class StockPool:
    """股票池管理类"""
    
    def __init__(self, pool_name: str = "default"):
        """
        初始化股票池
        
        Args:
            pool_name: 股票池名称
        """
        self.pool_name = pool_name
        self.pool_dir = os.path.expanduser("~/.vntrader/stock_pools")
        os.makedirs(self.pool_dir, exist_ok=True)
        
        self.pool_file = os.path.join(self.pool_dir, f"{pool_name}.json")
        self.history_file = os.path.join(self.pool_dir, f"{pool_name}_history.csv")
        
        self.db = get_database()
        self.pool_data = self.load_pool()
    
    def load_pool(self) -> dict:
        """加载股票池数据"""
        if os.path.exists(self.pool_file):
            with open(self.pool_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'name': self.pool_name,
            'created_at': datetime.now().isoformat(),
            'stocks': {}
        }
    
    def save_pool(self):
        """保存股票池数据"""
        with open(self.pool_file, 'w', encoding='utf-8') as f:
            json.dump(self.pool_data, f, indent=2, ensure_ascii=False)
    
    def create_from_csv(self, csv_file: str, description: str = ""):
        """
        从CSV文件创建股票池
        
        Args:
            csv_file: CSV文件路径
            description: 股票池描述
        """
        print(f"从 {csv_file} 创建股票池...")
        
        df = pd.read_csv(csv_file)
        
        self.pool_data['description'] = description
        self.pool_data['created_at'] = datetime.now().isoformat()
        self.pool_data['source_file'] = csv_file
        
        for _, row in df.iterrows():
            symbol = row['symbol']
            
            self.pool_data['stocks'][symbol] = {
                'entry_price': float(row['price']),
                'entry_date': datetime.now().strftime('%Y-%m-%d'),
                'rps_120': float(row.get('rps_120', 0)),
                'rps_250': float(row.get('rps_250', 0)),
                'rps_sum': float(row.get('rps_sum', 0)),
                'strategy': row.get('strategy', ''),
                'max_dd_120': float(row.get('max_dd_120', 0)),
            }
        
        self.save_pool()
        print(f"✅ 股票池创建完成: {len(self.pool_data['stocks'])} 只股票")
    
    def get_current_prices(self) -> Dict[str, float]:
        """获取所有股票的当前价格"""
        prices = {}
        
        for symbol in self.pool_data['stocks'].keys():
            try:
                # 解析symbol
                code, exchange_str = symbol.split('.')
                exchange = Exchange(exchange_str)
                
                # 获取最新K线
                bars = self.db.load_bar_data(
                    symbol=code,
                    exchange=exchange,
                    interval=Interval.DAILY,
                    start=datetime.now() - timedelta(days=5),
                    end=datetime.now()
                )
                
                if bars:
                    prices[symbol] = bars[-1].close_price
            
            except Exception as e:
                print(f"  ⚠️  {symbol}: 获取价格失败 - {str(e)[:50]}")
                prices[symbol] = None
        
        return prices
    
    def update_prices(self):
        """更新股票池价格并记录历史"""
        print("=" * 80)
        print(f"更新股票池价格: {self.pool_name}")
        print("=" * 80)
        print()
        
        # 获取当前价格
        print("获取当前价格...")
        current_prices = self.get_current_prices()
        
        # 计算收益
        results = []
        today = datetime.now().strftime('%Y-%m-%d')
        
        for symbol, stock_info in self.pool_data['stocks'].items():
            entry_price = stock_info['entry_price']
            current_price = current_prices.get(symbol)
            
            if current_price:
                change = current_price - entry_price
                change_pct = (change / entry_price) * 100
                
                results.append({
                    'date': today,
                    'symbol': symbol,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'change': change,
                    'change_pct': change_pct,
                    'rps_sum': stock_info.get('rps_sum', 0),
                    'strategy': stock_info.get('strategy', '')
                })
        
        # 保存到历史记录
        df_new = pd.DataFrame(results)
        
        if os.path.exists(self.history_file):
            df_old = pd.read_csv(self.history_file)
            # 删除今天的旧记录（如果有）
            df_old = df_old[df_old['date'] != today]
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_combined = df_new
        
        df_combined.to_csv(self.history_file, index=False, encoding='utf-8-sig')
        
        print(f"✅ 价格更新完成: {len(results)} 只股票")
        print(f"✅ 历史记录已保存: {self.history_file}")
        
        return df_new
    
    def show_performance(self, top_n: int = 10):
        """显示股票池表现"""
        if not os.path.exists(self.history_file):
            print("❌ 还没有历史记录，请先运行 update_prices()")
            return
        
        df = pd.read_csv(self.history_file)
        
        # 获取最新日期的数据
        latest_date = df['date'].max()
        df_latest = df[df['date'] == latest_date].copy()
        
        print("=" * 80)
        print(f"股票池表现报告: {self.pool_name}")
        print("=" * 80)
        print(f"更新日期: {latest_date}")
        print(f"股票数量: {len(df_latest)}")
        print()
        
        # 整体统计
        print("-" * 80)
        print("整体表现")
        print("-" * 80)
        
        avg_change = df_latest['change_pct'].mean()
        median_change = df_latest['change_pct'].median()
        max_gain = df_latest['change_pct'].max()
        max_loss = df_latest['change_pct'].min()
        
        positive_count = (df_latest['change_pct'] > 0).sum()
        win_rate = positive_count / len(df_latest) * 100
        
        print(f"平均涨跌: {avg_change:>7.2f}%")
        print(f"中位数:   {median_change:>7.2f}%")
        print(f"最大涨幅: {max_gain:>7.2f}%")
        print(f"最大跌幅: {max_loss:>7.2f}%")
        print(f"上涨数量: {positive_count}/{len(df_latest)} ({win_rate:.1f}%)")
        
        # Top涨幅
        print("\n" + "-" * 80)
        print(f"涨幅Top {top_n}")
        print("-" * 80)
        
        df_sorted = df_latest.sort_values('change_pct', ascending=False)
        
        print(f"{'排名':^4s} {'代码':^12s} {'买入价':^8s} {'当前价':^8s} "
              f"{'涨跌':^8s} {'涨跌%':^8s} {'RPS和':^8s}")
        print("-" * 80)
        
        for idx, (_, row) in enumerate(df_sorted.head(top_n).iterrows(), 1):
            print(f"{idx:^4d} {row['symbol']:^12s} {row['entry_price']:>7.2f} "
                  f"{row['current_price']:>7.2f} {row['change']:>7.2f} "
                  f"{row['change_pct']:>7.2f}% {row['rps_sum']:>7.1f}")
        
        # Top跌幅
        print("\n" + "-" * 80)
        print(f"跌幅Top {top_n}")
        print("-" * 80)
        
        print(f"{'排名':^4s} {'代码':^12s} {'买入价':^8s} {'当前价':^8s} "
              f"{'涨跌':^8s} {'涨跌%':^8s} {'RPS和':^8s}")
        print("-" * 80)
        
        for idx, (_, row) in enumerate(df_sorted.tail(top_n).iterrows(), 1):
            print(f"{idx:^4d} {row['symbol']:^12s} {row['entry_price']:>7.2f} "
                  f"{row['current_price']:>7.2f} {row['change']:>7.2f} "
                  f"{row['change_pct']:>7.2f}% {row['rps_sum']:>7.1f}")
    
    def generate_report(self):
        """生成详细报告"""
        if not os.path.exists(self.history_file):
            print("❌ 还没有历史记录")
            return
        
        df = pd.read_csv(self.history_file)
        latest_date = df['date'].max()
        df_latest = df[df['date'] == latest_date].copy()
        
        # 生成Markdown报告
        report_file = os.path.join(self.pool_dir, f"{self.pool_name}_report_{latest_date}.md")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# 股票池跟踪报告: {self.pool_name}\n\n")
            f.write(f"**更新日期**: {latest_date}\n\n")
            f.write(f"**股票数量**: {len(df_latest)}只\n\n")
            
            # 整体表现
            f.write("## 整体表现\n\n")
            avg_change = df_latest['change_pct'].mean()
            win_rate = (df_latest['change_pct'] > 0).sum() / len(df_latest) * 100
            
            f.write(f"- 平均涨跌: **{avg_change:.2f}%**\n")
            f.write(f"- 上涨比例: **{win_rate:.1f}%**\n")
            f.write(f"- 最大涨幅: **{df_latest['change_pct'].max():.2f}%**\n")
            f.write(f"- 最大跌幅: **{df_latest['change_pct'].min():.2f}%**\n\n")
            
            # 涨幅榜
            f.write("## 涨幅Top 10\n\n")
            f.write("| 排名 | 代码 | 买入价 | 当前价 | 涨跌幅 | RPS和 | 策略 |\n")
            f.write("|------|------|--------|--------|--------|-------|------|\n")
            
            df_sorted = df_latest.sort_values('change_pct', ascending=False)
            for idx, (_, row) in enumerate(df_sorted.head(10).iterrows(), 1):
                f.write(f"| {idx} | {row['symbol']} | {row['entry_price']:.2f} | "
                       f"{row['current_price']:.2f} | **{row['change_pct']:.2f}%** | "
                       f"{row['rps_sum']:.1f} | {row['strategy'][:20]} |\n")
            
            # 跌幅榜
            f.write("\n## 跌幅Top 10\n\n")
            f.write("| 排名 | 代码 | 买入价 | 当前价 | 涨跌幅 | RPS和 | 策略 |\n")
            f.write("|------|------|--------|--------|--------|-------|------|\n")
            
            for idx, (_, row) in enumerate(df_sorted.tail(10).iterrows(), 1):
                f.write(f"| {idx} | {row['symbol']} | {row['entry_price']:.2f} | "
                       f"{row['current_price']:.2f} | **{row['change_pct']:.2f}%** | "
                       f"{row['rps_sum']:.1f} | {row['strategy'][:20]} |\n")
        
        print(f"✅ 报告已生成: {report_file}")
        return report_file


def main():
    """主函数"""
    import argparse
    import glob
    
    parser = argparse.ArgumentParser(description='股票池管理')
    parser.add_argument('action', choices=['create', 'update', 'show', 'report'],
                       help='操作: create-创建, update-更新价格, show-显示表现, report-生成报告')
    parser.add_argument('--name', default='train_pool_20260304',
                       help='股票池名称')
    parser.add_argument('--csv', help='CSV文件路径（create时使用）')
    parser.add_argument('--desc', help='股票池描述')
    
    args = parser.parse_args()
    
    pool = StockPool(args.name)
    
    if args.action == 'create':
        if not args.csv:
            # 自动查找最新的筛选结果
            pattern = os.path.expanduser("~/.vntrader/train_daily_advanced_*.csv")
            files = glob.glob(pattern)
            if files:
                args.csv = max(files, key=os.path.getmtime)
                print(f"使用最新筛选结果: {os.path.basename(args.csv)}")
            else:
                print("❌ 请指定CSV文件或确保有筛选结果")
                return
        
        desc = args.desc or f"火车头策略筛选 - {datetime.now().strftime('%Y-%m-%d')}"
        pool.create_from_csv(args.csv, desc)
        print(f"\n股票池已创建: {pool.pool_file}")
        print(f"使用 'python3 {__file__} update --name {args.name}' 更新价格")
    
    elif args.action == 'update':
        df = pool.update_prices()
        print(f"\n更新完成，共 {len(df)} 只股票")
        pool.show_performance()
    
    elif args.action == 'show':
        pool.show_performance()
    
    elif args.action == 'report':
        report_file = pool.generate_report()
        print(f"\n可以使用以下命令查看报告:")
        print(f"  cat {report_file}")


if __name__ == "__main__":
    main()
