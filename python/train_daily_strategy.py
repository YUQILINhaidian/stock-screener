"""
火车每日观察选股策略
基于通达信公式"250706 火车每日观察选股公式源代码（可抗翠）"转换

策略逻辑：
1. MRGC（买入观察条件）
2. SXHCG（筛选候选股条件）
最终选股结果：SXHCG OR MRGC
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from vnpy.trader.database import get_database
from vnpy.trader.object import BarData


class TrainDailyStrategy:
    """火车每日观察选股策略"""
    
    # RPS周期
    RPS_PERIODS = [5, 10, 50, 120, 250]
    
    # 策略参数
    PARAMS = {
        # MRGC参数
        'turnover_rate_max': 25,        # 日线换手率上限(%)
        'max_drawdown_120': 0.50,       # 120天内最大回撤上限
        'max_drawdown_35': 0.35,        # 120天内最大回撤上限（严格版）
        'price_ratio_70': 0.70,         # 收盘价/一年最高价下限
        'price_ratio_80': 0.80,         # 收盘价/一年最高价下限（严格版）
        'price_ratio_85': 0.85,         # 收盘价/一年最高价下限（更严格版）
        
        # RPS阈值
        'rps_xg1_120': 96,              # XG1的RPS120阈值
        'rps_xg1_250': 96,              # XG1的RPS250阈值
        'rps_xg1_50': 95,               # XG1的RPS50阈值
        'rps_xg2': 97,                  # XG2的RPS阈值
        'rps_xg3': 98,                  # XG3的RPS阈值
        'rps_xg4': 95,                  # XG4的RPS阈值
        
        # SXHCG参数
        'rps_sum_min': 185,             # RPS120+RPS250之和下限
        'ma_days_above_250': 25,        # 30天内高于250日线的天数下限
        'ma_days_above_200': 25,        # 30天内高于200日线的天数下限
        'ma_days_above_20': 9,          # 10天内高于20日线的天数下限
        'ma_days_4': 3,                 # 4天内高于均线天数下限
        'max_drawdown_20': 0.25,        # 20天内最大回撤上限
        'turnover_rate_sxhcg': 15,      # SXHCG换手率上限(%)
    }
    
    def __init__(self):
        """初始化策略"""
        self.database = get_database()
        self.all_bars: Dict[str, pd.DataFrame] = {}
        self.rps_data: Dict[str, Dict[int, pd.Series]] = {}  # 旧版本兼容
        self.rps_wide_data: Dict[int, pd.DataFrame] = {}  # 新版本RPS存储
        
    def load_data(self) -> None:
        """从数据库加载所有股票数据"""
        print("正在加载数据库中的股票数据...")
        
        from vnpy.trader.constant import Interval
        
        # 获取所有股票概览
        overview = self.database.get_bar_overview()
        
        # 按股票代码分组
        bar_dict: Dict[str, List[BarData]] = {}
        
        for item in overview:
            if item.interval != Interval.DAILY:
                continue
            
            # 加载K线数据
            bars = self.database.load_bar_data(
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
        
        # 转换为DataFrame
        for key, bar_list in bar_dict.items():
            df = pd.DataFrame([{
                'datetime': bar.datetime,
                'open': bar.open_price,
                'high': bar.high_price,
                'low': bar.low_price,
                'close': bar.close_price,
                'volume': bar.volume,
                'turnover': bar.turnover,
            } for bar in bar_list])
            df = df.sort_values('datetime').reset_index(drop=True)
            self.all_bars[key] = df
        
        print(f"加载完成: {len(self.all_bars)} 只股票")
    
    def calculate_rps(self, period: int) -> pd.DataFrame:
        """计算所有股票的RPS值 - 返回宽格式DataFrame（股票为列，日期索引为行）"""
        print(f"正在计算{period}日RPS...")
        
        # 计算每只股票的涨跌幅
        returns_dict = {}
        for key, df in self.all_bars.items():
            if len(df) < period + 1:
                continue
            ret = (df['close'] / df['close'].shift(period) - 1) * 100
            returns_dict[key] = ret
        
        if not returns_dict:
            return pd.DataFrame()
        
        # 转换为DataFrame（股票为列，日期为行索引）
        returns_df = pd.DataFrame(returns_dict)
        
        print(f"  数据维度: {returns_df.shape[0]} 天, {returns_df.shape[1]} 只股票")
        
        # 使用向量化操作计算RPS
        # rank(axis=1) 对每行（每天）进行排名，pct=True返回百分位数
        # 注意：rank默认是升序，涨跌幅小的排名靠前
        rps_df = returns_df.rank(axis=1, method='average', pct=True) * 100
        
        print(f"  计算完成")
        return rps_df  # 直接返回宽格式DataFrame
    
    def get_rps_for_stock(self, symbol: str, period: int, date_idx: int) -> Optional[float]:
        """获取某股票某日的RPS值"""
        # 从宽格式DataFrame中查询
        if period not in self.rps_wide_data:
            return None
        rps_df = self.rps_wide_data[period]
        if symbol not in rps_df.columns:
            return None
        if date_idx in rps_df.index:
            return rps_df.loc[date_idx, symbol]
        return None
    
    def precalculate_all_rps(self) -> None:
        """预计算所有RPS值 - 优化版，直接存储宽格式DataFrame"""
        print("正在预计算所有RPS值...")
        
        for period in self.RPS_PERIODS:
            rps_df = self.calculate_rps(period)
            if not rps_df.empty:
                self.rps_wide_data[period] = rps_df
        
        print("RPS预计算完成")
    
    def calculate_turnover_rate(self, df: pd.DataFrame) -> pd.Series:
        """计算换手率 (假设没有流通股本数据，用成交量/平均成交量估算)"""
        # 由于没有CAPITAL数据，这里用成交量的相对值估算
        # 实际应该用: VOL/CAPITAL*100
        # 这里简化处理：用成交量/20日均量*100作为换手率的替代
        avg_volume = df['volume'].rolling(20).mean()
        turnover_rate = df['volume'] / avg_volume * 100
        return turnover_rate
    
    def calculate_drawdown(self, df: pd.DataFrame, lookback: int) -> Tuple[pd.Series, pd.Series]:
        """计算回撤幅度"""
        # 新高天数：从当前往前看，最近一个创新高(lookback天内)距今天数
        high_rolling = df['high'].rolling(lookback, min_periods=1).max()
        
        # 计算过去lookback天的最高点位置
        drawdowns = []
        for i in range(len(df)):
            if i < lookback:
                # 数据不足，取可用数据
                window_high = df['high'].iloc[:i+1].max()
            else:
                window_high = df['high'].iloc[i-lookback+1:i+1].max()
            
            # 找到新高点
            if i < lookback:
                new_high_idx = df['high'].iloc[:i+1].idxmax()
                new_high_days = i - new_high_idx
            else:
                new_high_idx = df['high'].iloc[i-lookback+1:i+1].idxmax()
                new_high_days = i - new_high_idx
            
            if new_high_days == 0:
                # 当天创新高，回撤为0
                drawdowns.append(0)
            else:
                # 从新高点到当前，找最低点
                if i - new_high_days >= 0:
                    new_high_price = df['high'].iloc[i - new_high_days]
                    low_since_new_high = df['low'].iloc[i - new_high_days + 1:i + 1].min()
                    dd = (new_high_price - low_since_new_high) / new_high_price
                    drawdowns.append(dd)
                else:
                    drawdowns.append(0)
        
        return pd.Series(drawdowns, index=df.index)
    
    def check_mrgc(self, df: pd.DataFrame, symbol: str, idx: int) -> Tuple[bool, str]:
        """
        检查MRGC（买入观察条件）
        返回: (是否满足, 满足的条件描述)
        """
        if idx < 250:  # 需要至少250天数据
            return False, ""
        
        row = df.iloc[idx]
        
        # 计算换手率
        turnover_rate = self.calculate_turnover_rate(df).iloc[idx]
        
        # MRGC00: 换手率 < 25%
        if turnover_rate >= self.PARAMS['turnover_rate_max']:
            return False, ""
        
        # 计算120天内最大回撤
        lookback_120 = min(120, idx + 1)
        drawdown_120 = self.calculate_drawdown(df, lookback_120).iloc[idx]
        
        # MRGC001: 过去120天最大回撤 <= 50%
        if drawdown_120 > self.PARAMS['max_drawdown_120']:
            return False, ""
        
        # MRGC002: 收盘价 >= 一年最高价的70%
        high_250 = df['high'].iloc[max(0, idx-249):idx+1].max()
        price_ratio = row['close'] / high_250
        if price_ratio < self.PARAMS['price_ratio_70']:
            return False, ""
        
        # 获取RPS值
        rps_50 = self.get_rps_for_stock(symbol, 50, idx)
        rps_120 = self.get_rps_for_stock(symbol, 120, idx)
        rps_250 = self.get_rps_for_stock(symbol, 250, idx)
        
        if rps_120 is None or rps_250 is None:
            return False, ""
        
        # XG1: 过去5天有创250日新高，且RPS条件
        xg11 = False
        for i in range(max(0, idx-4), idx+1):
            if df['close'].iloc[i] >= df['close'].iloc[max(0, i-249):i+1].max():
                xg11 = True
                break
        
        xg12 = (rps_120 >= self.PARAMS['rps_xg1_120']) or (rps_250 >= self.PARAMS['rps_xg1_250'])
        xg13 = (rps_120 >= self.PARAMS['rps_xg1_50']) and (rps_50 is not None and rps_50 >= self.PARAMS['rps_xg1_50'])
        
        if xg11 and (xg12 or xg13):
            return True, "XG1: 创新高+高RPS"
        
        # XG2: 收盘价 >= 一年最高价85%，且RPS >= 97
        high_250_all = df['high'].iloc[max(0, idx-249):idx+1].max()
        xg21 = row['close'] / high_250_all >= self.PARAMS['price_ratio_85']
        xg22 = (rps_120 >= self.PARAMS['rps_xg2']) or (rps_250 >= self.PARAMS['rps_xg2'])
        
        if xg21 and xg22:
            return True, "XG2: 接近新高+高RPS"
        
        # XG3: 收盘价 >= 一年最高价70%，且RPS >= 98
        xg31 = row['close'] / high_250_all >= self.PARAMS['price_ratio_70']
        xg32 = (rps_120 >= self.PARAMS['rps_xg3']) or (rps_250 >= self.PARAMS['rps_xg3'])
        
        if xg31 and xg32:
            return True, "XG3: 中等位置+超高RPS"
        
        # XG4: 过去120天最大回撤 <= 35%，收盘价 >= 一年最高价80%，且RPS >= 95
        # 计算严格回撤
        drawdown_strict = self.calculate_drawdown(df, lookback_120).iloc[idx]
        xg41 = (drawdown_strict <= self.PARAMS['max_drawdown_35']) and (price_ratio >= self.PARAMS['price_ratio_80'])
        xg42 = (rps_120 >= self.PARAMS['rps_xg4']) or (rps_250 >= self.PARAMS['rps_xg4'])
        
        if xg41 and xg42:
            return True, "XG4: 低回撤+高RPS"
        
        return False, ""
    
    def check_sxhcg(self, df: pd.DataFrame, symbol: str, idx: int) -> Tuple[bool, str]:
        """
        检查SXHCG（筛选候选股条件）
        返回: (是否满足, 满足的条件描述)
        """
        if idx < 250:
            return False, ""
        
        row = df.iloc[idx]
        
        # 获取RPS值
        rps_120 = self.get_rps_for_stock(symbol, 120, idx)
        rps_250 = self.get_rps_for_stock(symbol, 250, idx)
        
        if rps_120 is None or rps_250 is None:
            return False, ""
        
        # SXHCG1: RPS120 + RPS250 > 185
        if rps_120 + rps_250 <= self.PARAMS['rps_sum_min']:
            return False, ""
        
        # 计算均线
        ma_10 = df['close'].rolling(10).mean().iloc[idx]
        ma_20 = df['close'].rolling(20).mean().iloc[idx]
        ma_200 = df['close'].rolling(200).mean().iloc[idx]
        ma_250 = df['close'].rolling(250).mean().iloc[idx]
        
        if pd.isna(ma_200) or pd.isna(ma_250):
            return False, ""
        
        # SXHCG2: 均线条件
        # 收盘价站上20日线
        if row['close'] <= ma_20:
            return False, ""
        
        # 过去30天高于250日线的天数 >= 25
        window_30 = min(30, idx + 1)
        above_250 = sum(df['close'].iloc[idx-window_30+1:idx+1] > df['close'].rolling(250).mean().iloc[idx-window_30+1:idx+1])
        if above_250 < self.PARAMS['ma_days_above_250']:
            return False, ""
        
        # 过去30天高于200日线的天数 >= 25
        above_200 = sum(df['close'].iloc[idx-window_30+1:idx+1] > df['close'].rolling(200).mean().iloc[idx-window_30+1:idx+1])
        if above_200 < self.PARAMS['ma_days_above_200']:
            return False, ""
        
        # 过去10天高于20日线的天数 >= 9 或 过去4天同时高于10日线和20日线 >= 3天
        window_10 = min(10, idx + 1)
        above_20_10d = sum(df['close'].iloc[idx-window_10+1:idx+1] > df['close'].rolling(20).mean().iloc[idx-window_10+1:idx+1])
        
        window_4 = min(4, idx + 1)
        ma_10_series = df['close'].rolling(10).mean()
        ma_20_series = df['close'].rolling(20).mean()
        above_both = 0
        for i in range(idx-window_4+1, idx+1):
            if df['close'].iloc[i] > ma_10_series.iloc[i] and df['close'].iloc[i] > ma_20_series.iloc[i]:
                above_both += 1
        
        if above_20_10d < self.PARAMS['ma_days_above_20'] and above_both < self.PARAMS['ma_days_4']:
            return False, ""
        
        # SXHCG3: 过去20天最大回撤 <= 25%，收盘价 >= 一年最高价80%
        drawdown_20 = self.calculate_drawdown(df, 20).iloc[idx]
        high_250 = df['high'].iloc[max(0, idx-249):idx+1].max()
        price_ratio = row['close'] / high_250
        
        if drawdown_20 > self.PARAMS['max_drawdown_20'] or price_ratio < self.PARAMS['price_ratio_80']:
            return False, ""
        
        # SXHCG4: 均线趋势条件
        # 过去5天20日线上升 且 10日线在20日线上方
        ma_20_rising = all(ma_20_series.iloc[idx-i] >= ma_20_series.iloc[idx-i-1] for i in range(5) if idx-i-1 >= 0)
        ma_10_above_20 = all(ma_10_series.iloc[idx-i] >= ma_20_series.iloc[idx-i] for i in range(5) if idx-i >= 0)
        
        # 或者当前10日线向上、20日线向上、10日线在20日线上方
        ma_10_up = ma_10 >= ma_10_series.iloc[idx-1] if idx > 0 else False
        ma_20_up = ma_20 >= ma_20_series.iloc[idx-1] if idx > 0 else False
        ma_10_above_20_now = ma_10 >= ma_20
        
        if not ((ma_20_rising and ma_10_above_20) or (ma_10_up and ma_20_up and ma_10_above_20_now)):
            return False, ""
        
        # SXHCG5: 换手率 < 15%
        turnover_rate = self.calculate_turnover_rate(df).iloc[idx]
        if turnover_rate >= self.PARAMS['turnover_rate_sxhcg']:
            return False, ""
        
        # SXHCG6: 过去120天最大回撤 <= 50%
        lookback_120 = min(120, idx + 1)
        drawdown_120 = self.calculate_drawdown(df, lookback_120).iloc[idx]
        if drawdown_120 > self.PARAMS['max_drawdown_120']:
            return False, ""
        
        return True, "SXHCG: 筛选候选股"
    
    def run_screening(self, date: datetime = None) -> pd.DataFrame:
        """
        运行选股策略
        date: 选股日期，None表示最新日期
        """
        print("=" * 60)
        print("开始火车每日观察选股")
        print("=" * 60)
        
        # 加载数据
        if not self.all_bars:
            self.load_data()
        
        # 预计算RPS（检查新版本的rps_wide_data）
        if not self.rps_wide_data:
            self.precalculate_all_rps()
        
        results = []
        
        for symbol, df in self.all_bars.items():
            if len(df) < 250:
                continue
            
            # 确定选股日期的索引
            if date:
                mask = df['datetime'] <= date
                if not mask.any():
                    continue
                idx = mask.idxmax()  # 获取最后一个匹配的索引
            else:
                idx = len(df) - 1  # 最新日期
            
            # 检查MRGC条件
            mrgc_pass, mrgc_reason = self.check_mrgc(df, symbol, idx)
            
            # 检查SXHCG条件
            sxhcg_pass, sxhcg_reason = self.check_sxhcg(df, symbol, idx)
            
            # 满足任一条件即入选
            if mrgc_pass or sxhcg_pass:
                row = df.iloc[idx]
                reason = []
                if mrgc_pass:
                    reason.append(f"MRGC: {mrgc_reason}")
                if sxhcg_pass:
                    reason.append(f"SXHCG: {sxhcg_reason}")
                
                # 获取RPS值
                rps_50 = self.get_rps_for_stock(symbol, 50, idx) or 0
                rps_120 = self.get_rps_for_stock(symbol, 120, idx) or 0
                rps_250 = self.get_rps_for_stock(symbol, 250, idx) or 0
                
                results.append({
                    'symbol': symbol,
                    'datetime': row['datetime'],
                    'close': row['close'],
                    'rps_50': round(rps_50, 2),
                    'rps_120': round(rps_120, 2),
                    'rps_250': round(rps_250, 2),
                    'rps_sum': round(rps_120 + rps_250, 2),
                    'reason': '; '.join(reason)
                })
        
        if not results:
            print("未找到符合条件的股票")
            return pd.DataFrame()
        
        result_df = pd.DataFrame(results)
        result_df = result_df.sort_values('rps_sum', ascending=False)
        
        print(f"\n找到 {len(result_df)} 只符合条件的股票")
        
        return result_df
    
    def generate_report(self, date: datetime = None) -> None:
        """生成选股报告"""
        result_df = self.run_screening(date)
        
        if result_df.empty:
            return
        
        print("\n" + "=" * 60)
        print("火车每日观察选股结果")
        print("=" * 60)
        print(f"选股日期: {result_df['datetime'].iloc[0]}")
        print(f"入选股票数: {len(result_df)}")
        print("-" * 60)
        
        # 显示前20只股票
        display_cols = ['symbol', 'close', 'rps_50', 'rps_120', 'rps_250', 'rps_sum', 'reason']
        print(result_df[display_cols].head(20).to_string(index=False))
        
        # 保存结果
        output_dir = "/Users/yinchang/.vntrader/train_daily"
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, f"train_daily_screening_{datetime.now().strftime('%Y%m%d')}.csv")
        result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n数据已保存到: {output_file}")


def main():
    """主函数"""
    strategy = TrainDailyStrategy()
    strategy.generate_report()


if __name__ == "__main__":
    main()
