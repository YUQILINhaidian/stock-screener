#!/usr/bin/env python3
"""
RPS+基本面数据可视化工具（增强版）
整合RPS技术指标和基本面数据
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import sys
import os

sys.path.insert(0, os.path.expanduser("~"))
sys.path.insert(0, os.path.join(os.path.expanduser("~"), "fundamentals"))

from train_daily_strategy import TrainDailyStrategy
from fundamentals.data_loader import FundamentalDataLoader


class EnhancedRPSViewer:
    """RPS+基本面数据可视化工具"""
    
    def __init__(self):
        """初始化"""
        self.rps_strategy = TrainDailyStrategy()
        self.fundamental_loader = FundamentalDataLoader()
    
    def generate_html(self, output_file: str = None, date: datetime = None, max_stocks: int = 500) -> str:
        """
        生成增强版HTML页面
        
        Args:
            output_file: 输出文件路径
            date: 指定日期
            max_stocks: 最多显示的股票数量（为了加快生成速度）
        
        Returns:
            生成的HTML文件路径
        """
        print("=" * 60)
        print("RPS+基本面数据可视化工具（增强版）")
        print("=" * 60)
        
        # 加载基本面数据
        print("\n1. 加载基本面数据...")
        fundamental_df = self.fundamental_loader.get_all_stocks_with_price()
        print(f"   已加载 {len(fundamental_df)} 只股票的基本面数据")
        
        # 加载RPS数据
        print("\n2. 加载RPS数据...")
        if not self.rps_strategy.all_bars:
            self.rps_strategy.load_data()
        
        if not self.rps_strategy.rps_wide_data:
            self.rps_strategy.precalculate_all_rps()
        
        # 提取和合并数据
        print("\n3. 合并RPS和基本面数据...")
        merged_df = self._merge_data(fundamental_df, date, max_stocks)
        
        # 生成HTML
        print("\n4. 生成HTML页面...")
        html_content = self._create_html(merged_df)
        
        # 保存文件
        if output_file is None:
            output_file = f"/Users/yinchang/.vntrader/rps_fundamental_viewer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✅ HTML页面已生成: {output_file}")
        print(f"   在浏览器中打开此文件即可查看")
        print(f"   提示: 可以使用以下命令在浏览器中打开:")
        print(f"   open {output_file}")
        
        return output_file
    
    def _merge_data(self, fundamental_df: pd.DataFrame, date: datetime = None, max_stocks: int = 500) -> pd.DataFrame:
        """合并RPS和基本面数据"""
        
        # 获取RPS数据日期索引
        if date is None:
            date_idx = self.rps_strategy.rps_wide_data[120].index[-1]
        else:
            date_idx = None
            for idx in self.rps_strategy.rps_wide_data[120].index:
                if idx <= date:
                    date_idx = idx
            if date_idx is None:
                raise ValueError(f"找不到日期 {date} 的数据")
        
        print(f"   使用日期: {date_idx}")
        
        # 提取RPS数据
        rps_data_list = []
        
        for symbol in fundamental_df['symbol'].head(max_stocks):
            rps_row = {'symbol': symbol}
            
            for period in [5, 10, 50, 120, 250]:
                if period in self.rps_strategy.rps_wide_data:
                    rps_df = self.rps_strategy.rps_wide_data[period]
                    if symbol in rps_df.columns and date_idx in rps_df.index:
                        rps_val = rps_df.loc[date_idx, symbol]
                        if not pd.isna(rps_val):
                            rps_row[f'rps_{period}'] = round(rps_val, 2)
            
            rps_data_list.append(rps_row)
        
        rps_df = pd.DataFrame(rps_data_list)
        
        # 合并
        merged = pd.merge(
            fundamental_df.head(max_stocks),
            rps_df,
            on='symbol',
            how='left'
        )
        
        # 计算RPS之和
        if 'rps_120' in merged.columns and 'rps_250' in merged.columns:
            merged['rps_sum'] = merged['rps_120'].fillna(0) + merged['rps_250'].fillna(0)
        
        # 价格区间分类
        def get_price_category(price):
            if pd.isna(price) or price == 0:
                return "未知"
            elif price < 5:
                return "<5元"
            elif price < 10:
                return "5-10元"
            elif price < 20:
                return "10-20元"
            elif price < 50:
                return "20-50元"
            else:
                return">50元"
        
        merged['price_category'] = merged['latest_price'].apply(get_price_category)
        
        print(f"   合并后共 {len(merged)} 只股票")
        
        return merged
    
    def _create_html(self, df: pd.DataFrame) -> str:
        """创建HTML内容"""
        
        # 准备数据
        data_json = df[[
            'symbol', 'latest_price', 'price_category',
            'rps_5', 'rps_10', 'rps_50', 'rps_120', 'rps_250', 'rps_sum'
        ]].fillna('').to_json(orient='records', force_ascii=False)
        
        # 统计信息
        total_stocks = len(df)
        rps120_high = len(df[df['rps_120'] >= 90]) if 'rps_120' in df.columns else 0
        rps250_high = len(df[df['rps_250'] >= 90]) if 'rps_250' in df.columns else 0
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RPS+基本面数据查看器</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .stats {{
            padding: 20px 30px;
            background: #f8f9fa;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        
        .stat-item {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 8px;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .controls {{
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}
        
        .search-box input {{
            padding: 10px 15px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            min-width: 250px;
        }}
        
        .filter-btn {{
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }}
        
        .filter-btn:hover {{
            background: #5568d3;
            transform: translateY(-2px);
        }}
        
        .filter-btn.active {{
            background: #764ba2;
        }}
        
        .table-container {{
            padding: 20px 30px;
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        
        th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
            position: sticky;
            top: 0;
            cursor: pointer;
            user-select: none;
        }}
        
        th:hover {{
            background: #e9ecef;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .rps-high {{
            background: #d4edda;
            color: #155724;
            font-weight: bold;
        }}
        
        .rps-medium {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .rps-low {{
            color: #666;
        }}
        
        .price-tag {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            background: #e9ecef;
        }}
        
        .no-results {{
            text-align: center;
            padding: 40px;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 RPS + 基本面数据查看器</h1>
            <p>技术面（RPS）+ 基本面整合分析</p>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-label">总股票数</div>
                <div class="stat-value" id="totalStocks">{total_stocks}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">RPS120>90</div>
                <div class="stat-value" id="rps120High">{rps120_high}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">RPS250>90</div>
                <div class="stat-value" id="rps250High">{rps250_high}</div>
            </div>
        </div>
        
        <div class="controls">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="搜索股票代码...">
            </div>
            <button class="filter-btn" onclick="filterByRPS(90)">RPS>90</button>
            <button class="filter-btn" onclick="filterByRPS(95)">RPS>95</button>
            <button class="filter-btn" onclick="filterByPrice(5, 20)">5-20元</button>
            <button class="filter-btn" onclick="filterByPrice(10, 30)">10-30元</button>
            <button class="filter-btn" onclick="resetFilter()">重置</button>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th onclick="sortTable('symbol')">股票代码</th>
                        <th onclick="sortTable('latest_price')">最新价</th>
                        <th onclick="sortTable('price_category')">价格区间</th>
                        <th onclick="sortTable('rps_5')">RPS5</th>
                        <th onclick="sortTable('rps_10')">RPS10</th>
                        <th onclick="sortTable('rps_50')">RPS50</th>
                        <th onclick="sortTable('rps_120')">RPS120</th>
                        <th onclick="sortTable('rps_250')">RPS250</th>
                        <th onclick="sortTable('rps_sum')">RPS之和</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        const originalData = {data_json};
        let filteredData = [...originalData];
        let sortColumn = 'rps_120';
        let sortAsc = false;
        
        function getRPSClass(value) {{
            if (!value || value === '') return 'rps-low';
            if (value >= 90) return 'rps-high';
            if (value >= 80) return 'rps-medium';
            return 'rps-low';
        }}
        
        function renderTable() {{
            const tbody = document.getElementById('tableBody');
            
            if (filteredData.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="9" class="no-results">未找到匹配的股票</td></tr>';
                return;
            }}
            
            const rows = filteredData.map(row => `
                <tr>
                    <td>${{row.symbol}}</td>
                    <td>${{row.latest_price || '-'}}</td>
                    <td><span class="price-tag">${{row.price_category || '-'}}</span></td>
                    <td class="${{getRPSClass(row.rps_5)}}">${{row.rps_5 || '-'}}</td>
                    <td class="${{getRPSClass(row.rps_10)}}">${{row.rps_10 || '-'}}</td>
                    <td class="${{getRPSClass(row.rps_50)}}">${{row.rps_50 || '-'}}</td>
                    <td class="${{getRPSClass(row.rps_120)}}">${{row.rps_120 || '-'}}</td>
                    <td class="${{getRPSClass(row.rps_250)}}">${{row.rps_250 || '-'}}</td>
                    <td class="${{getRPSClass(row.rps_sum)}}">${{row.rps_sum || '-'}}</td>
                </tr>
            `).join('');
            
            tbody.innerHTML = rows;
        }}
        
        function sortTable(column) {{
            if (sortColumn === column) {{
                sortAsc = !sortAsc;
            }} else {{
                sortColumn = column;
                sortAsc = false;
            }}
            
            filteredData.sort((a, b) => {{
                let aVal = a[column];
                let bVal = b[column];
                
                if (aVal === '' || aVal === null) aVal = sortAsc ? Infinity : -Infinity;
                if (bVal === '' || bVal === null) bVal = sortAsc ? Infinity : -Infinity;
                
                if (typeof aVal === 'number' && typeof bVal === 'number') {{
                    return sortAsc ? aVal - bVal : bVal - aVal;
                }}
                
                return sortAsc ? String(aVal).localeCompare(String(bVal)) : String(bVal).localeCompare(String(aVal));
            }});
            
            renderTable();
        }}
        
        function filterByRPS(threshold) {{
            filteredData = originalData.filter(row => 
                (row.rps_120 && row.rps_120 >= threshold) || 
                (row.rps_250 && row.rps_250 >= threshold)
            );
            renderTable();
        }}
        
        function filterByPrice(min, max) {{
            filteredData = originalData.filter(row => 
                row.latest_price && row.latest_price >= min && row.latest_price <= max
            );
            renderTable();
        }}
        
        function resetFilter() {{
            filteredData = [...originalData];
            document.getElementById('searchInput').value = '';
            renderTable();
        }}
        
        document.getElementById('searchInput').addEventListener('input', (e) => {{
            const keyword = e.target.value.toLowerCase();
            filteredData = originalData.filter(row => 
                row.symbol.toLowerCase().includes(keyword)
            );
            renderTable();
        }});
        
        // 初始渲染
        renderTable();
    </script>
</body>
</html>"""
        
        return html


def main():
    """主函数"""
    print("\n提示: 这是增强版RPS查看器，整合了基本面数据")
    print("由于完整加载需要较长时间，默认只显示前500只股票\n")
    
    viewer = EnhancedRPSViewer()
    
    # 生成HTML（只显示500只股票以加快速度）
    output_file = viewer.generate_html(max_stocks=500)
    
    # 自动打开浏览器
    import subprocess
    subprocess.run(['open', output_file])


if __name__ == "__main__":
    main()
