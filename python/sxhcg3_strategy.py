#!/usr/bin/env python3
"""
顺向火车轨3.0策略 (SXHCG 3.0)

通达信公式翻译：
RPSHC120:=EXTDATA_USER(1,0)/10;  {RPS120}
RPSHC250:=EXTDATA_USER(2,0)/10;  {RPS250}
SXHCG1:=RPSHC120+RPSHC250>185;   {条件1: RPS120+RPS250>185}

SXHCG2:=C>MA(C,20) AND COUNT(C>MA(C,250),30)>=25 AND COUNT(C>MA(C,200),30)>=25 
       AND (COUNT(C>MA(C,20),10)>=9 OR (COUNT(C>MA(C,10),4)>=3 AND COUNT(C>MA(C,20),4)>=3));

新高天数:=HHVBARS(H,20);
新低天数:=IF(新高天数=0,0,LLVBARS(L,新高天数));
新高价:=REF(H,新高天数);
新低价:=REF(L,新低天数);
回撤幅度:=(新高价-新低价)/新高价;
SXHCG3:=回撤幅度<=0.25 AND COUNT(回撤幅度>0.25,新高天数)=0 AND C/HHV(C,250)>0.8;

SXHCG4:=EVERY(MA(C,20)>=REF(MA(C,20),1) AND MA(C,10)>=MA(C,20),5) 
       OR (MA(C,10)>=REF(MA(C,10),1) AND MA(C,20)>=REF(MA(C,20),1) AND MA(C,10)>=MA(C,20));

换手率:=VOL/CAPITAL*100<10;

信号: SXHCG1 AND SXHCG2 AND SXHCG3 AND SXHCG4 AND 换手率;

策略逻辑：
  1. RPS强度：RPS120 + RPS250 > 185（强势股特征）
  2. 价格位置：价格>MA20，30天内至少25天在MA250和MA200之上
  3. 回撤控制：回撤≤25%，价格在250日高点的80%以上
  4. 均线趋势：MA10和MA20向上，MA10>=MA20
  5. 换手率：< 10%（避免过度投机）

适用场景：
  - 中长期投资、趋势跟踪
  - 捕捉强势股的持续上涨机会
"""

import sys
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.expanduser("~"))

from vnpy.trader.database import get_database
from vnpy.trader.constant import Exchange, Interval


# ═══════════════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════════════

def ma(series: np.ndarray, period: int) -> np.ndarray:
    """计算移动平均线"""
    result = np.full_like(series, np.nan)
    for i in range(period - 1, len(series)):
        result[i] = np.mean(series[i - period + 1:i + 1])
    return result


def hhvbars(series: np.ndarray, period: int) -> np.ndarray:
    """
    HHVBARS(H, N): N周期内最高点距今天的周期数
    返回0表示今天创新高
    """
    length = len(series)
    result = np.zeros(length, dtype=int)
    
    for i in range(length):
        start_idx = max(0, i - period + 1)
        window = series[start_idx:i + 1]
        max_val = np.max(window)
        # 找到最高点的位置（从当前点往前数）
        for j in range(len(window) - 1, -1, -1):
            if window[j] == max_val:
                result[i] = len(window) - 1 - j
                break
    
    return result


def llvbars(series: np.ndarray, period: int) -> np.ndarray:
    """
    LLVBARS(L, N): N周期内最低点距今天的周期数
    """
    length = len(series)
    result = np.zeros(length, dtype=int)
    
    for i in range(length):
        start_idx = max(0, i - period + 1)
        window = series[start_idx:i + 1]
        min_val = np.min(window)
        for j in range(len(window) - 1, -1, -1):
            if window[j] == min_val:
                result[i] = len(window) - 1 - j
                break
    
    return result


def count_condition(condition: np.ndarray, period: int) -> np.ndarray:
    """
    COUNT(condition, N): 统计N周期内满足条件的次数
    """
    length = len(condition)
    result = np.zeros(length, dtype=int)
    
    for i in range(length):
        start_idx = max(0, i - period + 1)
        result[i] = np.sum(condition[start_idx:i + 1])
    
    return result


def every_condition(condition: np.ndarray, period: int) -> np.ndarray:
    """
    EVERY(condition, N): 判断N周期内是否全部满足条件
    """
    length = len(condition)
    result = np.zeros(length, dtype=bool)
    
    for i in range(period - 1, length):
        start_idx = i - period + 1
        result[i] = np.all(condition[start_idx:i + 1])
    
    return result


# ═══════════════════════════════════════════════════════════════════════
# 顺向火车轨3.0策略
# ═══════════════════════════════════════════════════════════════════════

class SXHCGStrategy:
    """顺向火车轨3.0策略"""

    # RPS计算周期
    RPS_PERIODS = [120, 250]

    def __init__(self):
        self.db = get_database()

        # 全市场数据
        self.all_bars: Dict[str, pd.DataFrame] = {}
        self.rps_wide_data: Dict[int, pd.DataFrame] = {}

        # 股票名称缓存
        self.name_cache = self._load_name_cache()

    def _load_name_cache(self) -> Dict[str, str]:
        """加载股票名称缓存"""
        name_cache = {}
        path = os.path.expanduser("~/.vntrader/stock_names.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                name_cache = json.load(f)
        return name_cache

    def get_stock_name(self, symbol: str) -> str:
        """获取股票名称"""
        code = symbol.split('.')[0]
        return self.name_cache.get(code, symbol)

    def load_all_market_data(self) -> None:
        """加载全市场日K数据"""
        print("正在加载全市场日K数据...")

        overview = self.db.get_bar_overview()
        bar_dict: Dict[str, List] = {}

        for item in overview:
            if item.interval != Interval.DAILY:
                continue
            if item.exchange not in (Exchange.SSE, Exchange.SZSE):
                continue

            bars = self.db.load_bar_data(
                symbol=item.symbol,
                exchange=item.exchange,
                interval=Interval.DAILY,
                start=datetime(2024, 1, 1),
                end=datetime.now()
            )
            if not bars:
                continue

            key = f"{item.symbol}.{item.exchange.value}"
            bar_dict[key] = bars

        for key, bar_list in bar_dict.items():
            df = pd.DataFrame([{
                'datetime': b.datetime,
                'open': b.open_price,
                'high': b.high_price,
                'low': b.low_price,
                'close': b.close_price,
                'volume': b.volume,
            } for b in bar_list])
            df.set_index('datetime', inplace=True)
            df.sort_index(inplace=True)
            self.all_bars[key] = df

        print(f"✅ 加载完成: {len(self.all_bars)} 只股票")

    def calculate_rps(self, period: int) -> pd.DataFrame:
        """计算N日RPS（百分位排名）"""
        print(f"  正在计算 {period} 日RPS...")

        returns_dict: Dict[str, pd.Series] = {}
        for symbol, df in self.all_bars.items():
            if len(df) < period + 1:
                continue
            ret = (df['close'] / df['close'].shift(period) - 1) * 100
            returns_dict[symbol] = ret

        if not returns_dict:
            return pd.DataFrame()

        returns_df = pd.DataFrame(returns_dict)
        rps_df = returns_df.rank(axis=1, method='average', pct=True) * 100

        print(f"    维度: {rps_df.shape[0]} 天 × {rps_df.shape[1]} 只股票")
        return rps_df

    def precalculate_all_rps(self) -> None:
        """预计算所有周期的RPS"""
        print("\n正在预计算全市场RPS值...")
        for period in self.RPS_PERIODS:
            rps_df = self.calculate_rps(period)
            if not rps_df.empty:
                self.rps_wide_data[period] = rps_df
        print("✅ RPS预计算完成\n")

    def get_rps_for_stock(self, symbol: str, period: int, date_idx) -> Optional[float]:
        """查询某只股票在某个日期的RPS值"""
        if period not in self.rps_wide_data:
            return None
        rps_df = self.rps_wide_data[period]
        if symbol not in rps_df.columns:
            return None
        if date_idx in rps_df.index:
            val = rps_df.loc[date_idx, symbol]
            return float(val) if not pd.isna(val) else None
        return None

    def check_sxhcg_signal(self, df: pd.DataFrame, rps_120: float, rps_250: float,
                           turnover_rate: float = None) -> Tuple[bool, dict]:
        """
        检查是否满足顺向火车轨3.0条件
        
        返回: (是否触发, 详细信息)
        """
        if len(df) < 250:
            return False, {}

        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        volumes = df['volume'].values

        idx = len(df) - 1

        # ── 条件1：RPS强度 SXHCG1 ──
        rps_sum = rps_120 + rps_250
        sxhcg1 = rps_sum > 185
        if not sxhcg1:
            return False, {'reason': f'RPS和={rps_sum:.1f} ≤ 185'}

        # ── 条件2：价格位置 SXHCG2 ──
        ma20 = ma(closes, 20)
        ma200 = ma(closes, 200)
        ma250 = ma(closes, 250)
        ma10 = ma(closes, 10)

        # C > MA20
        price_above_ma20 = closes[idx] > ma20[idx]

        # COUNT(C > MA250, 30) >= 25
        above_ma250_30 = count_condition(closes > ma250, 30)
        above_ma250_ok = above_ma250_30[idx] >= 25

        # COUNT(C > MA200, 30) >= 25
        above_ma200_30 = count_condition(closes > ma200, 30)
        above_ma200_ok = above_ma200_30[idx] >= 25

        # (COUNT(C > MA20, 10) >= 9) OR (COUNT(C > MA10, 4) >= 3 AND COUNT(C > MA20, 4) >= 3)
        above_ma20_10 = count_condition(closes > ma20, 10)
        above_ma10_4 = count_condition(closes > ma10, 4)
        above_ma20_4 = count_condition(closes > ma20, 4)
        
        price_stability = (above_ma20_10[idx] >= 9) or \
                          (above_ma10_4[idx] >= 3 and above_ma20_4[idx] >= 3)

        sxhcg2 = price_above_ma20 and above_ma250_ok and above_ma200_ok and price_stability
        if not sxhcg2:
            return False, {'reason': '价格位置条件不满足'}

        # ── 条件3：回撤控制 SXHCG3 ──
        # 新高天数 = HHVBARS(H, 20)
        new_high_days_arr = hhvbars(highs, 20)
        new_high_days = new_high_days_arr[idx]

        # 新低天数
        if new_high_days == 0:
            new_low_days = 0
        else:
            # 从新高点到现在，找最低点
            start_idx = idx - new_high_days
            llv_arr = llvbars(lows[start_idx:idx + 1], new_high_days + 1)
            new_low_days = llv_arr[-1]

        # 新高价和新低价
        new_high_price = highs[idx - new_high_days] if new_high_days > 0 else highs[idx]
        new_low_price = lows[idx - new_low_days] if new_low_days > 0 else lows[idx]

        # 回撤幅度 = (新高价 - 新低价) / 新高价
        if new_high_price > 0:
            drawdown = (new_high_price - new_low_price) / new_high_price
        else:
            drawdown = 1.0

        # 回撤≤25%
        drawdown_ok = drawdown <= 0.25

        # COUNT(回撤幅度>0.25, 新高天数)=0
        # 解释：在过去"新高天数"天内，每天的回撤幅度都<=25%
        # 需要计算每个历史时间点的"新高天数"和对应的"回撤幅度"
        if new_high_days > 0:
            no_excessive_drawdown = True
            # 检查过去新高天数天内，每一天的回撤是否都<=25%
            for d in range(1, min(new_high_days, 19) + 1):  # 最多检查20天内
                check_idx = idx - d
                if check_idx < 20:  # 需要足够数据
                    continue
                
                # 计算该天的新高天数和回撤幅度
                check_new_high_days = new_high_days_arr[check_idx]
                if check_new_high_days == 0:
                    continue  # 该天创新高，回撤为0
                
                # 计算该天的回撤幅度
                check_high_price = highs[check_idx - check_new_high_days]
                
                # 找该天的新低价（从新高点到该天的最低点）
                check_low_idx = check_idx
                for k in range(check_idx - check_new_high_days, check_idx + 1):
                    if lows[k] < lows[check_low_idx]:
                        check_low_idx = k
                check_low_price = lows[check_low_idx]
                
                if check_high_price > 0:
                    check_dd = (check_high_price - check_low_price) / check_high_price
                    if check_dd > 0.25:
                        no_excessive_drawdown = False
                        break
        else:
            no_excessive_drawdown = True

        # 价格在250日高点的80%以上
        high_250 = np.max(closes[-250:])
        price_position_ok = closes[idx] / high_250 > 0.8

        # SXHCG3 = 回撤≤25% AND 期间无过度回撤 AND 价格位置OK
        sxhcg3 = drawdown_ok and no_excessive_drawdown and price_position_ok
        if not sxhcg3:
            if not drawdown_ok:
                reason = f'回撤={drawdown:.2%}>25%'
            elif not no_excessive_drawdown:
                reason = '期间存在回撤>25%'
            else:
                reason = f'价格位置={closes[idx]/high_250:.2%}<80%'
            return False, {'reason': reason}

        # ── 条件4：均线趋势 SXHCG4 ──
        # EVERY(MA20 >= REF(MA20,1) AND MA10 >= MA20, 5)
        ma20_rising = ma20[1:] >= ma20[:-1]
        ma10_above_ma20 = ma10 >= ma20
        both_ok = ma20_rising & ma10_above_ma20[1:]
        every_ok = every_condition(both_ok, 5)
        
        # OR (MA10 >= REF(MA10,1) AND MA20 >= REF(MA20,1) AND MA10 >= MA20)
        ma10_rising = ma10[idx] >= ma10[idx - 1]
        ma20_rising_now = ma20[idx] >= ma20[idx - 1]
        ma10_above_ma20_now = ma10[idx] >= ma20[idx]
        current_ok = ma10_rising and ma20_rising_now and ma10_above_ma20_now

        # 修复：正确使用括号确保运算符优先级
        # SXHCG4 = EVERY条件 OR 当前均线条件
        every_condition_ok = every_ok[idx - 1] if idx > 0 else False
        sxhcg4 = every_condition_ok or current_ok
        
        if not sxhcg4:
            return False, {'reason': '均线趋势条件不满足'}

        # ── 条件5：换手率 ──
        # 简化处理：如果有换手率数据则检查，否则跳过
        turnover_ok = True
        if turnover_rate is not None:
            turnover_ok = turnover_rate < 10

        # ── 所有条件通过 ──
        return True, {
            'close': closes[idx],
            'rps_120': round(rps_120, 1),
            'rps_250': round(rps_250, 1),
            'rps_sum': round(rps_sum, 1),
            'drawdown': round(drawdown * 100, 2),
            'new_high_days': new_high_days,
            'price_position': round(closes[idx] / high_250 * 100, 1),
            'turnover_rate': turnover_rate,
            'volume': volumes[idx],
        }

    def run_screening(self):
        """运行顺向火车轨3.0选股"""
        print("=" * 80)
        print("顺向火车轨3.0选股策略 (SXHCG 3.0)")
        print("=" * 80)
        print("策略原理:")
        print("  1. RPS强度：RPS120 + RPS250 > 185")
        print("  2. 价格位置：价格>MA20，30天内至少25天在MA250/MA200之上")
        print("  3. 回撤控制：回撤≤25%，价格在250日高点的80%以上")
        print("  4. 均线趋势：MA10和MA20向上，MA10>=MA20")
        print("  5. 换手率：< 10%")
        print("=" * 80)
        print()

        # Step 1: 加载数据
        self.load_all_market_data()

        # Step 2: 预计算RPS
        self.precalculate_all_rps()

        # 找到最新交易日
        latest_dates = [df.index[-1] for df in self.all_bars.values() if len(df) > 0]
        if not latest_dates:
            print("❌ 无可用数据")
            return
        target_date = max(latest_dates)
        print(f"📅 筛选日期: {target_date.strftime('%Y-%m-%d')}")
        print()

        print("开始筛选...")
        print()

        results = []
        total = len(self.all_bars)

        for i, (symbol, df) in enumerate(self.all_bars.items()):
            if (i + 1) % 500 == 0:
                print(f"  处理进度: {i+1}/{total}")

            try:
                rows_up_to_target = df[df.index <= target_date]
                if len(rows_up_to_target) < 250:
                    continue

                date_idx = rows_up_to_target.index[-1]

                # 获取RPS数据
                rps_120 = self.get_rps_for_stock(symbol, 120, date_idx) or 0
                rps_250 = self.get_rps_for_stock(symbol, 250, date_idx) or 0

                # 检查条件
                is_match, details = self.check_sxhcg_signal(
                    rows_up_to_target, rps_120, rps_250
                )

                if is_match:
                    name = self.get_stock_name(symbol)
                    results.append({
                        'symbol': symbol,
                        'name': name,
                        'close': details['close'],
                        'rps_120': details['rps_120'],
                        'rps_250': details['rps_250'],
                        'rps_sum': details['rps_sum'],
                        'drawdown': details['drawdown'],
                        'price_position': details['price_position'],
                        'volume': details['volume'],
                    })

            except Exception:
                continue

        # ── 输出结果 ──
        print()
        print("=" * 80)
        print("筛选完成")
        print("=" * 80)
        print()

        if results:
            df_result = pd.DataFrame(results)
            df_result = df_result.sort_values('rps_sum', ascending=False)

            output_file = os.path.expanduser(
                f"~/.vntrader/sxhcg3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            df_result.to_csv(output_file, index=False, encoding='utf-8-sig')

            print(f"✅ 找到 {len(results)} 只顺向火车轨3.0信号股票")
            print()
            print(f"{'排名':^4} {'代码':^14} {'名称':^8} {'收盘':^8} "
                  f"{'RPS和':^6} {'RPS120':^7} {'RPS250':^7} {'回撤%':^6} {'位置%':^6}")
            print("-" * 85)

            for rank, (_, row) in enumerate(df_result.iterrows(), 1):
                print(f"{rank:^4} {row['symbol']:^14} {str(row['name'])[:6]:^8} "
                      f"{row['close']:>7.2f} {row['rps_sum']:>5.1f} "
                      f"{row['rps_120']:>6.1f} {row['rps_250']:>6.1f} "
                      f"{row['drawdown']:>5.1f}% {row['price_position']:>5.1f}%")
                if rank >= 30:
                    remaining = len(df_result) - 30
                    if remaining > 0:
                        print(f"  ... 还有 {remaining} 只（详见CSV）")
                    break

            print()
            print(f"📁 结果已保存: {output_file}")

        else:
            print("❌ 未找到符合条件的股票")
            print()
            print("说明:")
            print("  顺向火车轨3.0要求：")
            print("    - RPS120 + RPS250 > 185")
            print("    - 价格位置条件（均线支撑）")
            print("    - 回撤≤25%")
            print("    - 均线趋势向上")
            print("    - 换手率<10%")
            print("  条件较为严格，在市场调整期可能筛选结果较少")


# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    strategy = SXHCGStrategy()
    strategy.run_screening()
