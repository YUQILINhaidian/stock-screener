#!/usr/bin/env python3
"""
生成三线红股票的K线图
"""

import pandas as pd
import mplfinance as mpf
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.expanduser("~"))

from vnpy.trader.database import get_database
from vnpy.trader.constant import Exchange, Interval
from stock_name_manager import StockNameManager


def load_stock_data(symbol: str, exchange: Exchange, days: int = 120) -> pd.DataFrame:
    """
    从VNPy数据库加载K线数据
    
    Args:
        symbol: 股票代码（不含交易所后缀）
        exchange: 交易所
        days: 加载最近N天的数据
    
    Returns:
        DataFrame with OHLCV data
    """
    db = get_database()
    
    # 加载数据
    bars = db.load_bar_data(
        symbol=symbol,
        exchange=exchange,
        interval=Interval.DAILY,
        start=datetime.now() - timedelta(days=days),
        end=datetime.now()
    )
    
    if not bars:
        return None
    
    # 转换为DataFrame
    data = []
    for bar in bars:
        data.append({
            'Date': bar.datetime,
            'Open': bar.open_price,
            'High': bar.high_price,
            'Low': bar.low_price,
            'Close': bar.close_price,
            'Volume': bar.volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('Date', inplace=True)
    
    return df


def parse_symbol(full_symbol: str):
    """
    解析股票代码
    
    Args:
        full_symbol: 如 "000890.SZSE"
    
    Returns:
        (symbol, exchange)
    """
    if '.' in full_symbol:
        symbol, exchange_str = full_symbol.split('.')
        exchange_map = {
            'SZSE': Exchange.SZSE,
            'SSE': Exchange.SSE,
            'BSE': Exchange.BSE
        }
        return symbol, exchange_map.get(exchange_str, Exchange.SZSE)
    else:
        return full_symbol, Exchange.SZSE


def calculate_support_resistance(df: pd.DataFrame):
    """
    计算支撑位和阻力位
    
    Args:
        df: K线数据
    
    Returns:
        dict with support and resistance levels
    """
    levels = {}
    
    # 近20日支撑位和阻力位
    if len(df) >= 20:
        recent_20 = df.tail(20)
        levels['support_20'] = recent_20['Low'].min()
        levels['resistance_20'] = recent_20['High'].max()
    
    # 近60日支撑位和阻力位
    if len(df) >= 60:
        recent_60 = df.tail(60)
        levels['support_60'] = recent_60['Low'].min()
        levels['resistance_60'] = recent_60['High'].max()
    
    # 全部数据的支撑位和阻力位
    levels['support_all'] = df['Low'].min()
    levels['resistance_all'] = df['High'].max()
    
    return levels


def plot_stock_chart(symbol_full: str, df: pd.DataFrame, output_dir: str, rps_info: dict = None):
    """
    绘制单个股票的K线图（含支撑位和阻力位）
    
    Args:
        symbol_full: 完整股票代码
        df: K线数据
        output_dir: 输出目录
        rps_info: RPS信息字典
    """
    if df is None or df.empty:
        print(f"  ⚠️  {symbol_full}: 数据为空")
        return
    
    # 获取股票名称
    name_manager = StockNameManager()
    stock_name = name_manager.get_name(symbol_full)
    
    # 计算支撑位和阻力位
    levels = calculate_support_resistance(df)
    
    # 准备标题（包含股票名称）
    title = f"{stock_name} ({symbol_full})"
    if rps_info:
        title += f"\nRPS5={rps_info.get('rps_5', 0):.1f} RPS120={rps_info.get('rps_120', 0):.1f} RPS250={rps_info.get('rps_250', 0):.1f}"
        title += f" 价格={rps_info.get('latest_price', 0):.2f}"
    
    # 设置样式
    mc = mpf.make_marketcolors(
        up='red',      # 上涨为红色（中国习惯）
        down='green',  # 下跌为绿色
        edge='inherit',
        wick='inherit',
        volume='in',
        alpha=0.9
    )
    
    s = mpf.make_mpf_style(
        marketcolors=mc,
        gridstyle='--',
        y_on_right=False
    )
    
    # 准备水平线（支撑位和阻力位）
    hlines = []
    colors = []
    linestyles = []
    linewidths = []
    labels = []
    
    # 20日支撑位（绿色虚线）
    if 'support_20' in levels:
        hlines.append(levels['support_20'])
        colors.append('green')
        linestyles.append('--')
        linewidths.append(1.5)
    
    # 20日阻力位（红色虚线）
    if 'resistance_20' in levels:
        hlines.append(levels['resistance_20'])
        colors.append('red')
        linestyles.append('--')
        linewidths.append(1.5)
    
    # 60日支撑位（深绿色点线）
    if 'support_60' in levels and levels['support_60'] != levels['support_20']:
        hlines.append(levels['support_60'])
        colors.append('darkgreen')
        linestyles.append(':')
        linewidths.append(1.2)
    
    # 60日阻力位（深红色点线）
    if 'resistance_60' in levels and levels['resistance_60'] != levels['resistance_20']:
        hlines.append(levels['resistance_60'])
        colors.append('darkred')
        linestyles.append(':')
        linewidths.append(1.2)
    
    # 绘制K线图
    output_file = os.path.join(output_dir, f"{symbol_full.replace('.', '_')}.png")
    
    try:
        # 创建附加图表配置
        apd = []
        
        mpf.plot(
            df,
            type='candle',
            style=s,
            title=title,
            ylabel='Price (¥)',
            volume=True,
            hlines=dict(hlines=hlines, colors=colors, linestyle=linestyles, linewidths=linewidths),
            savefig=output_file,
            figsize=(14, 8),
            tight_layout=True
        )
        print(f"  ✅ {symbol_full}: {output_file}")
        
        # 打印支撑位和阻力位信息
        if 'support_20' in levels and 'resistance_20' in levels:
            print(f"     支撑位(20日): {levels['support_20']:.2f} | 阻力位(20日): {levels['resistance_20']:.2f}")
        
        return output_file
    except Exception as e:
        print(f"  ❌ {symbol_full}: {e}")
        return None


def main():
    """主函数"""
    print("=" * 80)
    print("三线红股票K线图生成工具")
    print("=" * 80)
    
    # 读取筛选结果
    csv_files = []
    vntrader_dir = os.path.expanduser("~/.vntrader")
    
    for file in os.listdir(vntrader_dir):
        if file.startswith("three_line_red_") and file.endswith(".csv"):
            csv_files.append(os.path.join(vntrader_dir, file))
    
    if not csv_files:
        print("❌ 未找到三线红筛选结果文件")
        return
    
    # 使用最新的文件
    latest_csv = max(csv_files, key=os.path.getmtime)
    print(f"\n读取文件: {latest_csv}")
    
    df = pd.read_csv(latest_csv)
    print(f"共 {len(df)} 只股票")
    
    # 创建输出目录
    output_dir = os.path.expanduser("~/.vntrader/charts/three_line_red")
    os.makedirs(output_dir, exist_ok=True)
    
    # 选择Top 20股票生成K线图
    top_n = min(20, len(df))
    print(f"\n生成前 {top_n} 只股票的K线图...")
    
    success_count = 0
    failed_count = 0
    
    for idx, row in df.head(top_n).iterrows():
        symbol_full = row['symbol']
        print(f"\n[{idx+1}/{top_n}] {symbol_full}")
        
        # 解析股票代码
        symbol, exchange = parse_symbol(symbol_full)
        
        # 加载K线数据
        stock_df = load_stock_data(symbol, exchange, days=120)
        
        if stock_df is None or stock_df.empty:
            print(f"  ⚠️  无法加载数据")
            failed_count += 1
            continue
        
        # 准备RPS信息
        rps_info = {
            'rps_5': row.get('rps_5', 0),
            'rps_10': row.get('rps_10', 0),
            'rps_50': row.get('rps_50', 0),
            'rps_120': row.get('rps_120', 0),
            'rps_250': row.get('rps_250', 0),
            'latest_price': row.get('latest_price', 0)
        }
        
        # 绘制K线图
        result = plot_stock_chart(symbol_full, stock_df, output_dir, rps_info)
        
        if result:
            success_count += 1
        else:
            failed_count += 1
    
    # 生成索引HTML
    print(f"\n生成图表索引页面...")
    generate_index_html(output_dir, df.head(top_n))
    
    print("\n" + "=" * 80)
    print("K线图生成完成")
    print("=" * 80)
    print(f"成功: {success_count}")
    print(f"失败: {failed_count}")
    print(f"图表目录: {output_dir}")
    print(f"索引页面: {os.path.join(output_dir, 'index.html')}")
    print("=" * 80)
    
    # 自动打开索引页面
    index_html = os.path.join(output_dir, 'index.html')
    if os.path.exists(index_html):
        import subprocess
        subprocess.run(['open', index_html])


def generate_index_html(output_dir: str, df: pd.DataFrame):
    """生成图表索引HTML页面"""
    
    # 获取股票名称管理器
    name_manager = StockNameManager()
    
    html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>三线红股票K线图（含支撑位/阻力位）</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .legend {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 30px;
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .legend-line {
            width: 40px;
            height: 2px;
        }
        .support-20 { background: green; }
        .resistance-20 { background: red; }
        .support-60 { background: darkgreen; border-top: 2px dotted darkgreen; }
        .resistance-60 { background: darkred; border-top: 2px dotted darkred; }
        .chart-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
            gap: 30px;
        }
        .chart-item {
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
            background: white;
            transition: transform 0.3s;
        }
        .chart-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }
        .chart-title {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            font-weight: bold;
        }
        .chart-img {
            width: 100%;
            display: block;
        }
        .chart-info {
            padding: 15px;
            background: #f8f9fa;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
            font-size: 14px;
        }
        .label {
            color: #666;
        }
        .value {
            font-weight: bold;
            color: #333;
        }
        .rps-high {
            color: #d4380d;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 三线红股票K线图</h1>
        <div class="subtitle">含支撑位/阻力位标记</div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-line support-20" style="border-top: 2px dashed green;"></div>
                <span>20日支撑位</span>
            </div>
            <div class="legend-item">
                <div class="legend-line resistance-20" style="border-top: 2px dashed red;"></div>
                <span>20日阻力位</span>
            </div>
            <div class="legend-item">
                <div class="legend-line" style="border-top: 2px dotted darkgreen;"></div>
                <span>60日支撑位</span>
            </div>
            <div class="legend-item">
                <div class="legend-line" style="border-top: 2px dotted darkred;"></div>
                <span>60日阻力位</span>
            </div>
        </div>
        
        <div class="chart-grid">
"""
    
    for idx, row in df.iterrows():
        symbol_full = row['symbol']
        img_file = f"{symbol_full.replace('.', '_')}.png"
        
        # 获取股票名称
        stock_name = name_manager.get_name(symbol_full)
        
        html_content += f"""
            <div class="chart-item">
                <div class="chart-title">{stock_name} ({symbol_full})</div>
                <img src="{img_file}" alt="{stock_name} ({symbol_full})" class="chart-img">
                <div class="chart-info">
                    <div class="info-row">
                        <span class="label">最新价:</span>
                        <span class="value">{row.get('latest_price', 0):.2f} ¥</span>
                    </div>
                    <div class="info-row">
                        <span class="label">RPS5:</span>
                        <span class="value rps-high">{row.get('rps_5', 0):.2f}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">RPS120:</span>
                        <span class="value rps-high">{row.get('rps_120', 0):.2f}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">RPS250:</span>
                        <span class="value rps-high">{row.get('rps_250', 0):.2f}</span>
                    </div>
                </div>
            </div>
"""
    
    html_content += """
        </div>
    </div>
</body>
</html>
"""
    
    with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)


if __name__ == "__main__":
    main()
