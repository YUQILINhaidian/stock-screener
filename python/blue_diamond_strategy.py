#!/usr/bin/env python3
"""
蓝色钻石选股策略（Python实现）

作者：陶博士2006
策略名称：蓝色钻石公式
参考链接：https://mp.weixin.qq.com/s/nHLgFvvbUvuKGwyNEv3m9w

策略原理：
捕捉强势股第二波上涨的机会
- 第一波上涨快速拉升
- 然后靠近或跌破20日线调整
- 等待右侧口袋支点买入

特点：
- 不要求RPS120和RPS250（与火车头策略不同）
- 只关注RPS20和RPS50（短期强度）
- 适合中期波段操作
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.expanduser("~"))

from vnpy.trader.database import get_database
from vnpy.trader.constant import Exchange, Interval
from train_daily_strategy import TrainDailyStrategy
from turnover_rate_manager import get_turnover_manager


class BlueDiamondStrategy(TrainDailyStrategy):
    """蓝色钻石选股策略"""
    
    def __init__(self):
        super().__init__()
        # 需要计算RPS20（20日RPS）
        self.rps_periods = [5, 10, 20, 50, 120, 250]
        # 加载换手率数据
        self.turnover_manager = get_turnover_manager()
    
    def calculate_rps_20(self, symbol: str, date_idx: int) -> float:
        """
        计算20日RPS
        
        Args:
            symbol: 股票代码
            date_idx: 日期索引
        
        Returns:
            RPS20值（0-100）
        """
        # 如果已经在预计算的RPS中，直接返回
        if hasattr(self, 'rps_20_data') and symbol in self.rps_20_data:
            return self.rps_20_data[symbol][date_idx]
        
        # 否则即时计算
        if symbol not in self.all_bars:
            return 0.0
        
        df = self.all_bars[symbol]
        if date_idx >= len(df) or date_idx < 20:
            return 0.0
        
        # 计算20日收益率
        current_close = df.iloc[date_idx]['close']
        past_20_close = df.iloc[date_idx - 20]['close']
        
        if past_20_close == 0:
            return 0.0
        
        return_20 = (current_close - past_20_close) / past_20_close
        
        # 计算所有股票在同一天的20日收益率
        all_returns = []
        for s in self.all_bars.keys():
            s_df = self.all_bars[s]
            if date_idx < len(s_df) and date_idx >= 20:
                s_current = s_df.iloc[date_idx]['close']
                s_past = s_df.iloc[date_idx - 20]['close']
                if s_past > 0:
                    s_return = (s_current - s_past) / s_past
                    all_returns.append(s_return)
        
        if not all_returns:
            return 0.0
        
        # 计算排名
        rank = sum(1 for r in all_returns if r < return_20)
        rps = (rank / len(all_returns)) * 100
        
        return rps
    
    def calculate_max_drawdown_20(self, symbol: str, date_idx: int) -> float:
        """
        计算20天内的最大回撤
        
        按原始公式逻辑：
        1. 找20天内最高点
        2. 从最高点之后找最低点
        3. 计算回撤
        
        Args:
            symbol: 股票代码
            date_idx: 日期索引
        
        Returns:
            最大回撤比例（0-1）
        """
        if symbol not in self.all_bars:
            return 0.0
        
        df = self.all_bars[symbol]
        
        if date_idx < 20 or date_idx >= len(df):
            return 0.0
        
        # 取最近20天数据
        recent_20 = df.iloc[date_idx-19:date_idx+1]
        
        # ZC新高天数:=HHVBARS(H,20);
        # 找到最高价的位置（从右往左数）
        high_idx_in_window = recent_20['high'].idxmax()
        high_bars = len(recent_20) - recent_20.index.get_loc(high_idx_in_window) - 1
        
        # ZC新低天数:=IF(ZC新高天数=0,0,LLVBARS(L,ZC新高天数));
        if high_bars == 0:
            return 0.0
        
        # 从最高点之后找最低点
        after_high = recent_20.loc[high_idx_in_window:]
        if len(after_high) <= 1:
            return 0.0
        
        low_price = after_high['low'].min()
        high_price = recent_20.loc[high_idx_in_window, 'high']
        
        # ZC回撤幅度:=(ZC新高价-ZC新低价)/ZC新高价;
        drawdown = (high_price - low_price) / high_price if high_price > 0 else 0.0
        
        return drawdown
    
    def check_blue_diamond(self, symbol: str, date_idx: int) -> Tuple[bool, str]:
        """
        检查是否符合蓝色钻石策略
        
        Args:
            symbol: 股票代码
            date_idx: 日期索引
        
        Returns:
            (是否符合, 符合的子条件说明)
        """
        if symbol not in self.all_bars:
            return False, ""
        
        df = self.all_bars[symbol]
        
        if date_idx < 250 or date_idx >= len(df):
            return False, ""
        
        current_close = df.iloc[date_idx]['close']
        
        # 获取RPS值
        rps_50 = self.get_rps_for_stock(symbol, 50, date_idx)
        rps_20 = self.calculate_rps_20(symbol, date_idx)
        
        # 获取均线
        ma_series = {}
        for period in [10, 20, 50, 120, 200, 250]:
            df_copy = self.all_bars[symbol].copy()
            df_copy[f'ma_{period}'] = df_copy['close'].rolling(window=period).mean()
            ma_series[period] = df_copy[f'ma_{period}']
        
        ma_10 = ma_series[10].iloc[date_idx] if date_idx >= 10 else 0
        ma_20 = ma_series[20].iloc[date_idx] if date_idx >= 20 else 0
        ma_50 = ma_series[50].iloc[date_idx] if date_idx >= 50 else 0
        ma_120 = ma_series[120].iloc[date_idx] if date_idx >= 120 else 0
        ma_200 = ma_series[200].iloc[date_idx] if date_idx >= 200 else 0
        ma_250 = ma_series[250].iloc[date_idx] if date_idx >= 250 else 0
        
        # 计算20天最大回撤
        max_dd_20 = self.calculate_max_drawdown_20(symbol, date_idx)
        
        # 获取250天最高价
        recent_250 = df.iloc[max(0, date_idx-249):date_idx+1]
        hhv_250 = recent_250['close'].max()
        
        # 获取换手率（从Baostock数据）
        turnover = self.turnover_manager.get_turnover_rate_or_default(symbol, default=100.0)
        
        # ===== ZCDX00: 基础条件 =====
        # ZCDX0001: 20天最大回撤 <= 25% AND COUNT(回撤>0.25, 新高天数)=0
        # 原始公式：ZCDX0001:=ZC回撤幅度<=0.25 AND COUNT(ZC回撤幅度>0.25,ZC新高天数)=0
        
        # 第一步：计算当前的新高天数和回撤幅度
        highs = df['high'].values
        lows = df['low'].values
        
        # HHVBARS(H,20) - 20天内最高点距今天数
        high_window = highs[max(0, date_idx-19):date_idx+1]
        if len(high_window) > 0:
            max_high_in_window = np.max(high_window)
            # 找到最高点的位置
            new_high_days = 0
            for i in range(len(high_window)-1, -1, -1):
                if high_window[i] == max_high_in_window:
                    new_high_days = len(high_window) - 1 - i
                    break
        else:
            new_high_days = 0
            max_high_in_window = highs[date_idx]
        
        # 计算当前回撤幅度
        if new_high_days == 0:
            # 今天创新高，回撤为0
            current_drawdown = 0.0
        else:
            # 找新高点到当前之间的最低价
            new_high_idx = date_idx - new_high_days
            low_since_new_high = np.min(lows[new_high_idx:date_idx+1])
            if max_high_in_window > 0:
                current_drawdown = (max_high_in_window - low_since_new_high) / max_high_in_window
            else:
                current_drawdown = 1.0
        
        # 条件1：当前回撤 <= 25%
        condition_dd_current = current_drawdown <= 0.25
        
        # 条件2：COUNT(ZC回撤幅度>0.25, ZC新高天数)=0
        # 在过去"新高天数"天内，每天的回撤幅度都不能超过25%
        no_excessive_drawdown = True
        if new_high_days > 0:
            for d in range(1, min(new_high_days, 19) + 1):  # 最多检查20天内
                check_idx = date_idx - d
                if check_idx < 20:  # 需要足够的数据
                    continue
                
                # 计算该天的新高天数
                check_high_window = highs[max(0, check_idx-19):check_idx+1]
                if len(check_high_window) == 0:
                    continue
                check_max_high = np.max(check_high_window)
                
                # 找该天的新高点位置
                check_new_high_days = 0
                for i in range(len(check_high_window)-1, -1, -1):
                    if check_high_window[i] == check_max_high:
                        check_new_high_days = len(check_high_window) - 1 - i
                        break
                
                # 计算该天的回撤幅度
                if check_new_high_days == 0:
                    check_drawdown = 0.0
                else:
                    check_new_high_idx = check_idx - check_new_high_days
                    check_low_since_new_high = np.min(lows[check_new_high_idx:check_idx+1])
                    if check_max_high > 0:
                        check_drawdown = (check_max_high - check_low_since_new_high) / check_max_high
                    else:
                        check_drawdown = 1.0
                
                # 如果任何一天的回撤超过25%，条件不满足
                if check_drawdown > 0.25:
                    no_excessive_drawdown = False
                    break
        
        condition_dd = condition_dd_current and no_excessive_drawdown
        
        # ZCDX0002: 收盘价 > 250天最高价的80%
        condition_position = (current_close / hhv_250 > 0.8) if hhv_250 > 0 else False
        
        zcdx00 = condition_dd and condition_position
        
        if not zcdx00:
            return False, ""
        
        # ===== ZCDX01: RPS条件（满足任一） =====
        # ZCDX011: RPS50 >= 98
        zcdx011 = rps_50 >= 98
        
        # ZCDX012: RPS20 >= 98
        zcdx012 = rps_20 >= 98
        
        # ZCDX013: RPS50 >= 97 且 RPS20+RPS50 >= 190
        zcdx013 = (rps_50 >= 97) and (rps_20 + rps_50 >= 190)
        
        zcdx01 = zcdx011 or zcdx012 or zcdx013
        
        if not zcdx01:
            return False, ""
        
        # ===== ZCDX02: 收盘价靠近20日线 =====
        # C/MA(C,20) < 1.005（收盘价在20日线上方不超过0.5%）
        if ma_20 <= 0:
            return False, ""
        
        zcdx02 = (current_close / ma_20) < 1.005
        
        if not zcdx02:
            return False, ""
        
        # ===== ZCDX03: 均线位置条件 =====
        recent_20 = df.iloc[max(0, date_idx-19):date_idx+1]
        
        # COUNT(C<MA(C,20),20) <= 2
        # 过去20天收盘价低于20日线的天数不超过2天
        ma_20_series_20 = ma_series[20].iloc[max(0, date_idx-19):date_idx+1]
        below_ma20_days = sum(recent_20['close'].values < ma_20_series_20.values)
        
        # COUNT(C<MA(C,10),20) <= 8
        ma_10_series_20 = ma_series[10].iloc[max(0, date_idx-19):date_idx+1]
        below_ma10_days = sum(recent_20['close'].values < ma_10_series_20.values)
        
        # COUNT(L<MA(C,20),20) <= 4 OR RPS50 >= 99
        low_below_ma20_days = sum(recent_20['low'].values < ma_20_series_20.values)
        
        zcdx03 = (below_ma20_days <= 2 and 
                  below_ma10_days <= 8 and 
                  (low_below_ma20_days <= 4 or rps_50 >= 99))
        
        if not zcdx03:
            return False, ""
        
        # ===== ZCDX04: 50日线在长期均线之上 =====
        # MA(C,50) > MA(C,120) AND MA(C,50) > MA(C,200) AND MA(C,50) > MA(C,250)
        zcdx04 = (ma_50 > ma_120 and ma_50 > ma_200 and ma_50 > ma_250)
        
        if not zcdx04:
            return False, ""
        
        # ===== ZCDX05: 换手率 < 10% =====
        zcdx05 = turnover < 10
        
        if not zcdx05:
            return False, ""
        
        # 所有条件都满足
        reason_parts = []
        if zcdx011:
            reason_parts.append(f"RPS50={rps_50:.1f}≥98")
        if zcdx012:
            reason_parts.append(f"RPS20={rps_20:.1f}≥98")
        if zcdx013:
            reason_parts.append(f"RPS50={rps_50:.1f}≥97且和={rps_20+rps_50:.1f}≥190")
        
        reason = " | ".join(reason_parts) if reason_parts else "符合蓝色钻石"
        
        return True, reason
    
    def screen_stocks(self, date_idx: int = -1) -> pd.DataFrame:
        """
        筛选符合蓝色钻石策略的股票
        
        Args:
            date_idx: 日期索引，-1表示最新
        
        Returns:
            符合条件的股票DataFrame
        """
        print("=" * 80)
        print("蓝色钻石策略筛选")
        print("=" * 80)
        
        results = []
        
        for symbol in self.all_bars.keys():
            try:
                df = self.all_bars[symbol]
                
                # 使用指定日期或最新日期
                idx = date_idx if date_idx >= 0 else len(df) - 1
                
                # 检查蓝色钻石条件
                is_match, reason = self.check_blue_diamond(symbol, idx)
                
                if is_match:
                    current_close = df.iloc[idx]['close']
                    
                    # 获取RPS值
                    rps_5 = self.get_rps_for_stock(symbol, 5, idx)
                    rps_10 = self.get_rps_for_stock(symbol, 10, idx)
                    rps_20 = self.calculate_rps_20(symbol, idx)
                    rps_50 = self.get_rps_for_stock(symbol, 50, idx)
                    rps_120 = self.get_rps_for_stock(symbol, 120, idx)
                    rps_250 = self.get_rps_for_stock(symbol, 250, idx)
                    
                    # 计算20天回撤
                    max_dd_20 = self.calculate_max_drawdown_20(symbol, idx)
                    
                    results.append({
                        'symbol': symbol,
                        'price': current_close,
                        'rps_5': rps_5,
                        'rps_10': rps_10,
                        'rps_20': rps_20,
                        'rps_50': rps_50,
                        'rps_120': rps_120,
                        'rps_250': rps_250,
                        'rps_sum_20_50': rps_20 + rps_50,
                        'max_dd_20': max_dd_20 * 100,
                        'reason': reason
                    })
            
            except Exception as e:
                continue
        
        if not results:
            print("未找到符合条件的股票")
            return pd.DataFrame()
        
        # 转换为DataFrame
        result_df = pd.DataFrame(results)
        
        # 按RPS50排序
        result_df = result_df.sort_values('rps_50', ascending=False)
        
        print(f"\n找到 {len(result_df)} 只符合蓝色钻石策略的股票")
        print("\n符合条件的股票列表（按RPS50排序）：")
        print(result_df[['symbol', 'price', 'rps_20', 'rps_50', 'rps_sum_20_50', 'max_dd_20', 'reason']].to_string())
        
        return result_df


def main():
    """主函数"""
    print("=" * 80)
    print("蓝色钻石选股策略")
    print("=" * 80)
    print("策略原理：捕捉强势股第二波上涨机会")
    print("特点：不要求RPS120/250，只关注RPS20/50短期强度")
    print("=" * 80)
    print()
    
    # 创建策略实例
    strategy = BlueDiamondStrategy()
    
    print("正在加载数据...")
    strategy.load_data()
    
    print("正在预计算RPS...")
    strategy.precalculate_all_rps()
    
    # 筛选股票
    result_df = strategy.screen_stocks()
    
    if not result_df.empty:
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.expanduser(f"~/.vntrader/blue_diamond_{timestamp}.csv")
        result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n结果已保存到: {output_file}")
        
        # 统计信息
        print("\n" + "=" * 80)
        print("统计信息")
        print("=" * 80)
        print(f"总股票数: {len(strategy.all_bars)}")
        print(f"符合条件: {len(result_df)} 只")
        print(f"符合率: {len(result_df)/len(strategy.all_bars)*100:.2f}%")
        print()
        print(f"RPS20平均值: {result_df['rps_20'].mean():.2f}")
        print(f"RPS50平均值: {result_df['rps_50'].mean():.2f}")
        print(f"RPS20+RPS50平均值: {result_df['rps_sum_20_50'].mean():.2f}")
        print(f"20天平均回撤: {result_df['max_dd_20'].mean():.2f}%")


if __name__ == "__main__":
    main()
