#!/usr/bin/env python3
"""
股票名称查询工具

从Baostock获取股票名称，并缓存到本地
"""

import sys
import os
import json
import baostock as bs
from datetime import datetime

sys.path.insert(0, os.path.expanduser("~"))


class StockNameManager:
    """股票名称管理器"""
    
    def __init__(self):
        self.cache_file = os.path.expanduser("~/.vntrader/stock_names.json")
        self.names = self.load_cache()
    
    def load_cache(self) -> dict:
        """加载缓存的股票名称"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_cache(self):
        """保存股票名称到缓存"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.names, f, ensure_ascii=False, indent=2)
    
    def fetch_all_names(self):
        """从Baostock获取所有股票名称"""
        print("=" * 80)
        print("从Baostock获取股票名称")
        print("=" * 80)
        
        # 登录Baostock
        lg = bs.login()
        if lg.error_code != '0':
            print(f'❌ 登录失败: {lg.error_msg}')
            return
        
        print('✅ 登录成功')
        
        # 获取所有股票
        rs = bs.query_stock_basic()
        
        if rs.error_code != '0':
            print(f'❌ 查询失败: {rs.error_msg}')
            bs.logout()
            return
        
        count = 0
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            code = row[0]  # 代码，如 sh.600000
            name = row[1]  # 名称
            
            # 转换代码格式
            if code.startswith('sh.'):
                symbol = code[3:] + '.SSE'
            elif code.startswith('sz.'):
                symbol = code[3:] + '.SZSE'
            else:
                continue
            
            # 同时保存带后缀和不带后缀的键，方便查询
            self.names[code[3:]] = name  # 不带后缀，如 "688566"
            self.names[symbol] = name    # 带后缀，如 "688566.SSE"
            count += 1
            
            if count % 500 == 0:
                print(f"已处理: {count} 只股票")
        
        bs.logout()
        
        print(f"\n✅ 获取完成: {len(self.names)} 只股票")
        
        # 保存到缓存
        self.save_cache()
        print(f"✅ 已保存到: {self.cache_file}")
    
    def get_name(self, symbol: str) -> str:
        """
        获取股票名称
        
        Args:
            symbol: 股票代码，如 "600000.SSE" 或 "600000"
        
        Returns:
            股票名称，如果未找到返回代码
        """
        # 如果symbol包含交易所后缀，去掉它
        if '.' in symbol:
            code = symbol.split('.')[0]
        else:
            code = symbol
        
        return self.names.get(code, symbol)
    
    def update_dataframe(self, df, symbol_column='symbol', name_column='name'):
        """
        为DataFrame添加股票名称列
        
        Args:
            df: 包含股票代码的DataFrame
            symbol_column: 股票代码列名
            name_column: 要添加的名称列名
        
        Returns:
            添加了名称列的DataFrame
        """
        df[name_column] = df[symbol_column].apply(self.get_name)
        return df


def main():
    """主函数"""
    manager = StockNameManager()
    
    # 如果缓存为空或过期，重新获取
    if not manager.names:
        print("缓存为空，正在获取股票名称...")
        manager.fetch_all_names()
    else:
        print(f"已加载缓存: {len(manager.names)} 只股票")
        print("\n示例股票名称:")
        for i, (symbol, name) in enumerate(list(manager.names.items())[:10]):
            print(f"  {symbol}: {name}")
    
    # 提供交互式查询
    print("\n输入股票代码查询名称（输入q退出）:")
    while True:
        symbol = input(">>> ").strip()
        if symbol.lower() == 'q':
            break
        if symbol:
            name = manager.get_name(symbol)
            print(f"  {symbol}: {name}")


if __name__ == "__main__":
    main()
