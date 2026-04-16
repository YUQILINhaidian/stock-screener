#!/usr/bin/env python3
"""
股票行业信息管理器

从Baostock获取股票行业分类信息
"""

import json
import baostock as bs
from pathlib import Path
from datetime import datetime


class StockIndustryManager:
    """股票行业信息管理器"""
    
    def __init__(self):
        self.cache_file = Path.home() / '.vntrader' / 'stock_industries.json'
        self.industries = self.load_cache()
    
    def load_cache(self) -> dict:
        """加载缓存的行业信息"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_cache(self):
        """保存行业信息到缓存"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.industries, f, ensure_ascii=False, indent=2)
    
    def fetch_all_industries(self):
        """从Baostock获取所有股票行业信息"""
        print("=" * 80)
        print("从Baostock获取股票行业信息")
        print("=" * 80)
        
        # 登录Baostock
        lg = bs.login()
        if lg.error_code != '0':
            print(f'❌ 登录失败: {lg.error_msg}')
            return
        
        print('✅ 登录成功')
        
        # 查询行业分类
        rs = bs.query_stock_industry()
        
        if rs.error_code != '0':
            print(f'❌ 查询失败: {rs.error_msg}')
            bs.logout()
            return
        
        count = 0
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            code = row[1]  # sh.600000
            name = row[2]  # 浦发银行
            industry = row[3]  # J66货币金融服务
            
            # 转换代码格式
            if code.startswith('sh.'):
                symbol = code[3:]  # 600000
            elif code.startswith('sz.'):
                symbol = code[3:]
            else:
                continue
            
            # 解析行业代码，提取行业名称
            industry_name = self._parse_industry(industry)
            
            # 保存
            self.industries[symbol] = {
                'name': name,
                'industry': industry_name,
                'industry_code': industry
            }
            count += 1
            
            if count % 500 == 0:
                print(f"已处理: {count} 只股票")
        
        bs.logout()
        
        print(f"\n✅ 获取完成: {len(self.industries)} 只股票")
        
        # 保存到缓存
        self.save_cache()
        print(f"✅ 已保存到: {self.cache_file}")
    
    def _parse_industry(self, industry_code: str) -> str:
        """解析行业代码，返回行业名称"""
        if not industry_code:
            return ''
        
        # 行业代码格式：J66货币金融服务
        # 前面是代码，后面是名称
        # 提取中文名称部分
        import re
        match = re.search(r'[A-Z]\d+?(.+)', industry_code)
        if match:
            return match.group(1)
        return industry_code
    
    def get_industry(self, symbol: str) -> str:
        """
        获取股票行业
        
        Args:
            symbol: 股票代码，如 "600000" 或 "600000.SSE"
        
        Returns:
            行业名称
        """
        # 去掉交易所后缀
        if '.' in symbol:
            code = symbol.split('.')[0]
        else:
            code = symbol
        
        if code in self.industries:
            return self.industries[code].get('industry', '')
        return ''
    
    def get_industry_info(self, symbol: str) -> dict:
        """
        获取股票完整信息
        
        Args:
            symbol: 股票代码
        
        Returns:
            包含名称、行业等信息的字典
        """
        if '.' in symbol:
            code = symbol.split('.')[0]
        else:
            code = symbol
        
        if code in self.industries:
            return self.industries[code]
        return {'name': symbol, 'industry': '', 'industry_code': ''}


def main():
    """主函数"""
    manager = StockIndustryManager()
    
    # 如果缓存为空，重新获取
    if not manager.industries:
        print("缓存为空，正在获取行业信息...")
        manager.fetch_all_industries()
    else:
        print(f"已加载缓存: {len(manager.industries)} 只股票")
        print("\n示例股票行业:")
        for i, (symbol, info) in enumerate(list(manager.industries.items())[:10]):
            print(f"  {symbol}: {info['name']} - {info['industry']}")


if __name__ == "__main__":
    main()
