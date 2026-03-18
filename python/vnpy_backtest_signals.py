#!/usr/bin/env python3
"""
使用VNPy回测引擎回测策略筛选结果

功能：
1. 读取策略筛选的股票列表
2. 使用VNPy BacktestingEngine进行回测
3. 生成专业的回测报告
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

sys.path.insert(0, os.path.expanduser("~"))

from vnpy_ctastrategy import (
    CtaTemplate,
    StopOrder,
    BarGenerator,
    ArrayManager,
)
from vnpy_ctastrategy.backtesting import BacktestingEngine
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.object import TickData, BarData, TradeData, OrderData


class SignalFollowStrategy(CtaTemplate):
    """
    信号跟随策略
    
    根据筛选信号买入，持仓N天后卖出
    """
    
    author = "Strategy Analyzer"
    
    # 策略参数
    holding_days = 1  # 持仓天数
    
    # 策略变量
    entry_bar_count = 0  # 买入后经过的K线数
    
    parameters = ["holding_days"]
    variables = ["entry_bar_count"]
    
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()
        
        self.entry_price = 0
        self.position_opened = False
    
    def on_init(self):
        """初始化"""
        self.write_log("策略初始化")
        self.load_bar(10)
    
    def on_start(self):
        """启动"""
        self.write_log("策略启动")
    
    def on_stop(self):
        """停止"""
        self.write_log("策略停止")
    
    def on_bar(self, bar: BarData):
        """K线数据更新"""
        self.am.update_bar(bar)
        if not self.am.inited:
            return
        
        # 如果没有持仓，在第一根K线（次日开盘）买入
        if not self.position_opened and self.pos == 0:
            # 使用开盘价买入
            self.buy(bar.close_price, 1)
            self.entry_price = bar.open_price
            self.position_opened = True
            self.entry_bar_count = 0
        
        # 如果有持仓，计数
        elif self.pos > 0:
            self.entry_bar_count += 1
            
            # 持仓达到指定天数，卖出
            if self.entry_bar_count >= self.holding_days:
                self.sell(bar.close_price, abs(self.pos))
    
    def on_order(self, order: OrderData):
        """委托更新"""
        pass
    
    def on_trade(self, trade: TradeData):
        """成交更新"""
        self.put_event()
    
    def on_stop_order(self, stop_order: StopOrder):
        """停止单更新"""
        pass


class VNPyBacktester:
    """VNPy回测器"""
    
    def __init__(self):
        self.engine = BacktestingEngine()
        self.results = []
    
    def run_backtest_for_signals(
        self,
        csv_file: str,
        start_date: datetime,
        end_date: datetime,
        holding_days: int = 1,
        max_stocks: int = None
    ):
        """
        对筛选结果进行回测
        
        Args:
            csv_file: 筛选结果CSV文件
            start_date: 回测开始日期
            end_date: 回测结束日期
            holding_days: 持仓天数
            max_stocks: 最大回测股票数（测试用）
        """
        print("=" * 80)
        print("VNPy回测引擎 - 策略信号回测")
        print("=" * 80)
        
        # 读取信号
        print(f"\n读取信号文件: {csv_file}")
        df_signals = pd.read_csv(csv_file)
        
        if max_stocks:
            df_signals = df_signals.head(max_stocks)
        
        print(f"信号数量: {len(df_signals)}")
        print(f"回测参数: {start_date.date()} ~ {end_date.date()}, 持仓{holding_days}天")
        
        print("\n开始回测...")
        print("-" * 80)
        
        # 逐个股票回测
        total = len(df_signals)
        success_count = 0
        failed_count = 0
        
        for idx, row in df_signals.iterrows():
            symbol_full = row['symbol']
            
            try:
                # 解析symbol
                symbol, exchange_str = symbol_full.split('.')
                
                # 构造vt_symbol
                vt_symbol = f"{symbol}.{exchange_str}"
                
                # 配置回测引擎（每只股票单独配置）
                self.engine.set_parameters(
                    vt_symbol=vt_symbol,
                    interval=Interval.DAILY,
                    start=start_date,
                    end=end_date,
                    rate=0.0003,  # 手续费率 0.03%
                    slippage=0.01,  # 滑点 1分
                    size=100,  # 每手100股
                    pricetick=0.01,  # 最小价格变动
                    capital=100000,  # 初始资金10万
                )
                
                # 添加策略
                setting = {"holding_days": holding_days}
                self.engine.add_strategy(SignalFollowStrategy, setting)
                
                # 加载数据
                self.engine.load_data()
                
                # 运行回测
                self.engine.run_backtesting()
                
                # 获取结果
                daily_results = self.engine.calculate_result()
                stats = self.engine.calculate_statistics()
                
                # 保存结果
                if stats:
                    result = {
                        'symbol': symbol_full,
                        'entry_price': row['price'],
                        'total_return': stats['total_return'],
                        'annual_return': stats['return'],
                        'max_drawdown': stats['max_drawdown'],
                        'sharpe_ratio': stats['sharpe_ratio'],
                        'total_trades': stats['total_trade_count'],
                        'win_rate': stats['winning_rate'],
                        'strategy': row.get('strategy', ''),
                    }
                    
                    self.results.append(result)
                    success_count += 1
                    
                    if (idx + 1) % 10 == 0:
                        print(f"进度: {idx+1}/{total} ({(idx+1)/total*100:.1f}%) - 成功:{success_count}, 失败:{failed_count}")
                
                # 清理策略
                self.engine.clear_data()
            
            except Exception as e:
                failed_count += 1
                if failed_count <= 5:  # 只显示前5个错误
                    print(f"  ⚠️  {symbol_full}: {str(e)[:50]}")
        
        print(f"\n✅ 回测完成: 成功{success_count}只, 失败{failed_count}只")
        
        # 生成报告
        if self.results:
            self.generate_report()
        else:
            print("\n❌ 没有回测结果")
    
    def generate_report(self):
        """生成回测报告"""
        df = pd.DataFrame(self.results)
        
        print("\n" + "=" * 80)
        print("VNPy回测报告")
        print("=" * 80)
        
        print(f"\n有效样本: {len(df)}只")
        
        # 总体统计
        print("\n" + "-" * 80)
        print("总体表现")
        print("-" * 80)
        
        print(f"平均收益率: {df['total_return'].mean():.2f}%")
        print(f"平均年化收益: {df['annual_return'].mean():.2f}%")
        print(f"平均最大回撤: {df['max_drawdown'].mean():.2f}%")
        print(f"平均夏普比率: {df['sharpe_ratio'].mean():.2f}")
        print(f"平均胜率: {df['win_rate'].mean():.2f}%")
        
        # 最佳案例
        print("\n" + "-" * 80)
        print("最佳案例 Top 10")
        print("-" * 80)
        
        best = df.nlargest(10, 'total_return')
        print(best[['symbol', 'total_return', 'max_drawdown', 'win_rate', 'strategy']].to_string(index=False))
        
        # 最差案例
        print("\n" + "-" * 80)
        print("最差案例 Top 10")
        print("-" * 80)
        
        worst = df.nsmallest(10, 'total_return')
        print(worst[['symbol', 'total_return', 'max_drawdown', 'win_rate', 'strategy']].to_string(index=False))
        
        # 保存结果
        output_file = os.path.expanduser(f"~/.vntrader/vnpy_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n✅ 详细结果已保存: {output_file}")


def main():
    """主函数"""
    import argparse
    import glob
    import re
    
    parser = argparse.ArgumentParser(description='VNPy回测策略信号')
    parser.add_argument('--days', type=int, default=5, help='持仓天数')
    parser.add_argument('--max', type=int, help='最大回测股票数')
    parser.add_argument('--file', '-f', help='指定CSV文件')
    
    args = parser.parse_args()
    
    print("\n🔄 VNPy专业回测引擎")
    print("=" * 80)
    
    # 查找最新的筛选结果
    if args.file:
        latest_file = os.path.expanduser(args.file)
    else:
        pattern = os.path.expanduser("~/.vntrader/train_daily_advanced_*.csv")
        files = glob.glob(pattern)
        
        if not files:
            print(f"❌ 未找到筛选结果文件")
            return
        
        latest_file = max(files, key=os.path.getmtime)
    
    print(f"使用文件: {os.path.basename(latest_file)}")
    
    # 从文件名提取信号日期
    filename = os.path.basename(latest_file)
    date_match = re.search(r'(\d{8})', filename)
    if date_match:
        signal_date = datetime.strptime(date_match.group(1), '%Y%m%d')
    else:
        signal_date = datetime.now() - timedelta(days=1)
    
    # 回测时间范围：从信号日期的次日开始的hold_days+5天
    start_date = signal_date + timedelta(days=1)
    end_date = start_date + timedelta(days=args.days + 10)  # 额外留一些buffer
    
    print(f"信号日期: {signal_date.strftime('%Y-%m-%d')}")
    print(f"回测范围: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print(f"持仓天数: {args.days}")
    
    # 创建回测器
    backtester = VNPyBacktester()
    backtester.run_backtest_for_signals(
        csv_file=latest_file,
        start_date=start_date,
        end_date=end_date,
        holding_days=args.days,
        max_stocks=args.max
    )


if __name__ == "__main__":
    main()
