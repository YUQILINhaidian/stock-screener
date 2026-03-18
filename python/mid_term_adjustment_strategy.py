#!/usr/bin/env python3
"""
中期调整后选股策略 (Mid-Term Adjustment Strategy)

通达信公式翻译：
{参数设置}
N:=250;    {涨幅周期}
M:=120;    {调整周期}
RPS值:=90; {RPS一线红参数}

{区间涨幅超100%}
区间涨幅:=C/REF(C,N)>=2;

{中期调整幅度≤50%}
最高价:=HHV(H,M);
最低价:=LLV(L,M);
调整幅度:=(最高价-最低价)/最高价<=0.5;

{RPS一线红}
RPS50:=EXTDATA_USER(3,0)/10>=RPS值;
RPS120:=EXTDATA_USER(1,0)/10>=RPS值;
RPS250:=EXTDATA_USER(2,0)/10>=RPS值;

{综合选股}
选股:区间涨幅 AND 调整幅度 AND (RPS50 OR RPS120 OR RPS250);

策略逻辑：
  1. 区间涨幅：250天内涨幅超过100%（即翻倍）
  2. 中期调整幅度：120天内最大回撤不超过50%
  3. RPS一线红：RPS50、RPS120、RPS250中任意一个>=90

适用场景：
  - 捕捉强势股中期调整后的买点
  - 适合波段操作
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
# 策略参数
# ═══════════════════════════════════════════════════════════════════════

# 涨幅周期（天）
GAIN_PERIOD = 250

# 调整周期（天）
ADJUSTMENT_PERIOD = 120

# RPS阈值
RPS_THRESHOLD = 90


# ═══════════════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════════════

def hhv(series: np.ndarray, period: int) -> np.ndarray:
    """HHV(H, N): N周期内最高值"""
    length = len(series)
    result = np.full(length, np.nan)
    
    for i in range(period - 1, length):
        result[i] = np.max(series[i - period + 1:i + 1])
    
    # 对于前面的数据，使用可用的数据
    for i in range(period - 1):
        result[i] = np.max(series[:i + 1])
    
    return result


def llv(series: np.ndarray, period: int) -> np.ndarray:
    """LLV(L, N): N周期内最低值"""
    length = len(series)
    result = np.full(length, np.nan)
    
    for i in range(period - 1, length):
        result[i] = np.min(series[i - period + 1:i + 1])
    
    # 对于前面的数据，使用可用的数据
    for i in range(period - 1):
        result[i] = np.min(series[:i + 1])
    
    return result


# ═══════════════════════════════════════════════════════════════════════
# 中期调整后选股策略
# ═══════════════════════════════════════════════════════════════════════

class MidTermAdjustmentStrategy:
    """中期调整后选股策略"""

    # RPS计算周期
    RPS_PERIODS = [50, 120, 250]

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

    def check_signal(self, df: pd.DataFrame, rps_50: float, rps_120: float, 
                     rps_250: float) -> Tuple[bool, dict]:
        """
        检查是否满足中期调整后选股条件
        
        返回: (是否触发, 详细信息)
        """
        if len(df) < GAIN_PERIOD:
            return False, {}

        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        volumes = df['volume'].values

        idx = len(df) - 1

        # ── 条件1：区间涨幅超100% ──
        # C/REF(C, N) >= 2，即250天内涨幅超过100%
        gain_250d = closes[idx] / closes[idx - GAIN_PERIOD]
        gain_ok = gain_250d >= 2.0

        if not gain_ok:
            return False, {'reason': f'250日涨幅={(gain_250d-1)*100:.1f}%<100%'}

        # ── 条件2：中期调整幅度≤50% ──
        # 最高价:=HHV(H,M);
        # 最低价:=LLV(L,M);
        # 调整幅度:=(最高价-最低价)/最高价<=0.5;
        
        # 获取M周期内的最高价和最低价
        period_high = np.max(highs[-ADJUSTMENT_PERIOD:])
        period_low = np.min(lows[-ADJUSTMENT_PERIOD:])
        
        # 调整幅度 = (最高价 - 最低价) / 最高价
        adjustment = (period_high - period_low) / period_high
        adjustment_ok = adjustment <= 0.5

        if not adjustment_ok:
            return False, {'reason': f'调整幅度={adjustment*100:.1f}%>50%'}

        # ── 条件3：收盘价年线以上 ──
        # C > MA(C, 250)
        if len(closes) < 250:
            return False, {'reason': '数据不足250天'}
        
        ma250 = np.mean(closes[-250:])
        above_ma250 = closes[idx] > ma250
        
        if not above_ma250:
            return False, {'reason': f'收盘价{closes[idx]:.2f}低于年线{ma250:.2f}'}

        # ── 条件4：RPS一线红 ──
        # RPS50 >= 90 OR RPS120 >= 90 OR RPS250 >= 90
        rps_red_line = (rps_50 >= RPS_THRESHOLD) or \
                       (rps_120 >= RPS_THRESHOLD) or \
                       (rps_250 >= RPS_THRESHOLD)

        if not rps_red_line:
            return False, {
                'reason': f'RPS不满足一线红(50:{rps_50:.0f},120:{rps_120:.0f},250:{rps_250:.0f})'
            }

        # ── 所有条件通过 ──
        # 计算最大RPS
        max_rps = max(rps_50, rps_120, rps_250)
        
        return True, {
            'close': closes[idx],
            'gain_250d': round((gain_250d - 1) * 100, 1),  # 涨幅百分比
            'adjustment': round(adjustment * 100, 1),  # 调整幅度百分比
            'rps_50': round(rps_50, 1),
            'rps_120': round(rps_120, 1),
            'rps_250': round(rps_250, 1),
            'max_rps': round(max_rps, 1),
            'rps_red_count': sum([
                1 if rps_50 >= RPS_THRESHOLD else 0,
                1 if rps_120 >= RPS_THRESHOLD else 0,
                1 if rps_250 >= RPS_THRESHOLD else 0,
            ]),
            'volume': volumes[idx],
            'period_high': period_high,
            'period_low': period_low,
        }

    def run_screening(self):
        """运行中期调整后选股"""
        print("=" * 80)
        print("中期调整后选股策略 (Mid-Term Adjustment Strategy)")
        print("=" * 80)
        print("策略原理:")
        print(f"  1. 区间涨幅：{GAIN_PERIOD}天内涨幅超过100%（翻倍）")
        print(f"  2. 中期调整幅度：{ADJUSTMENT_PERIOD}天内最大回撤不超过50%")
        print(f"  3. RPS一线红：RPS50/120/250中任意一个>={RPS_THRESHOLD}")
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
                if len(rows_up_to_target) < GAIN_PERIOD:
                    continue

                date_idx = rows_up_to_target.index[-1]

                # 获取RPS数据
                rps_50 = self.get_rps_for_stock(symbol, 50, date_idx) or 0
                rps_120 = self.get_rps_for_stock(symbol, 120, date_idx) or 0
                rps_250 = self.get_rps_for_stock(symbol, 250, date_idx) or 0

                # 检查条件
                is_match, details = self.check_signal(
                    rows_up_to_target, rps_50, rps_120, rps_250
                )

                if is_match:
                    name = self.get_stock_name(symbol)
                    results.append({
                        'symbol': symbol,
                        'name': name,
                        'close': details['close'],
                        'gain_250d': details['gain_250d'],
                        'adjustment': details['adjustment'],
                        'rps_50': details['rps_50'],
                        'rps_120': details['rps_120'],
                        'rps_250': details['rps_250'],
                        'max_rps': details['max_rps'],
                        'rps_red_count': details['rps_red_count'],
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
            # 按涨幅和RPS排序
            df_result = df_result.sort_values(
                ['gain_250d', 'max_rps'], 
                ascending=[False, False]
            )

            output_file = os.path.expanduser(
                f"~/.vntrader/mid_term_adjustment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            df_result.to_csv(output_file, index=False, encoding='utf-8-sig')

            print(f"✅ 找到 {len(results)} 只中期调整后选股信号股票")
            print()
            print(f"{'排名':^4} {'代码':^14} {'名称':^8} {'收盘':^8} "
                  f"{'涨幅%':^7} {'调整%':^6} {'RPS50':^6} {'RPS120':^6} {'RPS250':^6} {'红线':^4}")
            print("-" * 95)

            for rank, (_, row) in enumerate(df_result.iterrows(), 1):
                print(f"{rank:^4} {row['symbol']:^14} {str(row['name'])[:6]:^8} "
                      f"{row['close']:>7.2f} {row['gain_250d']:>6.1f}% "
                      f"{row['adjustment']:>5.1f}% "
                      f"{row['rps_50']:>5.1f} {row['rps_120']:>5.1f} {row['rps_250']:>5.1f} "
                      f"{row['rps_red_count']:>3}线")
                if rank >= 30:
                    remaining = len(df_result) - 30
                    if remaining > 0:
                        print(f"  ... 还有 {remaining} 只（详见CSV）")
                    break

            print()
            print(f"📁 结果已保存: {output_file}")

            # 统计信息
            print()
            print("📊 统计信息:")
            print(f"   平均涨幅: {df_result['gain_250d'].mean():.1f}%")
            print(f"   平均调整: {df_result['adjustment'].mean():.1f}%")
            print(f"   平均最大RPS: {df_result['max_rps'].mean():.1f}")
            
            # RPS红线分布
            red_counts = df_result['rps_red_count'].value_counts().sort_index()
            print(f"   RPS红线分布: ", end="")
            for count in sorted(red_counts.index):
                print(f"{count}线:{red_counts[count]}只 ", end="")
            print()

        else:
            print("❌ 未找到符合条件的股票")
            print()
            print("说明:")
            print(f"  中期调整后选股要求：")
            print(f"    - {GAIN_PERIOD}天内涨幅超过100%（翻倍）")
            print(f"    - {ADJUSTMENT_PERIOD}天内调整幅度≤50%")
            print(f"    - RPS50/120/250中任意一个≥{RPS_THRESHOLD}")
            print("  条件较为严格，在市场调整期可能筛选结果较少")


# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    strategy = MidTermAdjustmentStrategy()
    strategy.run_screening()
