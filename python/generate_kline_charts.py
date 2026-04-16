#!/usr/bin/env python3
"""
通用股票K线图生成工具
支持任意策略的筛选结果
"""

import pandas as pd
import mplfinance as mpf
import os
import sys
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, os.path.expanduser("~"))

from vnpy.trader.database import get_database
from vnpy.trader.constant import Exchange, Interval

# 尝试导入股票名称管理器
try:
    from stock_name_manager import StockNameManager
    HAS_NAME_MANAGER = True
except ImportError:
    HAS_NAME_MANAGER = False


# 策略配置
STRATEGY_CONFIG = {
    'three_line_red': {
        'name': '三线红策略',
        'file_pattern': 'three_line_red_*.csv',
        'default_dir': 'three_line_red'
    },
    'monthly_reversal': {
        'name': '月线反转策略',
        'file_pattern': 'monthly_reversal_*.csv',
        'default_dir': 'monthly_reversal'
    },
    'pocket_pivot': {
        'name': '口袋支点策略',
        'file_pattern': 'pocket_pivot_*.csv',
        'default_dir': 'pocket_pivot'
    },
    'arc_bottom': {
        'name': '圆弧底策略',
        'file_pattern': 'arc_bottom_*.csv',
        'default_dir': 'arc_bottom'
    },
    'first_limit_up': {
        'name': '首次涨停策略',
        'file_pattern': 'first_limit_up_*.csv',
        'default_dir': 'first_limit_up'
    },
    'blue_diamond': {
        'name': '蓝色钻石策略',
        'file_pattern': 'blue_diamond_*.csv',
        'default_dir': 'blue_diamond'
    },
    'train_advanced': {
        'name': '火车头高级策略',
        'file_pattern': 'train_daily_advanced_*.csv',
        'default_dir': 'train_advanced'
    },
    'stage2': {
        'name': '第二阶段策略',
        'file_pattern': 'stage2_*.csv',
        'default_dir': 'stage2'
    },
    'near_year_high': {
        'name': '接近一年新高策略',
        'file_pattern': 'near_year_high_*.csv',
        'default_dir': 'near_year_high'
    },
    'sxhcg3': {
        'name': '顺向火车轨3.0策略',
        'file_pattern': 'sxhcg3_*.csv',
        'default_dir': 'sxhcg3'
    },
    'mid_term_adjustment': {
        'name': '中期调整后选股策略',
        'file_pattern': 'mid_term_adjustment_*.csv',
        'default_dir': 'mid_term_adjustment'
    }
}


def detect_strategy_from_csv(csv_path: str) -> str:
    """
    根据CSV文件名自动检测策略类型
    
    Args:
        csv_path: CSV文件路径
    
    Returns:
        策略key
    """
    filename = os.path.basename(csv_path)
    
    for strategy_key, config in STRATEGY_CONFIG.items():
        if filename.startswith(config['file_pattern'].replace('*', '')):
            return strategy_key
    
    return 'unknown'


def get_strategy_config(strategy_key: str) -> dict:
    """
    获取策略配置
    
    Args:
        strategy_key: 策略key
    
    Returns:
        策略配置字典
    """
    if strategy_key in STRATEGY_CONFIG:
        return STRATEGY_CONFIG[strategy_key]
    
    return {
        'name': '未知策略',
        'file_pattern': '*.csv',
        'default_dir': strategy_key
    }


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


def parse_symbol(full_symbol):
    """
    解析股票代码
    
    Args:
        full_symbol: 如 "000890.SZSE" 或整数
    
    Returns:
        (symbol, exchange)
    """
    # 转换为字符串
    full_symbol = str(full_symbol)
    
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


def get_stock_name(symbol: str) -> str:
    """
    获取股票名称
    
    Args:
        symbol: 股票代码
    
    Returns:
        股票名称
    """
    if HAS_NAME_MANAGER:
        name_manager = StockNameManager()
        return name_manager.get_name(symbol)
    return symbol


def plot_stock_chart(symbol_full: str, df: pd.DataFrame, output_dir: str, extra_info: dict = None):
    """
    绘制单个股票的K线图（含支撑位和阻力位）
    
    Args:
        symbol_full: 完整股票代码
        df: K线数据
        output_dir: 输出目录
        extra_info: 额外信息字典（如RPS、价格等）
    """
    if df is None or df.empty:
        print(f"  ⚠️  {symbol_full}: 数据为空")
        return None
    
    # 获取股票名称
    stock_name = get_stock_name(symbol_full)
    
    # 计算支撑位和阻力位
    levels = calculate_support_resistance(df)
    
    # 准备标题（包含股票名称）
    title = f"{stock_name} ({symbol_full})"
    if extra_info:
        # 根据不同策略显示不同信息
        info_parts = []
        if 'rps_5' in extra_info:
            info_parts.append(f"RPS5={extra_info['rps_5']:.1f}")
        if 'rps_50' in extra_info:
            info_parts.append(f"RPS50={extra_info['rps_50']:.1f}")
        if 'rps_120' in extra_info:
            info_parts.append(f"RPS120={extra_info['rps_120']:.1f}")
        if 'rps_250' in extra_info:
            info_parts.append(f"RPS250={extra_info['rps_250']:.1f}")
        if 'close' in extra_info:
            info_parts.append(f"价格={extra_info['close']:.2f}")
        if 'ratio_30_120' in extra_info:
            info_parts.append(f"30/120比={extra_info['ratio_30_120']:.2f}")
        
        if info_parts:
            title += "\n" + " ".join(info_parts)
    
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


def generate_index_html(output_dir: str, df: pd.DataFrame, strategy_name: str):
    """生成图表索引HTML页面"""
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{strategy_name}K线图（含支撑位/阻力位）</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }}
        .legend {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 30px;
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-line {{
            width: 40px;
            height: 2px;
        }}
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
            gap: 30px;
        }}
        .chart-item {{
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
            background: white;
            transition: transform 0.3s;
        }}
        .chart-item:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }}
        .chart-title {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            font-weight: bold;
        }}
        .chart-img {{
            width: 100%;
            display: block;
        }}
        .chart-info {{
            padding: 15px;
            background: #f8f9fa;
        }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
            font-size: 14px;
        }}
        .label {{
            color: #666;
        }}
        .value {{
            font-weight: bold;
            color: #333;
        }}
        .rps-high {{
            color: #d4380d;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 {strategy_name}K线图</h1>
        <div class="subtitle">含支撑位/阻力位标记 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-line" style="border-top: 2px dashed green;"></div>
                <span>20日支撑位</span>
            </div>
            <div class="legend-item">
                <div class="legend-line" style="border-top: 2px dashed red;"></div>
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
        # 获取symbol和exchange，并转换为字符串
        symbol = str(row.get('symbol', row.get('code', '')))
        exchange = str(row.get('exchange', ''))
        
        # 组合成完整代码格式
        if exchange:
            symbol_full = f"{symbol}.{exchange}"
        else:
            symbol_full = symbol
        
        img_file = f"{symbol_full.replace('.', '_')}.png"
        
        # 获取股票名称
        stock_name = get_stock_name(symbol_full)
        
        # 获取显示信息
        close_price = row.get('close', row.get('latest_price', row.get('price', 0)))
        
        html_content += f"""
            <div class="chart-item">
                <div class="chart-title">{stock_name} ({symbol_full})</div>
                <img src="{img_file}" alt="{stock_name} ({symbol_full})" class="chart-img">
                <div class="chart-info">
                    <div class="info-row">
                        <span class="label">收盘价:</span>
                        <span class="value">{close_price:.2f} ¥</span>
                    </div>
"""
        
        # 根据可用字段添加RPS信息
        for rps_field in ['rps_5', 'rps_50', 'rps_120', 'rps_250', 'RPS5', 'RPS50', 'RPS120', 'RPS250']:
            if rps_field in row and pd.notna(row[rps_field]):
                rps_value = row[rps_field]
                rps_label = rps_field.replace('_', ' ').upper()
                html_content += f"""
                    <div class="info-row">
                        <span class="label">{rps_label}:</span>
                        <span class="value rps-high">{rps_value:.2f}</span>
                    </div>
"""
        
        # 添加30/120比值（月线反转特有）
        if 'ratio_30_120' in row and pd.notna(row['ratio_30_120']):
            html_content += f"""
                    <div class="info-row">
                        <span class="label">30/120比值:</span>
                        <span class="value rps-high">{row['ratio_30_120']:.2f}</span>
                    </div>
"""
        
        html_content += """
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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成股票K线图')
    parser.add_argument('--csv', type=str, help='指定CSV文件路径')
    parser.add_argument('--output', type=str, help='指定输出目录')
    parser.add_argument('--strategy', type=str, help='指定策略名称')
    parser.add_argument('--top', type=int, default=20, help='生成前N只股票的K线图（默认20）')
    
    args = parser.parse_args()
    
    # 确定CSV文件路径
    csv_path = None
    strategy_key = None
    
    if args.csv:
        csv_path = args.csv
        strategy_key = args.strategy or detect_strategy_from_csv(csv_path)
    else:
        # 自动查找最新的筛选结果
        vntrader_dir = os.path.expanduser("~/.vntrader")
        screen_dir = os.path.join(vntrader_dir, "screen_results")
        
        # 如果screen_results目录存在，从中查找
        if os.path.exists(screen_dir):
            csv_files = []
            for file in os.listdir(screen_dir):
                if file.endswith('.csv'):
                    csv_files.append(os.path.join(screen_dir, file))
            
            if csv_files:
                csv_path = max(csv_files, key=os.path.getmtime)
                strategy_key = detect_strategy_from_csv(csv_path)
        
        # 如果没找到，尝试从vntrader根目录查找（兼容旧版本）
        if not csv_path:
            csv_files = []
            for file in os.listdir(vntrader_dir):
                if file.endswith('.csv') and not file.startswith('stock_'):
                    csv_files.append(os.path.join(vntrader_dir, file))
            
            if csv_files:
                csv_path = max(csv_files, key=os.path.getmtime)
                strategy_key = detect_strategy_from_csv(csv_path)
    
    if not csv_path or not os.path.exists(csv_path):
        print("❌ 未找到筛选结果文件")
        print("用法: python3 generate_kline_charts.py --csv <csv文件路径> --strategy <策略名称>")
        print("\n支持的策略:")
        for key, config in STRATEGY_CONFIG.items():
            print(f"  - {key}: {config['name']}")
        return
    
    # 获取策略配置
    strategy_config = get_strategy_config(strategy_key)
    strategy_name = strategy_config['name']
    
    print("=" * 80)
    print(f"{strategy_name}K线图生成工具")
    print("=" * 80)
    print(f"读取文件: {csv_path}")
    
    # 读取CSV
    df = pd.read_csv(csv_path)
    print(f"共 {len(df)} 只股票")
    
    # 确定输出目录
    if args.output:
        output_dir = args.output
    else:
        output_dir = os.path.expanduser(f"~/.vntrader/charts/{strategy_config['default_dir']}")
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"输出目录: {output_dir}")
    
    # 选择Top N股票生成K线图
    top_n = min(args.top, len(df))
    print(f"\n生成前 {top_n} 只股票的K线图...")
    
    success_count = 0
    failed_count = 0
    
    for idx, row in df.head(top_n).iterrows():
        # 获取symbol和exchange，支持分开的列或合并的格式
        symbol = str(row.get('symbol', row.get('code', '')))
        exchange_str = str(row.get('exchange', ''))
        
        # 组合完整代码
        if exchange_str:
            symbol_full = f"{symbol}.{exchange_str}"
        else:
            symbol_full = symbol
        
        print(f"\n[{idx+1}/{top_n}] {symbol_full}")
        
        # 解析股票代码（如果exchange列存在，直接使用）
        if exchange_str:
            exchange_map = {
                'SZSE': Exchange.SZSE,
                'SSE': Exchange.SSE,
                'BSE': Exchange.BSE
            }
            exchange = exchange_map.get(exchange_str, Exchange.SZSE)
        else:
            # 否则从完整代码解析
            _, exchange = parse_symbol(symbol_full)
        
        # 加载K线数据
        stock_df = load_stock_data(symbol, exchange, days=120)
        
        if stock_df is None or stock_df.empty:
            print(f"  ⚠️  无法加载数据")
            failed_count += 1
            continue
        
        # 准备额外信息（传递所有可用字段）
        extra_info = row.to_dict()
        
        # 绘制K线图
        result = plot_stock_chart(symbol_full, stock_df, output_dir, extra_info)
        
        if result:
            success_count += 1
        else:
            failed_count += 1
    
    # 生成索引HTML
    print(f"\n生成图表索引页面...")
    generate_index_html(output_dir, df.head(top_n), strategy_name)
    
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


if __name__ == "__main__":
    main()
