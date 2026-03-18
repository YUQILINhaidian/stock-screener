#!/usr/bin/env python3
"""
圆弧底选股策略

通达信公式翻译：
  AA:=(C*2+H+L+O)/5;
  条件1:=MA(C,5);
  条件2:=(EMA(AA,4)+MA(AA,8)+MA(AA,16))/3;
  条件5:=(EMA(AA,9)+MA(AA,18)+MA(AA,36))/3;
  条件4:=(EMA(AA,13)+MA(AA,26)+MA(AA,52))/3;
  条件6:=(EMA(AA,24)+MA(AA,48)+MA(AA,96))/3;
  条件10:=MAX(MAX(条件2,条件5),MAX(条件4,条件6));
  条件9:=MIN(MIN(条件2,条件5),MIN(条件4,条件6));
  条件16:=MIN(MIN(条件2,条件5),条件4);
  条件20:=MAX(MAX(条件2,条件5),条件4);
  圆弧底:LONGCROSS(条件2,条件4,30)
         AND (条件6-条件4)/条件4<0.05
         AND 条件20<条件6;

逻辑解读：
  - AA: 加权均价（收盘价权重更大）
  - 条件2: 短周期综合线 (4/8/16)
  - 条件5: 中短周期综合线 (9/18/36)
  - 条件4: 中周期综合线 (13/26/52)
  - 条件6: 长周期综合线 (24/48/96)
  - LONGCROSS(条件2,条件4,30): 条件2在过去30天持续低于条件4后，今天上穿
    → 表示短周期线在底部蛰伏30天后首次突破中周期线（圆弧底完成）
  - (条件6-条件4)/条件4 < 0.05: 长周期线与中周期线收敛（底部形态确认）
  - 条件20 < 条件6: 短中期最大值仍低于长期线（仍在底部区域，安全边际高）
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.expanduser("~"))

from vnpy.trader.database import get_database
from vnpy.trader.constant import Exchange, Interval


# ═══════════════════════════════════════════════════════════════════════
# 技术指标计算
# ═══════════════════════════════════════════════════════════════════════

def ema(series: np.ndarray, period: int) -> np.ndarray:
    """指数移动平均（与通达信 EMA 一致）"""
    result = np.empty_like(series)
    result[0] = series[0]
    alpha = 2.0 / (period + 1)
    for i in range(1, len(series)):
        result[i] = alpha * series[i] + (1 - alpha) * result[i - 1]
    return result


def ma(series: np.ndarray, period: int) -> np.ndarray:
    """简单移动平均"""
    result = np.full_like(series, np.nan)
    for i in range(period - 1, len(series)):
        result[i] = np.mean(series[i - period + 1: i + 1])
    return result


def longcross(a: np.ndarray, b: np.ndarray, n: int) -> np.ndarray:
    """
    LONGCROSS(A, B, N)
    含义: A 在过去 N 天一直低于 B，今天 A 上穿 B
    即: 今天 A > B 且 前 N 天 A 都 < B
    """
    length = len(a)
    result = np.zeros(length, dtype=bool)
    for i in range(n, length):
        if a[i] > b[i]:  # 今天 A > B（上穿）
            all_below = True
            for j in range(1, n + 1):
                if a[i - j] >= b[i - j]:
                    all_below = False
                    break
            result[i] = all_below
    return result


# ═══════════════════════════════════════════════════════════════════════
# 圆弧底策略
# ═══════════════════════════════════════════════════════════════════════

class ArcBottomStrategy:
    """圆弧底选股策略"""

    def __init__(self):
        self.db = get_database()

    def calc_indicators(self, df: pd.DataFrame) -> Optional[dict]:
        """
        计算圆弧底所需的全部指标。

        参数:
            df: DataFrame，需要包含 open/high/low/close 列，行数 >= 120

        返回:
            dict 包含最新一天是否触发信号及辅助数据，
            若数据不足返回 None
        """
        if len(df) < 120:
            return None

        O = df['open'].values.astype(float)
        H = df['high'].values.astype(float)
        L = df['low'].values.astype(float)
        C = df['close'].values.astype(float)

        # AA: 加权均价
        AA = (C * 2 + H + L + O) / 5.0

        # 四档综合线
        cond2 = (ema(AA, 4)  + ma(AA, 8)  + ma(AA, 16)) / 3.0   # 短周期
        cond5 = (ema(AA, 9)  + ma(AA, 18) + ma(AA, 36)) / 3.0   # 中短周期
        cond4 = (ema(AA, 13) + ma(AA, 26) + ma(AA, 52)) / 3.0   # 中周期
        cond6 = (ema(AA, 24) + ma(AA, 48) + ma(AA, 96)) / 3.0   # 长周期

        # 辅助指标
        cond10 = np.maximum(np.maximum(cond2, cond5), np.maximum(cond4, cond6))  # 全局最大
        cond9  = np.minimum(np.minimum(cond2, cond5), np.minimum(cond4, cond6))  # 全局最小
        cond16 = np.minimum(np.minimum(cond2, cond5), cond4)                     # 短中最小
        cond20 = np.maximum(np.maximum(cond2, cond5), cond4)                     # 短中最大

        # ── 圆弧底信号 ──
        cross_signal = longcross(cond2, cond4, 30)

        # 最新一天
        idx = len(C) - 1
        if np.isnan(cond6[idx]) or np.isnan(cond4[idx]):
            return None

        signal_cross = cross_signal[idx]
        signal_converge = ((cond6[idx] - cond4[idx]) / cond4[idx]) < 0.05 if cond4[idx] > 0 else False
        signal_below = cond20[idx] < cond6[idx]

        triggered = signal_cross and signal_converge and signal_below

        return {
            'triggered':      triggered,
            'signal_cross':   signal_cross,
            'signal_converge': signal_converge,
            'signal_below':   signal_below,
            'close':          C[idx],
            'cond2':          cond2[idx],
            'cond4':          cond4[idx],
            'cond5':          cond5[idx],
            'cond6':          cond6[idx],
            'cond20':         cond20[idx],
            'converge_ratio': (cond6[idx] - cond4[idx]) / cond4[idx] if cond4[idx] > 0 else 999,
        }

    def run_screening(self):
        """运行圆弧底选股"""
        print("=" * 80)
        print("圆弧底选股策略")
        print("=" * 80)
        print("原理: 短周期综合线在底部蛰伏30天后首次上穿中周期线")
        print("      同时长周期线与中周期线收敛，短中期线仍低于长期线")
        print("      → 圆弧底形态确认，底部突破信号")
        print("=" * 80)
        print()

        # 获取所有股票
        overview = self.db.get_bar_overview()
        symbols = [(item.symbol, item.exchange)
                    for item in overview
                    if item.interval == Interval.DAILY
                    and item.exchange in (Exchange.SSE, Exchange.SZSE)]
        print(f"📦 共 {len(symbols)} 只股票待筛选")
        print()

        results = []
        total = len(symbols)

        for i, (symbol, exchange) in enumerate(symbols):
            if (i + 1) % 500 == 0:
                print(f"  处理进度: {i+1}/{total} ({(i+1)/total*100:.1f}%)")

            try:
                bars = self.db.load_bar_data(
                    symbol=symbol,
                    exchange=exchange,
                    interval=Interval.DAILY,
                    start=datetime(2024, 1, 1),
                    end=datetime.now()
                )
                if len(bars) < 120:
                    continue

                df = pd.DataFrame([{
                    'datetime': b.datetime,
                    'open':     b.open_price,
                    'high':     b.high_price,
                    'low':      b.low_price,
                    'close':    b.close_price,
                    'volume':   b.volume,
                } for b in bars])
                df.set_index('datetime', inplace=True)
                df.sort_index(inplace=True)

                result = self.calc_indicators(df)
                if result and result['triggered']:
                    symbol_key = f"{symbol}.{exchange.value}"
                    results.append({
                        'symbol':         symbol_key,
                        'name':           _get_stock_name(symbol),
                        'close':          result['close'],
                        'cond2':          round(result['cond2'], 2),
                        'cond4':          round(result['cond4'], 2),
                        'cond6':          round(result['cond6'], 2),
                        'converge_ratio': round(result['converge_ratio'] * 100, 2),
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
            df_result = df_result.sort_values('converge_ratio')

            output_file = os.path.expanduser(
                f"~/.vntrader/arc_bottom_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            df_result.to_csv(output_file, index=False, encoding='utf-8-sig')

            print(f"✅ 找到 {len(results)} 只圆弧底信号股票")
            print()
            print(f"{'排名':^4} {'代码':^14} {'名称':^8} {'收盘价':^8} "
                  f"{'短线':^8} {'中线':^8} {'长线':^8} {'收敛%':^7}")
            print("-" * 80)

            for rank, (_, row) in enumerate(df_result.iterrows(), 1):
                print(f"{rank:^4} {row['symbol']:^14} {str(row['name'])[:6]:^8} "
                      f"{row['close']:>7.2f} {row['cond2']:>7.2f} "
                      f"{row['cond4']:>7.2f} {row['cond6']:>7.2f} "
                      f"{row['converge_ratio']:>6.2f}%")
                if rank >= 30:
                    remaining = len(df_result) - 30
                    if remaining > 0:
                        print(f"  ... 还有 {remaining} 只（详见CSV）")
                    break

            print()
            print(f"📁 结果已保存: {output_file}")

        else:
            print("❌ 未找到符合圆弧底信号的股票")
            print()
            print("说明:")
            print("  圆弧底要求短周期线在底部蛰伏30天后才刚上穿中周期线")
            print("  这是一个相对稀少的信号，不是每天都能出现")
            print("  建议每天收盘后运行一次，捕捉信号触发的时刻")


# ═══════════════════════════════════════════════════════════════════════
# 股票名称辅助
# ═══════════════════════════════════════════════════════════════════════

_NAME_CACHE: Dict[str, str] = {}


def _get_stock_name(code: str) -> str:
    """从缓存获取中文名称"""
    global _NAME_CACHE
    if not _NAME_CACHE:
        path = os.path.expanduser("~/.vntrader/stock_names.json")
        if os.path.exists(path):
            import json
            with open(path, 'r', encoding='utf-8') as f:
                _NAME_CACHE = json.load(f)
    return _NAME_CACHE.get(code, code)


# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    strategy = ArcBottomStrategy()
    strategy.run_screening()
