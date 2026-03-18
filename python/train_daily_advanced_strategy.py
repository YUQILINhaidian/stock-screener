#!/usr/bin/env python3
"""
火车每日观察选股策略（Python实现）

基于陶博士2006的火车每日观察选股公式
包含两个主要策略：
1. MRGC（美人国策略）
2. SXHCG（双线红策略）

参考资料：https://mp.weixin.qq.com/s/e_HKy7tPJ96QWcFvBr-zJQ
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.expanduser("~"))

from vnpy.trader.database import get_database
from vnpy.trader.constant import Exchange, Interval
from train_daily_strategy import TrainDailyStrategy
from turnover_rate_manager import get_turnover_manager


class TrainDailyAdvancedStrategy(TrainDailyStrategy):
    """火车每日观察高级选股策略"""
    
    def __init__(self):
        super().__init__()
        self.ma_data = {}  # 存储均线数据
        # 加载换手率数据
        self.turnover_manager = get_turnover_manager()
    
    def calculate_ma(self, symbol: str, period: int) -> pd.Series:
        """
        计算移动平均线
        
        Args:
            symbol: 股票代码
            period: 均线周期
        
        Returns:
            均线序列
        """
        if symbol not in self.all_bars:
            return pd.Series()
        
        df = self.all_bars[symbol]
        return df['close'].rolling(window=period).mean()
    
    def calculate_max_drawdown(self, symbol: str, period: int) -> float:
        """
        计算指定周期内的最大回撤
        
        Args:
            symbol: 股票代码
            period: 回撤计算周期
        
        Returns:
            最大回撤比例（0-1之间）
        """
        if symbol not in self.all_bars:
            return 1.0
        
        df = self.all_bars[symbol].tail(period)
        if len(df) == 0:
            return 1.0
        
        # 找到期间内的最高点
        high_idx = df['high'].idxmax()
        high_price = df.loc[high_idx, 'high']
        
        # 从最高点之后找最低点
        if high_idx == df.index[-1]:
            # 如果最高点就是最后一天，回撤为0
            return 0.0
        
        after_high = df.loc[high_idx:]
        low_price = after_high['low'].min()
        
        # 计算回撤
        drawdown = (high_price - low_price) / high_price
        
        return drawdown
    
    def get_turnover_rate(self, symbol: str) -> float:
        """
        获取最新的换手率（从Baostock数据）
        
        Args:
            symbol: 股票代码
        
        Returns:
            换手率（%）
        """
        # 从Baostock获取的换手率数据
        return self.turnover_manager.get_turnover_rate_or_default(symbol, default=100.0)
    
    def check_mrgc_strategy(self, symbol: str, date_idx: int) -> Tuple[bool, str]:
        """
        检查MRGC（美人国）策略条件
        
        Args:
            symbol: 股票代码
            date_idx: 日期索引
        
        Returns:
            (是否符合, 符合的子条件)
        """
        if symbol not in self.all_bars:
            return False, ""
        
        df = self.all_bars[symbol]
        if date_idx >= len(df):
            return False, ""
        
        current_close = df.iloc[date_idx]['close']
        
        # MRGC00: 换手率 < 25%
        turnover = self.get_turnover_rate(symbol)
        if turnover >= 25:
            return False, ""
        
        # MRGC001: 120天最大回撤 ≤ 50%
        max_dd_120 = self.calculate_max_drawdown(symbol, 120)
        if max_dd_120 > 0.5:
            return False, ""
        
        # MRGC002: 收盘价 > 250天最高价的70%
        hhv_250 = df.iloc[max(0, date_idx-250):date_idx+1]['close'].max()
        if current_close / hhv_250 <= 0.7:
            return False, ""
        
        # 获取RPS值
        rps_120 = self.get_rps_for_stock(symbol, 120, date_idx)
        rps_250 = self.get_rps_for_stock(symbol, 250, date_idx)
        rps_50 = self.get_rps_for_stock(symbol, 50, date_idx)
        
        if rps_120 is None or rps_250 is None:
            return False, ""
        
        # 检查四个子条件
        
        # XG1: 近5天创250天新高 + RPS条件
        recent_5 = df.iloc[max(0, date_idx-4):date_idx+1]
        hhv_250_close = df.iloc[max(0, date_idx-250):date_idx+1]['close'].max()
        xg11 = (recent_5['close'] == hhv_250_close).any()
        xg12 = (rps_120 > 96) or (rps_250 > 96)
        xg13 = (rps_120 > 95) and (rps_50 is not None and rps_50 > 95)
        xg1 = xg11 and (xg12 or xg13)
        
        # XG2: 收盘价 > 250天最高价的85% + (RPS120>97 或 RPS250>97)
        hhv_250_high = df.iloc[max(0, date_idx-250):date_idx+1]['high'].max()
        xg21 = current_close / hhv_250_high >= 0.85
        xg22 = (rps_120 > 97) or (rps_250 > 97)
        xg2 = xg21 and xg22
        
        # XG3: 收盘价 > 250天最高价的70% + (RPS120>98 或 RPS250>98)
        xg31 = current_close / hhv_250_high >= 0.70
        xg32 = (rps_120 > 98) or (rps_250 > 98)
        xg3 = xg31 and xg32
        
        # XG4: 120天最大回撤≤35% 且 收盘价>250天最高价的80% + RPS条件
        max_dd_35 = max_dd_120 <= 0.35
        price_80 = current_close / hhv_250_close > 0.8
        xg41 = max_dd_35 and price_80
        xg42 = (rps_120 > 95) or (rps_250 > 95)
        xg4 = xg41 and xg42
        
        # 满足任一子条件即可
        if xg1:
            return True, "XG1(创新高+高RPS)"
        elif xg2:
            return True, "XG2(强势+超高RPS)"
        elif xg3:
            return True, "XG3(次强势+极高RPS)"
        elif xg4:
            return True, "XG4(低回撤+高位+高RPS)"
        else:
            return False, ""
    
    def check_sxhcg_strategy(self, symbol: str, date_idx: int) -> Tuple[bool, str]:
        """
        检查SXHCG（双线红）策略条件
        
        Args:
            symbol: 股票代码
            date_idx: 日期索引
        
        Returns:
            (是否符合, 详细信息)
        """
        if symbol not in self.all_bars:
            return False, ""
        
        df = self.all_bars[symbol]
        if date_idx >= len(df) or date_idx < 250:
            return False, ""
        
        current_close = df.iloc[date_idx]['close']
        
        # 获取RPS值
        rps_120 = self.get_rps_for_stock(symbol, 120, date_idx)
        rps_250 = self.get_rps_for_stock(symbol, 250, date_idx)
        
        if rps_120 is None or rps_250 is None:
            return False, ""
        
        # SXHCG1: RPS120 + RPS250 > 185
        if rps_120 + rps_250 <= 185:
            return False, ""
        
        # 计算均线
        ma_10 = df.iloc[:date_idx+1]['close'].rolling(10).mean()
        ma_20 = df.iloc[:date_idx+1]['close'].rolling(20).mean()
        ma_200 = df.iloc[:date_idx+1]['close'].rolling(200).mean()
        ma_250 = df.iloc[:date_idx+1]['close'].rolling(250).mean()
        
        # SXHCG20: 收盘价站上20日线
        if current_close <= ma_20.iloc[date_idx]:
            return False, ""
        
        # SXHCG21: 过去30天至少25天收盘价高于250日线
        recent_30 = df.iloc[max(0, date_idx-29):date_idx+1]
        ma_250_recent = ma_250.iloc[max(0, date_idx-29):date_idx+1]
        above_ma250_days = (recent_30['close'].values > ma_250_recent.values).sum()
        if above_ma250_days < 25:
            return False, ""
        
        # SXHCG22: 过去30天至少25天收盘价高于200日线
        ma_200_recent = ma_200.iloc[max(0, date_idx-29):date_idx+1]
        above_ma200_days = (recent_30['close'].values > ma_200_recent.values).sum()
        if above_ma200_days < 25:
            return False, ""
        
        # SXHCG23或SXHCG24
        recent_10 = df.iloc[max(0, date_idx-9):date_idx+1]
        ma_20_recent_10 = ma_20.iloc[max(0, date_idx-9):date_idx+1]
        above_ma20_10days = (recent_10['close'].values > ma_20_recent_10.values).sum()
        sxhcg23 = above_ma20_10days >= 9
        
        recent_4 = df.iloc[max(0, date_idx-3):date_idx+1]
        ma_10_recent_4 = ma_10.iloc[max(0, date_idx-3):date_idx+1]
        ma_20_recent_4 = ma_20.iloc[max(0, date_idx-3):date_idx+1]
        above_ma10_4days = (recent_4['close'].values > ma_10_recent_4.values).sum()
        above_ma20_4days = (recent_4['close'].values > ma_20_recent_4.values).sum()
        sxhcg24 = (above_ma10_4days >= 3) and (above_ma20_4days >= 3)
        
        if not (sxhcg23 or sxhcg24):
            return False, ""
        
        # SXHCG3: 20天最大回撤 ≤ 25% 且 收盘价 > 250天最高价的80%
        max_dd_20 = self.calculate_max_drawdown(symbol, 20)
        hhv_250 = df.iloc[max(0, date_idx-250):date_idx+1]['close'].max()
        if max_dd_20 > 0.25 or current_close / hhv_250 <= 0.8:
            return False, ""
        
        # SXHCG4: 均线上升
        ma_10_curr = ma_10.iloc[date_idx]
        ma_10_prev = ma_10.iloc[date_idx-1] if date_idx > 0 else ma_10_curr
        ma_20_curr = ma_20.iloc[date_idx]
        ma_20_prev = ma_20.iloc[date_idx-1] if date_idx > 0 else ma_20_curr
        
        sxhcg421 = ma_10_curr >= ma_10_prev  # 10日线向上
        sxhcg422 = ma_20_curr >= ma_20_prev  # 20日线向上
        sxhcg423 = ma_10_curr >= ma_20_curr  # 10日线在20日线上方
        
        if not (sxhcg421 and sxhcg422 and sxhcg423):
            return False, ""
        
        # SXHCG5: 换手率 < 15%
        turnover = self.get_turnover_rate(symbol)
        if turnover >= 15:
            return False, ""
        
        # SXHCG6: 120天最大回撤 ≤ 50%
        max_dd_120 = self.calculate_max_drawdown(symbol, 120)
        if max_dd_120 > 0.5:
            return False, ""
        
        return True, f"双线红(RPS和={rps_120+rps_250:.1f})"
    
    def screen_stocks(self, date_idx: int = -1) -> pd.DataFrame:
        """
        筛选符合火车每日观察策略的股票
        
        Args:
            date_idx: 日期索引，-1表示最新
        
        Returns:
            符合条件的股票DataFrame
        """
        results = []
        
        print(f"\n开始筛选（日期索引: {date_idx}）...")
        print("=" * 80)
        
        for symbol in self.all_bars.keys():
            # 获取实际的date_idx
            actual_idx = date_idx if date_idx >= 0 else len(self.all_bars[symbol]) - 1
            
            if actual_idx < 250:  # 至少需要250天数据
                continue
            
            # 检查MRGC策略
            mrgc_pass, mrgc_detail = self.check_mrgc_strategy(symbol, actual_idx)
            
            # 检查SXHCG策略
            sxhcg_pass, sxhcg_detail = self.check_sxhcg_strategy(symbol, actual_idx)
            
            if mrgc_pass or sxhcg_pass:
                df = self.all_bars[symbol]
                current_price = df.iloc[actual_idx]['close']
                
                # 获取RPS值
                rps_5 = self.get_rps_for_stock(symbol, 5, actual_idx) or 0
                rps_10 = self.get_rps_for_stock(symbol, 10, actual_idx) or 0
                rps_50 = self.get_rps_for_stock(symbol, 50, actual_idx) or 0
                rps_120 = self.get_rps_for_stock(symbol, 120, actual_idx) or 0
                rps_250 = self.get_rps_for_stock(symbol, 250, actual_idx) or 0
                
                # 确定策略类型
                strategy = []
                if mrgc_pass:
                    strategy.append(f"MRGC-{mrgc_detail}")
                if sxhcg_pass:
                    strategy.append(f"SXHCG-{sxhcg_detail}")
                
                results.append({
                    'symbol': symbol,
                    'price': current_price,
                    'rps_5': rps_5,
                    'rps_10': rps_10,
                    'rps_50': rps_50,
                    'rps_120': rps_120,
                    'rps_250': rps_250,
                    'rps_sum': rps_120 + rps_250,
                    'strategy': ' | '.join(strategy),
                    'max_dd_120': self.calculate_max_drawdown(symbol, 120) * 100
                })
        
        if not results:
            print("未找到符合条件的股票")
            return pd.DataFrame()
        
        result_df = pd.DataFrame(results)
        result_df = result_df.sort_values('rps_sum', ascending=False)
        
        print(f"\n找到 {len(result_df)} 只符合条件的股票")
        print("=" * 80)
        
        return result_df


def main():
    """主函数"""
    print("=" * 80)
    print("火车每日观察选股策略（Python版）")
    print("=" * 80)
    
    strategy = TrainDailyAdvancedStrategy()
    
    # 加载数据
    print("\n1. 加载K线数据...")
    strategy.load_data()
    
    # 预计算RPS
    print("\n2. 预计算RPS值...")
    strategy.precalculate_all_rps()
    
    # 筛选股票
    print("\n3. 执行策略筛选...")
    result_df = strategy.screen_stocks()
    
    if not result_df.empty:
        # 显示结果
        print("\n符合条件的股票:")
        print(result_df.to_string(index=False))
        
        # 保存结果
        output_file = os.path.expanduser(
            f"~/.vntrader/train_daily_advanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n结果已保存到: {output_file}")
        
        # 统计
        print("\n" + "=" * 80)
        print("策略分布:")
        print("=" * 80)
        for strategy_name in result_df['strategy'].unique():
            count = (result_df['strategy'] == strategy_name).sum()
            print(f"{strategy_name}: {count} 只")


if __name__ == "__main__":
    main()
