#!/usr/bin/env python3
"""
口袋支点策略实现

陶博士2006的口袋支点策略
九大核心条件同时满足
捕捉强势股调整后的启动买点

RPS计算方式（修复版）:
  - 先加载全市场所有股票的日K数据
  - 对同一天所有股票的N日涨跌幅进行横向排名（百分位）
  - 等同于 train_daily_strategy.py 中的 precalculate_all_rps() 方法
  - 确保RPS值是真正的市场相对强度百分位，而非单股票近似值
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import baostock as bs

sys.path.insert(0, os.path.expanduser("~"))

from vnpy.trader.database import get_database
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData


class PocketPivotStrategy:
    """口袋支点策略（RPS修复版）"""

    # RPS计算周期（与火车头策略保持一致）
    RPS_PERIODS = [5, 10, 20, 50, 120, 250]

    def __init__(self):
        self.db = get_database()

        # 全市场数据：key = "000001.SZSE", value = DataFrame(datetime索引，ohlcv列)
        self.all_bars: Dict[str, pd.DataFrame] = {}

        # 宽格式RPS缓存：key = period, value = DataFrame(日期索引 x 股票列)
        self.rps_wide_data: Dict[int, pd.DataFrame] = {}

        # 行业信息缓存：key = "000001.SZSE", value = "行业名称"
        self.industry_data: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # 行业信息
    # ------------------------------------------------------------------

    def load_industry_data(self) -> None:
        """从baostock获取股票行业信息"""
        import json

        # 尝试从缓存文件加载
        cache_file = os.path.expanduser("~/.vntrader/stock_industry.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.industry_data = json.load(f)
                print(f"✅ 从缓存加载行业信息: {len(self.industry_data)} 只股票")
                return
            except:
                pass

        # 从baostock获取
        print("正在从baostock获取股票行业信息...")
        lg = bs.login()
        if lg.error_code != '0':
            print(f"❌ 登录失败: {lg.error_msg}")
            return

        # 使用 query_stock_industry 获取行业信息
        rs = bs.query_stock_industry()
        if rs.error_code != '0':
            print(f"❌ 查询失败: {rs.error_msg}")
            bs.logout()
            return

        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())

        bs.logout()

        # 获取字段名
        field_names = rs.fields if isinstance(rs.fields, list) else []

        # 找到industry字段的索引
        industry_idx = -1
        for idx, fname in enumerate(field_names):
            if fname == 'industry':
                industry_idx = idx
                break

        if data_list and industry_idx >= 0:
            for row in data_list:
                # row[0]=updateDate, row[1]=code, row[2]=code_name, row[3]=industry
                if len(row) > max(industry_idx, 1):
                    code = row[1]  # 格式: sh.600000 或 sz.000001
                    industry = row[industry_idx] if row[industry_idx] else ""
                    
                    if code and industry:
                        # 转换格式: sh.600000 -> 600000.SSE, sz.000001 -> 000001.SZSE
                        code_lower = code.lower()
                        if code_lower.startswith('sh.'):
                            ts_code = code[3:] + '.SSE'
                        elif code_lower.startswith('sz.'):
                            ts_code = code[3:] + '.SZSE'
                        else:
                            ts_code = code
                        
                        self.industry_data[ts_code] = industry

            # 保存到缓存
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self.industry_data, f, ensure_ascii=False, indent=2)
            except:
                pass

        print(f"✅ 加载行业信息: {len(self.industry_data)} 只股票")

    # ------------------------------------------------------------------
    # 数据加载
    # ------------------------------------------------------------------

    def load_all_market_data(self) -> None:
        """加载全市场日K数据（与 TrainDailyStrategy.load_data 同样逻辑）"""
        print("正在加载全市场日K数据...")

        overview = self.db.get_bar_overview()

        bar_dict: Dict[str, List[BarData]] = {}
        for item in overview:
            if item.interval != Interval.DAILY:
                continue

            bars = self.db.load_bar_data(
                symbol=item.symbol,
                exchange=item.exchange,
                interval=Interval.DAILY,
                start=datetime(2020, 1, 1),
                end=datetime.now()
            )
            if not bars:
                continue

            key = f"{item.symbol}.{item.exchange.value}"
            bar_dict[key] = bars

        # 转换为 DataFrame
        for key, bar_list in bar_dict.items():
            df = pd.DataFrame([{
                'datetime': bar.datetime,
                'open':  bar.open_price,
                'high':  bar.high_price,
                'low':   bar.low_price,
                'close': bar.close_price,
                'volume': bar.volume,
            } for bar in bar_list])
            df.set_index('datetime', inplace=True)
            df.sort_index(inplace=True)
            self.all_bars[key] = df

        print(f"✅ 加载完成: {len(self.all_bars)} 只股票")

    # ------------------------------------------------------------------
    # RPS 预计算（真正的横向百分位排名）
    # ------------------------------------------------------------------

    def calculate_rps(self, period: int) -> pd.DataFrame:
        """
        计算所有股票在每个交易日的N日RPS（百分位排名）。

        算法：
          1. 对每只股票计算每天的N日收益率
          2. 在同一天对所有股票的收益率进行横向排名（pct=True → 0~1 → 乘以100得0~100）
          3. RPS=95 表示该股票当天N日涨幅超过全市场95%的股票
        """
        print(f"  正在计算 {period} 日RPS...")

        returns_dict: Dict[str, pd.Series] = {}
        for symbol, df in self.all_bars.items():
            if len(df) < period + 1:
                continue
            ret = (df['close'] / df['close'].shift(period) - 1) * 100
            returns_dict[symbol] = ret

        if not returns_dict:
            return pd.DataFrame()

        returns_df = pd.DataFrame(returns_dict)                     # 日期 × 股票
        rps_df = returns_df.rank(axis=1, method='average', pct=True) * 100  # 横向排名

        print(f"    维度: {rps_df.shape[0]} 天 × {rps_df.shape[1]} 只股票")
        return rps_df

    def precalculate_all_rps(self) -> None:
        """预计算所有周期的RPS，结果存入 self.rps_wide_data"""
        print("\n正在预计算全市场RPS值（所有周期）...")
        for period in self.RPS_PERIODS:
            rps_df = self.calculate_rps(period)
            if not rps_df.empty:
                self.rps_wide_data[period] = rps_df
        print("✅ RPS预计算完成\n")

    def get_rps_for_stock(self, symbol: str, period: int, date_idx) -> Optional[float]:
        """
        查询某只股票在某个日期的N日RPS值。

        参数:
            symbol   : "000001.SZSE"
            period   : 5/10/20/50/120/250
            date_idx : DataFrame行索引（datetime类型）
        """
        if period not in self.rps_wide_data:
            return None
        rps_df = self.rps_wide_data[period]
        if symbol not in rps_df.columns:
            return None
        if date_idx in rps_df.index:
            val = rps_df.loc[date_idx, symbol]
            return float(val) if not pd.isna(val) else None
        return None

    # ------------------------------------------------------------------
    # 换手率
    # ------------------------------------------------------------------

    def load_turnover_data(self) -> dict:
        """加载换手率数据（JSON 或 CSV 均可）"""
        import json
        import glob

        turnover_file = os.path.expanduser("~/.vntrader/turnover_rates.json")
        if os.path.exists(turnover_file):
            with open(turnover_file, 'r') as f:
                return json.load(f)

        csv_files = glob.glob(os.path.expanduser("~/.vntrader/turnover_rate_*.csv"))
        if csv_files:
            latest_csv = max(csv_files, key=os.path.getmtime)
            df = pd.read_csv(latest_csv)
            return {
                row.get('symbol', ''): {'turnover_rate': row.get('turnover_rate', 15)}
                for _, row in df.iterrows()
            }

        return {}

    # ------------------------------------------------------------------
    # 主筛选入口
    # ------------------------------------------------------------------

    def run_screening(self):
        """运行口袋支点策略筛选"""
        print("=" * 80)
        print("口袋支点策略筛选（RPS修复版）")
        print("=" * 80)
        print("策略原理: 捕捉强势股调整后的启动买点")
        print("核心特征: 当日涨幅≥5% + 放量 + RPS强势（真正横向百分位排名）")
        print("=" * 80)
        print()

        # Step1: 加载全市场数据
        self.load_all_market_data()

        # Step2: 预计算全市场RPS
        self.precalculate_all_rps()

        # Step3: 加载换手率
        turnover_data = self.load_turnover_data()
        print(f"✅ 加载换手率数据: {len(turnover_data)} 只股票")
        print()

        # Step4: 加载行业信息
        self.load_industry_data()
        print()

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
            if (i + 1) % 200 == 0:
                print(f"处理进度: {i+1}/{total}")

            try:
                # 找到目标日期在DataFrame中的位置
                rows_up_to_target = df[df.index <= target_date]
                if len(rows_up_to_target) < 250:
                    continue

                date_idx = rows_up_to_target.index[-1]  # 最新交易日
                actual_idx = len(rows_up_to_target) - 1  # 整数位置索引

                # 构建 bars 列表（使用 actual_idx 对应的截断 DataFrame）
                sub_df = df.iloc[:actual_idx + 1]

                # 获取RPS数据
                rps_data = {
                    'rps_5':   self.get_rps_for_stock(symbol, 5,   date_idx) or 0,
                    'rps_10':  self.get_rps_for_stock(symbol, 10,  date_idx) or 0,
                    'rps_20':  self.get_rps_for_stock(symbol, 20,  date_idx) or 0,
                    'rps_50':  self.get_rps_for_stock(symbol, 50,  date_idx) or 0,
                    'rps_120': self.get_rps_for_stock(symbol, 120, date_idx) or 0,
                    'rps_250': self.get_rps_for_stock(symbol, 250, date_idx) or 0,
                }

                # 换手率
                turnover = turnover_data.get(symbol, {'turnover_rate': 15})

                # 检查口袋支点（直接传 DataFrame，避免重复转换）
                is_pivot, pivot_data = self.check_pocket_pivot(sub_df, rps_data, turnover)

                if is_pivot:
                    # 获取行业信息
                    industry = self.industry_data.get(symbol, "")
                    results.append({
                        'symbol':       symbol,
                        'name':         symbol.split('.')[0],  # 简化显示
                        'industry':     industry,
                        'price':        sub_df.iloc[-1]['close'],
                        'change_pct':   pivot_data['change_pct'],
                        'volume_ratio': pivot_data['volume_ratio'],
                        'rps_50':       rps_data['rps_50'],
                        'rps_120':      rps_data['rps_120'],
                        'rps_250':      rps_data['rps_250'],
                        'max_dd':       pivot_data['max_dd'],
                        'conditions':   pivot_data['conditions'],
                    })

            except Exception:
                continue

        # ------------------------------------------------------------------
        # 输出结果
        # ------------------------------------------------------------------
        print()
        print("=" * 80)
        print("筛选完成")
        print("=" * 80)
        print()

        if results:
            result_df = pd.DataFrame(results)
            result_df = result_df.sort_values('rps_50', ascending=False)

            output_file = os.path.expanduser(
                f"~/.vntrader/pocket_pivot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            result_df.to_csv(output_file, index=False, encoding='utf-8-sig')

            print(f"✅ 找到 {len(results)} 只符合口袋支点策略的股票")
            print()
            print("Top 10 口袋支点股票:")
            print()
            print(f"{'排名':^4s} {'代码':^14s} {'价格':^8s} {'涨幅%':^8s} {'量比':^8s} "
                  f"{'RPS50':^7s} {'RPS120':^7s} {'RPS250':^7s} {'回撤%':^7s} {'行业':12s} {'触发条件':s}")
            print("-" * 125)

            for rank, (_, row) in enumerate(result_df.head(10).iterrows(), 1):
                industry_str = row.get('industry', '')[:12] if row.get('industry') else '-'
                print(f"{rank:^4d} {row['symbol']:^14s} {row['price']:>7.2f} "
                      f"{row['change_pct']:>7.2f}% {row['volume_ratio']:>7.2f}x "
                      f"{row['rps_50']:>6.1f} {row['rps_120']:>6.1f} {row['rps_250']:>6.1f} "
                      f"{row['max_dd']:>6.2f}% {industry_str:12s} {row['conditions']}")

            print()
            print(f"📁 详细结果已保存: {output_file}")

        else:
            print("❌ 未找到符合条件的股票")
            print()
            print("可能的原因:")
            print("  1. 市场处于弱势，强势股较少（KD7 涨幅≥5% 在震荡市极难满足）")
            print("  2. 条件过严，九个条件必须同时满足")
            print("  3. 换手率数据不足")
            print()
            print("建议:")
            print("  1. 使用火车头高级策略筛选强势股池 (train_daily_advanced_strategy.py)")
            print("  2. 观察强势股是否出现口袋支点信号")
            print("  3. 降低 KD7 涨幅阈值（5% → 3%）")

    # ------------------------------------------------------------------
    # 口袋支点九大条件检查
    # ------------------------------------------------------------------

    def check_pocket_pivot(self, df: pd.DataFrame, rps_data: dict, turnover: dict):
        """
        检查是否满足口袋支点九大条件。

        参数:
            df       : 截至目标日期的日K DataFrame（datetime索引，ohlcv列）
            rps_data : 该股票在目标日期的RPS字典
            turnover : 该股票的换手率字典

        返回:
            (bool, dict)  — 是否触发，触发细节
        """
        if len(df) < 250:
            return False, {}

        closes  = df['close'].values
        highs   = df['high'].values
        lows    = df['low'].values
        volumes = df['volume'].values

        close_latest  = closes[-1]
        close_prev    = closes[-2] if len(closes) >= 2 else closes[-1]
        high_latest   = highs[-1]
        volume_latest = volumes[-1]

        change_pct = (close_latest / close_prev - 1) * 100 if close_prev > 0 else 0

        conditions = []

        # ---------------------------------------------------------------
        # KD1: RPS 条件（至少满足一个）
        # ---------------------------------------------------------------
        rps_50  = rps_data.get('rps_50',  0)
        rps_120 = rps_data.get('rps_120', 0)
        rps_250 = rps_data.get('rps_250', 0)

        kd1 = (rps_250 >= 87) or (rps_120 >= 90) or (rps_50 >= 90)
        if not kd1:
            return False, {}
        conditions.append(f"RPS({rps_50:.0f}/{rps_120:.0f}/{rps_250:.0f})")

        # ---------------------------------------------------------------
        # KD2: 成交量条件（至少满足一个）
        # ---------------------------------------------------------------
        vols_10     = volumes[-10:]
        avg_vol_10  = np.mean(vols_10)
        max_vol_10  = np.max(vols_10)

        fkd21 = volume_latest >= max_vol_10          # 10日成交量新高
        fkd22 = change_pct > 9.9                     # 涨幅>9.9%
        volume_ratio = volume_latest / avg_vol_10 if avg_vol_10 > 0 else 1
        fkd23 = volume_ratio > 2                     # 量比>2倍

        kd2 = fkd21 or fkd22 or fkd23
        if not kd2:
            return False, {}
        conditions.append(f"量比{volume_ratio:.1f}x")

        # ---------------------------------------------------------------
        # KD3: 价格位置和趋势（至少满足一个）
        # ---------------------------------------------------------------
        fkd31 = fkd32 = fkd33 = False

        if len(closes) >= 90:
            ma90      = np.mean(closes[-90:])
            ma90_prev = np.mean(closes[-95:-5]) if len(closes) >= 95 else ma90
            high_90   = np.max(highs[-90:])
            fkd31 = (close_latest > ma90) and (ma90 >= ma90_prev) and (high_latest >= high_90)

        if len(closes) >= 100:
            ma100      = np.mean(closes[-100:])
            ma100_prev = np.mean(closes[-105:-5]) if len(closes) >= 105 else ma100
            high_100   = np.max(highs[-100:])
            fkd32 = (close_latest > ma100) and (ma100 >= ma100_prev) and (high_latest >= high_100)

        if len(closes) >= 120:
            ma120      = np.mean(closes[-120:])
            ma120_prev = np.mean(closes[-122:-2]) if len(closes) >= 122 else ma120
            fkd33 = (close_latest > ma120) and (ma120 >= ma120_prev)

        kd3 = fkd31 or fkd32 or fkd33
        if not kd3:
            return False, {}
        conditions.append("位置趋势OK")

        # ---------------------------------------------------------------
        # KD4: 短期调整
        # ---------------------------------------------------------------
        low_15  = np.min(lows[-15:])
        low_50  = np.min(lows[-50:])
        high_250 = np.max(highs[-250:]) if len(highs) >= 250 else np.max(highs)

        kd4 = (low_15 > low_50 * 0.995) or (high_latest >= high_250)
        if not kd4:
            return False, {}
        conditions.append("短期调整OK")

        # ---------------------------------------------------------------
        # KD5: 中期调整（120日最大回撤<46%）
        # ---------------------------------------------------------------
        high_120 = np.max(highs[-120:]) if len(highs) >= 120 else np.max(highs)
        low_40   = np.min(lows[-40:])   if len(lows)  >= 40  else np.min(lows)

        if len(highs) >= 120:
            high_120_idx   = int(np.argmax(highs[-120:]))
            low_since_high = np.min(lows[-(120 - high_120_idx):])
            max_dd = (high_120 - low_since_high) / high_120 * 100 if high_120 > 0 else 0
        else:
            high_idx       = int(np.argmax(highs))
            low_since_high = np.min(lows[high_idx:])
            max_dd = (highs[high_idx] - low_since_high) / highs[high_idx] * 100 if highs[high_idx] > 0 else 0

        fkd5 = (low_40 / high_120 > 0.5) or (high_latest >= high_250)
        kd5  = (max_dd < 46) and fkd5
        if not kd5:
            return False, {}
        conditions.append(f"回撤{max_dd:.1f}%")

        # ---------------------------------------------------------------
        # KD6: 结构紧凑
        # ---------------------------------------------------------------
        low_100            = np.min(lows[-100:]) if len(lows) >= 100 else np.min(lows)
        current_high_ratio = high_latest / high_250 if high_250 > 0 else 0
        high_40            = np.max(highs[-40:]) if len(highs) >= 40 else np.max(highs)

        fkd41 = (low_15 > low_50) or (high_latest >= high_250)
        fkd42 = (low_15 == low_50) and (low_15 > low_100) and (current_high_ratio > 0.88)
        fkd43 = (low_15 == low_50) and (low_15 > low_100) and (current_high_ratio > 0.75) \
                and (high_latest >= high_40) and (change_pct > 7)

        kd6 = fkd41 or fkd42 or fkd43
        if not kd6:
            return False, {}
        conditions.append("结构紧凑")

        # ---------------------------------------------------------------
        # KD7: 当日涨幅≥5%
        # ---------------------------------------------------------------
        kd7 = change_pct >= 5
        if not kd7:
            return False, {}
        conditions.append(f"涨幅{change_pct:.1f}%")

        # ---------------------------------------------------------------
        # KD8: 换手率≤15%
        # ---------------------------------------------------------------
        turnover_rate = turnover.get('turnover_rate', 15)
        kd8 = turnover_rate <= 15
        if not kd8:
            return False, {}
        conditions.append(f"换手{turnover_rate:.1f}%")

        # ---------------------------------------------------------------
        # KD9: 昨日最低价偏离均线
        # ---------------------------------------------------------------
        if len(closes) >= 51:
            yesterday_low  = lows[-2]
            ma50_prev  = np.mean(closes[-51:-1])   # 昨日 MA50
            ma10_prev  = np.mean(closes[-11:-1])   # 昨日 MA10

            kd9 = (yesterday_low <= ma50_prev * 1.24) or (yesterday_low <= ma10_prev * 1.03)
            if not kd9:
                return False, {}
        # 数据不足时放宽

        # ---------------------------------------------------------------
        # 全部条件通过
        # ---------------------------------------------------------------
        return True, {
            'change_pct':   change_pct,
            'volume_ratio': volume_ratio,
            'max_dd':       max_dd,
            'conditions':   ' | '.join(conditions),
        }


# ===========================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("口袋支点策略（RPS修复版）")
    print("=" * 80)
    print()
    print("改进说明:")
    print("  - 修复前: RPS 使用单股票近似值（不准确）")
    print("  - 修复后: 预加载全市场数据，对同一天所有股票横向百分位排名（正确）")
    print()
    print("使用方法:")
    print("  python3 pocket_pivot_strategy.py")
    print()
    print("注意事项:")
    print("  1. 口袋支点必须同时满足9个条件")
    print("  2. 当日涨幅必须≥5%（KD7）是最主要的约束")
    print("  3. 必须有成交量配合")
    print("  4. 在震荡市/弱势市场可能筛选结果为0")
    print("  5. 建议结合火车头策略使用")
    print("  6. 设置止损位-5%")
    print("  7. 持仓周期: 短期-中期(5-15天)")
    print()
    print("=" * 80)
    print("📚 参考: https://mp.weixin.qq.com/s/k0gHe6465-etVZOadnwMPQ")
    print("=" * 80)
    print()

    strategy = PocketPivotStrategy()
    strategy.run_screening()
