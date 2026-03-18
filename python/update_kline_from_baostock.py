#!/usr/bin/env python3
"""
从Baostock下载最新K线数据并更新到VNPy数据库

功能：
1. 从Baostock下载指定日期范围的K线数据
2. 导入到VNPy数据库
3. 支持增量更新（只下载缺失的日期）
"""

import sys
import os
from datetime import datetime, timedelta
import baostock as bs
import pandas as pd

sys.path.insert(0, os.path.expanduser("~"))

from vnpy.trader.database import get_database
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData


class BaostockKlineUpdater:
    """Baostock K线数据更新器"""
    
    def __init__(self):
        self.db = get_database()
        self.lg = None
    
    def login_baostock(self):
        """登录Baostock"""
        print("登录Baostock...")
        self.lg = bs.login()
        if self.lg.error_code != '0':
            print(f'❌ 登录失败: {self.lg.error_msg}')
            return False
        print('✅ 登录成功')
        return True
    
    def logout_baostock(self):
        """登出Baostock"""
        if self.lg:
            bs.logout()
            print('✅ 登出Baostock')
    
    def get_stock_list(self):
        """获取股票列表"""
        print("\n获取股票列表...")
        
        # 从VNPy数据库获取已有股票
        overviews = self.db.get_bar_overview()
        
        stock_list = []
        for overview in overviews:
            if overview.exchange in [Exchange.SSE, Exchange.SZSE]:
                # 转换为Baostock格式
                if overview.exchange == Exchange.SSE:
                    code = f"sh.{overview.symbol}"
                else:
                    code = f"sz.{overview.symbol}"
                
                stock_list.append({
                    'code': code,
                    'symbol': overview.symbol,
                    'exchange': overview.exchange,
                    'name': overview.symbol
                })
        
        print(f"获取到 {len(stock_list)} 只股票")
        return stock_list
    
    def download_kline(
        self,
        code: str,
        start_date: str,
        end_date: str
    ):
        """
        下载单只股票的K线数据
        
        Args:
            code: Baostock股票代码（如sh.600000）
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
        
        Returns:
            DataFrame或None
        """
        rs = bs.query_history_k_data_plus(
            code,
            "date,code,open,high,low,close,volume,amount,turn",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="3"  # 后复权
        )
        
        if rs.error_code != '0':
            return None
        
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return None
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        # 数据类型转换
        df['open'] = pd.to_numeric(df['open'], errors='coerce')
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # 去除无效数据
        df = df.dropna(subset=['open', 'high', 'low', 'close'])
        
        return df if len(df) > 0 else None
    
    def save_to_vnpy(
        self,
        df: pd.DataFrame,
        symbol: str,
        exchange: Exchange
    ) -> int:
        """
        保存数据到VNPy数据库
        
        Args:
            df: K线数据DataFrame
            symbol: 股票代码
            exchange: 交易所
        
        Returns:
            保存的K线数量
        """
        bars = []
        
        for _, row in df.iterrows():
            bar = BarData(
                symbol=symbol,
                exchange=exchange,
                datetime=datetime.strptime(row['date'], '%Y-%m-%d'),
                interval=Interval.DAILY,
                volume=float(row['volume']),
                turnover=float(row['amount']) if 'amount' in row and pd.notna(row['amount']) else 0.0,  # 成交额
                open_price=float(row['open']),
                high_price=float(row['high']),
                low_price=float(row['low']),
                close_price=float(row['close']),
                gateway_name="DB"
            )
            bars.append(bar)
        
        if bars:
            self.db.save_bar_data(bars)
            return len(bars)
        
        return 0
    
    def update_all_stocks(
        self,
        start_date: str = None,
        end_date: str = None,
        max_stocks: int = None
    ):
        """
        更新所有股票的K线数据
        
        Args:
            start_date: 开始日期（YYYY-MM-DD），默认为7天前
            end_date: 结束日期（YYYY-MM-DD），默认为今天
            max_stocks: 最大更新股票数（测试用）
        """
        # 默认日期范围
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        print("=" * 80)
        print("Baostock K线数据更新")
        print("=" * 80)
        print(f"日期范围: {start_date} ~ {end_date}")
        print()
        
        # 登录Baostock
        if not self.login_baostock():
            return
        
        try:
            # 获取股票列表
            stock_list = self.get_stock_list()
            
            if max_stocks:
                stock_list = stock_list[:max_stocks]
                print(f"⚠️  测试模式：只更新前 {max_stocks} 只股票")
            
            # 逐个下载
            total = len(stock_list)
            success_count = 0
            failed_count = 0
            total_bars = 0
            
            print(f"\n开始下载...")
            print("-" * 80)
            
            for idx, stock in enumerate(stock_list):
                code = stock['code']
                symbol = stock['symbol']
                exchange = stock['exchange']
                
                try:
                    # 下载数据
                    df = self.download_kline(code, start_date, end_date)
                    
                    if df is not None and len(df) > 0:
                        # 保存到数据库
                        bar_count = self.save_to_vnpy(df, symbol, exchange)
                        
                        if bar_count > 0:
                            success_count += 1
                            total_bars += bar_count
                            
                            if (idx + 1) % 100 == 0:
                                print(f"进度: {idx+1}/{total} ({(idx+1)/total*100:.1f}%) - "
                                      f"成功:{success_count}, 失败:{failed_count}, "
                                      f"K线数:{total_bars}")
                        else:
                            failed_count += 1
                    else:
                        failed_count += 1
                
                except Exception as e:
                    failed_count += 1
                    if failed_count <= 5:
                        print(f"  ⚠️  {symbol}: {str(e)[:50]}")
            
            print(f"\n{'=' * 80}")
            print("更新完成")
            print(f"{'=' * 80}")
            print(f"成功: {success_count} 只股票")
            print(f"失败: {failed_count} 只股票")
            print(f"总K线数: {total_bars} 条")
            print(f"平均: {total_bars/success_count:.1f} 条/股" if success_count > 0 else "")
            
        finally:
            # 登出
            self.logout_baostock()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='从Baostock更新K线数据')
    parser.add_argument('--start', help='开始日期(YYYY-MM-DD)')
    parser.add_argument('--end', help='结束日期(YYYY-MM-DD)')
    parser.add_argument('--max', type=int, help='最大更新股票数（测试用）')
    
    args = parser.parse_args()
    
    updater = BaostockKlineUpdater()
    updater.update_all_stocks(
        start_date=args.start,
        end_date=args.end,
        max_stocks=args.max
    )


if __name__ == "__main__":
    main()
