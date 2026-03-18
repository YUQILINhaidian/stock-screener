#!/usr/bin/env python3
"""
策略筛选结果汇总分析工具

功能:
1. 读取不同策略的最新筛选结果CSV
2. 整合各策略的筛选指标明细
3. 生成K线图
4. 创建HTML页面展示K线图和指标明细

用法:
  python3 ~/strategy_summary.py                    # 汇总所有策略
  python3 ~/strategy_summary.py --strategy pocket  # 仅汇总口袋支点
  python3 ~/strategy_summary.py --generate-charts  # 生成K线图
"""

import sys
import os
import glob
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.expanduser("~"))

from vnpy.trader.database import get_database
from vnpy.trader.constant import Exchange, Interval

# 尝试导入mplfinance用于K线图生成
try:
    import mplfinance as mpf
    MPLFINANCE_AVAILABLE = True
except ImportError:
    MPLFINANCE_AVAILABLE = False
    print("⚠️ mplfinance未安装，K线图生成功能不可用")


# ═══════════════════════════════════════════════════════════════════════
# 策略配置
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class StrategyConfig:
    """策略配置"""
    name: str           # 策略名称
    display_name: str   # 显示名称
    csv_pattern: str    # CSV文件匹配模式
    key_metrics: List[str]  # 关键指标字段
    description: str = ""   # 策略描述


STRATEGIES = {
    'pocket_pivot': StrategyConfig(
        name='pocket_pivot',
        display_name='口袋支点策略',
        csv_pattern='pocket_pivot_*.csv',
        key_metrics=['price', 'change_pct', 'volume_ratio', 'rps_50', 'rps_120', 'rps_250', 'max_dd'],
        description='捕捉强势股调整后的启动买点，当日涨幅≥5% + 放量 + RPS强势'
    ),
    'train_advanced': StrategyConfig(
        name='train_advanced',
        display_name='火车头高级策略',
        csv_pattern='train_daily_advanced_*.csv',
        key_metrics=['price', 'rps_50', 'rps_120', 'rps_250', 'rps_sum', 'max_dd_120', 'strategy'],
        description='MRGC + SXHCG 双策略组合，捕捉强势股'
    ),
    'arc_bottom': StrategyConfig(
        name='arc_bottom',
        display_name='圆弧底策略',
        csv_pattern='arc_bottom_*.csv',
        key_metrics=['close', 'cond2', 'cond4', 'cond6', 'converge_ratio'],
        description='多重综合均线确认底部反转，低频高质量信号'
    ),
    'first_limit_up': StrategyConfig(
        name='first_limit_up',
        display_name='首次涨停&一线红',
        csv_pattern='first_limit_up_*.csv',
        key_metrics=['close', 'change_pct', 'limit_pct', 'rps_max', 'rps_50', 'rps_120', 'rps_250'],
        description='RPS强度 + 涨停板 + 一线红，捕捉首次涨停突破'
    ),
    'blue_diamond': StrategyConfig(
        name='blue_diamond',
        display_name='蓝色钻石策略',
        csv_pattern='blue_diamond_*.csv',
        key_metrics=['close', 'rps_20', 'rps_50', 'max_dd', 'turnover_rate'],
        description='捕捉强势股的第二波上涨机会'
    ),
}


# ═══════════════════════════════════════════════════════════════════════
# 核心类
# ═══════════════════════════════════════════════════════════════════════

class StrategySummary:
    """策略筛选结果汇总分析"""

    def __init__(self):
        self.db = get_database()
        self.vntrader_dir = os.path.expanduser("~/.vntrader")
        self.output_dir = os.path.join(self.vntrader_dir, "strategy_summary")
        os.makedirs(self.output_dir, exist_ok=True)

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

    def find_latest_csv(self, strategy_key: str) -> Optional[str]:
        """查找策略的最新CSV文件"""
        if strategy_key not in STRATEGIES:
            return None

        config = STRATEGIES[strategy_key]
        pattern = os.path.join(self.vntrader_dir, config.csv_pattern)
        files = glob.glob(pattern)

        if not files:
            return None

        # 返回最新的文件
        return max(files, key=os.path.getmtime)

    def load_strategy_results(self, strategy_key: str) -> Optional[pd.DataFrame]:
        """加载策略筛选结果"""
        csv_file = self.find_latest_csv(strategy_key)
        if not csv_file:
            return None

        df = pd.read_csv(csv_file)
        df['_source_file'] = os.path.basename(csv_file)
        df['_strategy'] = strategy_key
        return df

    def get_all_strategy_summaries(self) -> Dict[str, dict]:
        """获取所有策略的汇总信息"""
        summaries = {}

        for key, config in STRATEGIES.items():
            df = self.load_strategy_results(key)
            if df is not None and len(df) > 0:
                summaries[key] = {
                    'config': config,
                    'count': len(df),
                    'file': df['_source_file'].iloc[0],
                    'top_stocks': df.head(5).to_dict('records'),
                    'all_stocks': df.to_dict('records'),  # 添加完整股票列表
                    'metrics_stats': self._calculate_metrics_stats(df, config.key_metrics)
                }

        return summaries

    def _calculate_metrics_stats(self, df: pd.DataFrame, metrics: List[str]) -> dict:
        """计算指标统计"""
        stats = {}
        for metric in metrics:
            if metric in df.columns:
                values = df[metric].dropna()
                # 只对数值类型计算统计
                if len(values) > 0 and pd.api.types.is_numeric_dtype(values):
                    stats[metric] = {
                        'mean': round(float(values.mean()), 2),
                        'median': round(float(values.median()), 2),
                        'min': round(float(values.min()), 2),
                        'max': round(float(values.max()), 2),
                    }
        return stats

    def print_summary(self, strategy_key: str = None):
        """打印策略汇总"""
        print("=" * 80)
        print("📊 策略筛选结果汇总")
        print("=" * 80)
        print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        if strategy_key:
            # 单个策略
            self._print_single_strategy(strategy_key)
        else:
            # 所有策略
            summaries = self.get_all_strategy_summaries()
            total_stocks = sum(s['count'] for s in summaries.values())

            print(f"📈 共 {len(summaries)} 个策略有筛选结果，合计 {total_stocks} 只股票\n")

            for key, summary in summaries.items():
                config = summary['config']
                print(f"┌{'─' * 76}┐")
                print(f"│ {config.display_name} ({summary['count']}只){' ' * (50 - len(config.display_name) - len(str(summary['count'])))}│")
                print(f"│ {config.description[:70]}{' ' * (70 - len(config.description[:70]))}│")
                print(f"│ 文件: {summary['file'][:60]}{' ' * (60 - len(summary['file'][:60]))}│")
                print(f"└{'─' * 76}┘")

                # 显示Top 5
                print("\n  Top 5 股票:")
                for i, stock in enumerate(summary['top_stocks'], 1):
                    symbol = stock.get('symbol', '')
                    name = stock.get('name', self.get_stock_name(symbol))
                    price = stock.get('price', stock.get('close', 0))
                    print(f"    {i}. {symbol} {name[:6]:<6} ¥{price:.2f}")

                print()

    def _print_single_strategy(self, strategy_key: str):
        """打印单个策略详情"""
        if strategy_key not in STRATEGIES:
            print(f"❌ 未知策略: {strategy_key}")
            print(f"   可用策略: {list(STRATEGIES.keys())}")
            return

        df = self.load_strategy_results(strategy_key)
        if df is None:
            print(f"❌ 未找到策略 {strategy_key} 的筛选结果")
            return

        config = STRATEGIES[strategy_key]
        print(f"\n📋 {config.display_name}")
        print(f"   描述: {config.description}")
        print(f"   文件: {df['_source_file'].iloc[0]}")
        print(f"   股票数: {len(df)}")
        print()

        # 显示关键指标统计
        print("📊 关键指标统计:")
        stats = self._calculate_metrics_stats(df, config.key_metrics)
        for metric, values in stats.items():
            print(f"   {metric}: 均值={values['mean']} 中位数={values['median']} 范围=[{values['min']}, {values['max']}]")

        print()

        # 显示所有股票
        print("📈 筛选结果明细:")
        print(f"   {'排名':^4} {'代码':^14} {'名称':^8} ", end='')
        for metric in config.key_metrics[:4]:
            print(f"{metric[:8]:^10} ", end='')
        print()
        print("   " + "-" * 70)

        for i, row in df.iterrows():
            symbol = row.get('symbol', '')
            name = row.get('name', self.get_stock_name(symbol))
            print(f"   {i+1:^4} {symbol:^14} {str(name)[:6]:^8} ", end='')
            for metric in config.key_metrics[:4]:
                val = row.get(metric, '-')
                if isinstance(val, float):
                    print(f"{val:>9.2f} ", end='')
                else:
                    print(f"{str(val)[:8]:>9} ", end='')
            print()

    def generate_kline_charts(self, strategy_key: str = None) -> int:
        """生成K线图"""
        if not MPLFINANCE_AVAILABLE:
            print("❌ mplfinance未安装，无法生成K线图")
            print("   安装命令: pip install mplfinance")
            return 0

        generated = 0

        if strategy_key:
            strategies = {strategy_key: STRATEGIES[strategy_key]}
        else:
            strategies = STRATEGIES

        for key, config in strategies.items():
            df = self.load_strategy_results(key)
            if df is None or len(df) == 0:
                continue

            print(f"\n📊 生成 {config.display_name} K线图...")

            chart_dir = os.path.join(self.output_dir, key, 'charts')
            os.makedirs(chart_dir, exist_ok=True)

            for _, row in df.iterrows():
                symbol = row.get('symbol', '')
                if not symbol:
                    continue

                try:
                    chart_file = self._generate_single_chart(symbol, chart_dir, row)
                    if chart_file:
                        generated += 1
                except Exception as e:
                    print(f"  ❌ {symbol}: {e}")

        return generated

    def _generate_single_chart(self, symbol: str, output_dir: str, info: dict) -> Optional[str]:
        """生成单只股票的K线图"""
        code, exchange_str = symbol.split('.')
        exchange = Exchange(exchange_str)

        # 加载K线数据
        bars = self.db.load_bar_data(
            symbol=code,
            exchange=exchange,
            interval=Interval.DAILY,
            start=datetime.now() - timedelta(days=180),
            end=datetime.now()
        )

        if len(bars) < 20:
            return None

        # 转换为DataFrame
        df = pd.DataFrame([{
            'Date': b.datetime,
            'Open': b.open_price,
            'High': b.high_price,
            'Low': b.low_price,
            'Close': b.close_price,
            'Volume': b.volume,
        } for b in bars])
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)

        # 计算均线
        df['MA5'] = df['Close'].rolling(5).mean()
        df['MA10'] = df['Close'].rolling(10).mean()
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA50'] = df['Close'].rolling(50).mean()

        # 构建标题
        name = info.get('name', self.get_stock_name(symbol))
        title = f"{name} ({symbol})"

        # 添加RPS信息
        rps_info = []
        for key in ['rps_50', 'rps_120', 'rps_250', 'rps_max', 'rps_sum']:
            if key in info and not pd.isna(info[key]):
                rps_info.append(f"{key.split('_')[-1]}={info[key]:.1f}")
        if rps_info:
            title += f"\nRPS: {', '.join(rps_info)}"

        # 样式
        mc = mpf.make_marketcolors(
            up='red', down='green',
            edge='inherit', wick='inherit',
            volume='in', alpha=0.9
        )
        s = mpf.make_mpf_style(
            marketcolors=mc,
            gridstyle='--',
            y_on_right=False
        )

        # 附加图
        apd = [
            mpf.make_addplot(df['MA5'], color='orange', width=1),
            mpf.make_addplot(df['MA10'], color='purple', width=1),
            mpf.make_addplot(df['MA20'], color='blue', width=1.2),
            mpf.make_addplot(df['MA50'], color='gray', width=1),
        ]

        output_file = os.path.join(output_dir, f"{symbol.replace('.', '_')}.png")

        mpf.plot(
            df,
            type='candle',
            style=s,
            title=title,
            ylabel='Price (¥)',
            volume=True,
            addplot=apd,
            savefig=output_file,
            figsize=(14, 8),
            tight_layout=True
        )

        return output_file

    def generate_html_report(self, strategy_key: str = None, generate_charts: bool = True) -> str:
        """生成HTML汇总报告"""
        summaries = self.get_all_strategy_summaries()

        if strategy_key:
            summaries = {k: v for k, v in summaries.items() if k == strategy_key}

        if not summaries:
            print("❌ 没有可汇总的策略结果")
            return ""

        # 先生成K线图
        chart_files = {}
        if generate_charts and MPLFINANCE_AVAILABLE:
            print("\n📊 生成K线图...")
            chart_files = self._generate_all_charts(summaries)

        html_file = os.path.join(self.output_dir, f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")

        html_content = self._build_html(summaries, chart_files)

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\n✅ HTML报告已生成: {html_file}")
        return html_file

    def _generate_all_charts(self, summaries: Dict[str, dict]) -> Dict[str, List[str]]:
        """生成所有策略的K线图，返回图表文件路径字典"""
        chart_files = {}

        for key, summary in summaries.items():
            chart_dir = os.path.join(self.output_dir, key, 'charts')
            os.makedirs(chart_dir, exist_ok=True)
            chart_files[key] = []

            print(f"  正在生成 {summary['config'].display_name} K线图...")

            for stock in summary['all_stocks']:
                symbol = stock.get('symbol', '')
                if not symbol:
                    continue

                try:
                    chart_file = self._generate_single_chart(symbol, chart_dir, stock)
                    if chart_file:
                        # 使用相对路径
                        rel_path = f"{key}/charts/{os.path.basename(chart_file)}"
                        chart_files[key].append({
                            'symbol': symbol,
                            'name': stock.get('name', self.get_stock_name(symbol)),
                            'path': rel_path
                        })
                except Exception as e:
                    continue

            print(f"    已生成 {len(chart_files[key])} 张K线图")

        return chart_files

    def _build_html(self, summaries: Dict[str, dict], chart_files: Dict[str, List] = None) -> str:
        """构建HTML内容"""
        total_stocks = sum(s['count'] for s in summaries.values())

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>策略筛选结果汇总</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            color: white;
            padding: 30px 0;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 16px;
            border-bottom: 2px solid #f0f0f0;
        }}
        .card-title {{ font-size: 1.3em; color: #333; }}
        .card-count {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: bold;
        }}
        .card-desc {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 16px;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 16px;
        }}
        .metric {{
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .metric-value {{ font-size: 1.2em; font-weight: bold; color: #333; }}
        .metric-label {{ font-size: 0.8em; color: #888; }}
        .stock-list {{
            max-height: 600px;
            overflow-y: auto;
        }}
        .stock-list-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 10px;
            background: #f0f0f0;
            border-radius: 4px;
            margin-bottom: 8px;
            font-size: 0.85em;
            color: #666;
        }}
        .stock-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px;
            border-bottom: 1px solid #f0f0f0;
        }}
        .stock-item:hover {{ background: #f8f9fa; }}
        .stock-symbol {{ font-weight: bold; color: #667eea; }}
        .stock-name {{ color: #666; margin-left: 10px; }}
        .stock-price {{ font-weight: bold; }}
        .positive {{ color: #e74c3c; }}
        .negative {{ color: #27ae60; }}
        .charts-section {{
            margin-top: 30px;
        }}
        .charts-title {{
            color: white;
            font-size: 1.5em;
            margin-bottom: 20px;
            text-align: center;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }}
        .chart-card {{
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .chart-card img {{
            width: 100%;
            height: auto;
        }}
        .footer {{
            text-align: center;
            color: white;
            padding: 30px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 策略筛选结果汇总</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 共 {len(summaries)} 个策略 | 合计 {total_stocks} 只股票</p>
        </div>

        <div class="summary-cards">
"""

        # 添加每个策略的卡片
        for key, summary in summaries.items():
            config = summary['config']
            html += f"""
            <div class="card">
                <div class="card-header">
                    <span class="card-title">{config.display_name}</span>
                    <span class="card-count">{summary['count']} 只</span>
                </div>
                <p class="card-desc">{config.description}</p>
                <div class="metrics">
"""

            # 添加关键指标
            for metric, values in summary.get('metrics_stats', {}).items():
                html += f"""
                    <div class="metric">
                        <div class="metric-value">{values['mean']}</div>
                        <div class="metric-label">{metric}</div>
                    </div>
"""

            html += """
                </div>
                <div class="stock-list-header">
                    <span>📈 全部筛选结果</span>
                    <span>共 {count} 只股票</span>
                </div>
                <div class="stock-list">
""".format(count=summary['count'])

            # 添加股票列表 - 显示全部股票
            for stock in summary['all_stocks']:
                symbol = stock.get('symbol', '')
                name = stock.get('name', self.get_stock_name(symbol))
                price = stock.get('price', stock.get('close', 0))
                change = stock.get('change_pct', stock.get('rps_sum', 0))

                change_class = 'positive' if change > 0 else 'negative'
                change_str = f"+{change:.1f}%" if change > 0 else f"{change:.1f}%"

                html += f"""
                    <div class="stock-item">
                        <span>
                            <span class="stock-symbol">{symbol}</span>
                            <span class="stock-name">{name}</span>
                        </span>
                        <span class="stock-price">¥{price:.2f} <span class="{change_class}">{change_str}</span></span>
                    </div>
"""

            html += """
                </div>
            </div>
"""

        html += """
        </div>

        <!-- K线图展示区域 -->
"""

        # 添加K线图展示
        if chart_files:
            html += """
        <div class="charts-section">
            <h2 class="charts-title">📊 K线图展示</h2>
"""
            for key, charts in chart_files.items():
                if not charts:
                    continue
                config = summaries[key]['config']
                html += f"""
            <div class="strategy-charts">
                <h3 style="color: white; margin: 20px 0 10px 0;">{config.display_name} ({len(charts)}张)</h3>
                <div class="charts-grid">
"""
                for chart in charts[:20]:  # 每个策略最多显示20张
                    html += f"""
                    <div class="chart-card">
                        <img src="{chart['path']}" alt="{chart['symbol']} {chart['name']}">
                    </div>
"""

                if len(charts) > 20:
                    html += f"""
                <p style="color: white; text-align: center; padding: 10px;">... 还有 {len(charts) - 20} 张K线图未显示</p>
"""

                html += """
                </div>
            </div>
"""

            html += """
        </div>
"""

        html += """
        <div class="footer">
            <p>Stock Screener - 量化选股策略工具</p>
        </div>
    </div>
</body>
</html>
"""

        return html


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(description='策略筛选结果汇总分析')
    parser.add_argument('--strategy', '-s', help='指定策略 (pocket_pivot, train_advanced, arc_bottom, first_limit_up, blue_diamond)')
    parser.add_argument('--generate-charts', '-c', action='store_true', help='生成K线图')
    parser.add_argument('--html', action='store_true', help='生成HTML报告')
    parser.add_argument('--all', '-a', action='store_true', help='显示所有策略详情')

    args = parser.parse_args()

    summary = StrategySummary()

    if args.generate_charts:
        count = summary.generate_kline_charts(args.strategy)
        print(f"\n✅ 共生成 {count} 张K线图")

    if args.html:
        summary.generate_html_report(args.strategy)

    if not args.generate_charts and not args.html:
        # 默认打印汇总
        summary.print_summary(args.strategy if not args.all else None)

        # 询问是否生成HTML
        print("\n💡 提示:")
        print("   生成K线图: python3 ~/strategy_summary.py --generate-charts")
        print("   生成HTML报告: python3 ~/strategy_summary.py --html")
        print("   全部执行: python3 ~/strategy_summary.py -c --html")


if __name__ == "__main__":
    main()
