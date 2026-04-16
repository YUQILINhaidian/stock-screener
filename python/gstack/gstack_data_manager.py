#!/usr/bin/env python3
"""
本地股票数据管理器

使用本机VNPy数据中心的数据，结合gstack进行可视化展示

数据源:
- VNPy SQLite数据库 (~/.vntrader/database.db)
- 股票池JSON文件 (~/.vntrader/stock_pools/)
- 筛选结果CSV (~/.vntrader/screen_results/)

功能:
- 查询股票实时价格（从数据库）
- 更新股票池数据（使用现有stock_pool_tracker.py）
- 生成HTML可视化看板（用gstack截图导出）

使用示例:
    # 生成持仓看板并截图
    python3 gstack_data_manager.py --pool monthly_reversal_pool --screenshot
    
    # 导出PDF报告
    python3 gstack_data_manager.py --pool monthly_reversal_pool --pdf
"""

import sqlite3
import json
import os
import sys
import argparse
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GStackDataManager:
    """本地股票数据管理器"""
    
    def __init__(self, 
                 db_path: str = None,
                 browse_bin: str = None):
        """
        初始化数据管理器
        
        Args:
            db_path: VNPy数据库路径
            browse_bin: gstack browse二进制路径
        """
        if db_path is None:
            db_path = os.path.expanduser("~/.vntrader/database.db")
        
        if browse_bin is None:
            browse_bin = os.path.expanduser("~/.codeflicker/skills/gstack/browse/dist/browse")
        
        self.db_path = db_path
        self.browse = browse_bin
        
        # 验证数据库存在
        if not os.path.exists(self.db_path):
            logger.warning(f"VNPy数据库不存在: {self.db_path}")
        
        logger.info(f"数据库: {self.db_path}")
        logger.info(f"gstack browse: {self.browse}")
    
    def get_stock_price(self, symbol: str, exchange: str = None) -> Optional[Dict]:
        """
        从本地数据库查询最新价格
        
        Args:
            symbol: 股票代码（如 "600519"）
            exchange: 交易所（SSE/SZSE），自动推断
            
        Returns:
            包含价格信息的字典
        """
        if exchange is None:
            # 自动推断交易所
            if symbol.startswith('6'):
                exchange = 'SSE'
            elif symbol.startswith(('0', '3')):
                exchange = 'SZSE'
            else:
                exchange = 'SSE'  # 默认上交所
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查询最新K线数据
            cursor.execute("""
                SELECT close_price, high_price, low_price, open_price, 
                       volume, datetime
                FROM dbbardata
                WHERE symbol = ? AND exchange = ?
                ORDER BY datetime DESC
                LIMIT 1
            """, (symbol, exchange))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "symbol": symbol,
                    "exchange": exchange,
                    "price": result[0],
                    "high": result[1],
                    "low": result[2],
                    "open": result[3],
                    "volume": result[4],
                    "datetime": result[5],
                    "source": "local_vnpy_db"
                }
            else:
                logger.warning(f"未找到股票数据: {symbol}.{exchange}")
                return None
                
        except Exception as e:
            logger.error(f"查询失败: {symbol} - {e}")
            return None
    
    def load_stock_pool(self, pool_name: str) -> Dict:
        """
        加载股票池数据
        
        Args:
            pool_name: 股票池名称
            
        Returns:
            股票池数据字典
        """
        pool_file = os.path.expanduser(f"~/.vntrader/stock_pools/{pool_name}.json")
        
        if not os.path.exists(pool_file):
            raise FileNotFoundError(f"股票池不存在: {pool_file}")
        
        with open(pool_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"加载股票池: {pool_name}, {len(data.get('stocks', {}))} 只股票")
        return data
    
    def generate_portfolio_html(self, pool_name: str, output_path: str = None) -> str:
        """
        生成持仓看板HTML（供gstack截图使用）
        
        Args:
            pool_name: 股票池名称
            output_path: 输出HTML路径（默认 /tmp/{pool_name}_dashboard.html）
            
        Returns:
            HTML文件路径
        """
        logger.info(f"生成持仓看板: {pool_name}")
        
        # 加载股票池数据
        data = self.load_stock_pool(pool_name)
        
        stocks = data.get('stocks', {})
        created_at = data.get('created_at', 'N/A')
        updated_at = data.get('updated_at', 'N/A')
        
        # 计算统计数据
        total_stocks = len(stocks)
        total_return = 0
        winning_stocks = 0
        
        stocks_list = []
        for symbol_full, stock_data in stocks.items():
            entry_price = stock_data.get('entry_price', 0)
            current_price = stock_data.get('current_price', entry_price)
            return_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            
            total_return += return_pct
            if return_pct > 0:
                winning_stocks += 1
            
            # 提取股票代码和名称
            symbol = symbol_full.split('.')[0]
            name = stock_data.get('name', symbol)
            
            stocks_list.append({
                'symbol': symbol,
                'name': name,
                'entry_price': entry_price,
                'current_price': current_price,
                'return_pct': return_pct,
                'entry_date': stock_data.get('entry_date', 'N/A')
            })
        
        # 按收益率倒序排序
        stocks_list.sort(key=lambda x: x['return_pct'], reverse=True)
        
        avg_return = total_return / total_stocks if total_stocks > 0 else 0
        win_rate = winning_stocks / total_stocks * 100 if total_stocks > 0 else 0
        
        # 生成HTML
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{pool_name} - 持仓看板</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; }}
        .return-positive {{ color: #ef4444; }}
        .return-negative {{ color: #10b981; }}
    </style>
</head>
<body class="bg-gray-50 p-8">
    <div class="max-w-7xl mx-auto">
        <!-- 标题 -->
        <header class="mb-8">
            <h1 class="text-4xl font-bold text-gray-800 mb-2">📊 {pool_name}</h1>
            <p class="text-gray-600">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        
        <!-- 概览卡片 -->
        <div class="grid grid-cols-4 gap-6 mb-8">
            <div class="bg-white rounded-lg shadow p-6">
                <div class="text-gray-500 text-sm mb-2">总股票数</div>
                <div class="text-3xl font-bold text-blue-600">{total_stocks}</div>
            </div>
            <div class="bg-white rounded-lg shadow p-6">
                <div class="text-gray-500 text-sm mb-2">平均收益率</div>
                <div class="text-3xl font-bold {'text-red-600' if avg_return > 0 else 'text-green-600'}">
                    {avg_return:+.2f}%
                </div>
            </div>
            <div class="bg-white rounded-lg shadow p-6">
                <div class="text-gray-500 text-sm mb-2">胜率</div>
                <div class="text-3xl font-bold text-purple-600">{win_rate:.1f}%</div>
            </div>
            <div class="bg-white rounded-lg shadow p-6">
                <div class="text-gray-500 text-sm mb-2">盈利股票数</div>
                <div class="text-3xl font-bold text-orange-600">{winning_stocks}/{total_stocks}</div>
            </div>
        </div>
        
        <!-- 建仓信息 -->
        <div class="bg-blue-50 border-l-4 border-blue-500 p-4 mb-8">
            <div class="flex">
                <div class="flex-1">
                    <p class="text-sm text-blue-800">
                        <strong>建仓时间:</strong> {created_at[:10] if created_at != 'N/A' else 'N/A'}
                    </p>
                </div>
                <div class="flex-1">
                    <p class="text-sm text-blue-800">
                        <strong>最后更新:</strong> {updated_at[:10] if updated_at != 'N/A' else 'N/A'}
                    </p>
                </div>
            </div>
        </div>
        
        <!-- 持仓明细表格 -->
        <div class="bg-white rounded-lg shadow overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-800 text-white">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">
                            排名
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">
                            股票代码
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">
                            股票名称
                        </th>
                        <th class="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider">
                            建仓价格
                        </th>
                        <th class="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider">
                            当前价格
                        </th>
                        <th class="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider">
                            收益率
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">
                            建仓日期
                        </th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
"""
        
        # 生成表格行
        for i, stock in enumerate(stocks_list, 1):
            return_class = 'return-positive' if stock['return_pct'] > 0 else 'return-negative'
            row_bg = 'bg-gray-50' if i % 2 == 0 else 'bg-white'
            
            html += f"""
                    <tr class="{row_bg}">
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {i}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                            {stock['symbol']}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {stock['name']}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-700">
                            ¥{stock['entry_price']:.2f}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 font-semibold">
                            ¥{stock['current_price']:.2f}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-bold {return_class}">
                            {stock['return_pct']:+.2f}%
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {stock['entry_date']}
                        </td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
        
        <!-- 页脚 -->
        <footer class="mt-8 text-center text-gray-500 text-sm">
            <p>报告由 stock-screener + gstack 自动生成</p>
        </footer>
    </div>
</body>
</html>
"""
        
        # 保存HTML文件
        if output_path is None:
            output_path = f"/tmp/{pool_name}_dashboard.html"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"✅ HTML看板已生成: {output_path}")
        return output_path
    
    def screenshot_html(self, html_path: str, output_path: str = None, 
                       viewport: str = "1920x1080") -> str:
        """
        使用gstack截图HTML文件
        
        Args:
            html_path: HTML文件路径
            output_path: 截图输出路径
            viewport: 视口大小
            
        Returns:
            截图文件路径
        """
        if output_path is None:
            output_path = html_path.replace('.html', '.png')
        
        logger.info(f"正在截图: {html_path}")
        
        import threading
        import http.server
        import socketserver
        import time
        
        # 启动临时HTTP服务器
        PORT = 8765
        html_dir = os.path.dirname(html_path)
        html_filename = os.path.basename(html_path)
        
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=html_dir, **kwargs)
            
            def log_message(self, format, *args):
                pass  # 静默日志
        
        httpd = socketserver.TCPServer(("", PORT), Handler)
        
        # 在后台线程启动服务器
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        logger.debug(f"临时HTTP服务器启动: http://localhost:{PORT}")
        
        try:
            # 设置视口大小
            subprocess.run([self.browse, "viewport", viewport], check=True)
            
            # 导航到HTML（通过HTTP）
            url = f"http://localhost:{PORT}/{html_filename}"
            subprocess.run([self.browse, "goto", url], check=True)
            
            # 等待页面加载
            time.sleep(3)
            
            # 截图
            subprocess.run([self.browse, "screenshot", output_path], check=True)
            
            logger.info(f"✅ 截图已保存: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"截图失败: {e}")
            raise
        finally:
            # 关闭服务器
            httpd.shutdown()
            logger.debug("临时HTTP服务器已关闭")
    
    def export_pdf(self, html_path: str, output_path: str = None) -> str:
        """
        导出PDF报告
        
        Args:
            html_path: HTML文件路径
            output_path: PDF输出路径
            
        Returns:
            PDF文件路径
        """
        if output_path is None:
            output_path = html_path.replace('.html', '.pdf')
        
        logger.info(f"正在导出PDF: {html_path}")
        
        import threading
        import http.server
        import socketserver
        import time
        
        # 启动临时HTTP服务器
        PORT = 8766
        html_dir = os.path.dirname(html_path)
        html_filename = os.path.basename(html_path)
        
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=html_dir, **kwargs)
            
            def log_message(self, format, *args):
                pass
        
        httpd = socketserver.TCPServer(("", PORT), Handler)
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        try:
            # 导航到HTML
            url = f"http://localhost:{PORT}/{html_filename}"
            subprocess.run([self.browse, "goto", url], check=True)
            
            # 等待页面加载
            time.sleep(3)
            
            # 导出PDF
            subprocess.run([self.browse, "pdf", output_path], check=True)
            
            logger.info(f"✅ PDF已保存: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"PDF导出失败: {e}")
            raise
        finally:
            httpd.shutdown()


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="本地股票数据管理器 + gstack可视化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查询单只股票价格
  %(prog)s --query 600519
  
  # 生成持仓看板HTML
  %(prog)s --pool monthly_reversal_pool
  
  # 生成看板并截图
  %(prog)s --pool monthly_reversal_pool --screenshot
  
  # 导出PDF报告
  %(prog)s --pool monthly_reversal_pool --pdf
        """
    )
    
    parser.add_argument(
        '--query',
        help='查询股票价格（股票代码）'
    )
    
    parser.add_argument(
        '--pool',
        help='股票池名称'
    )
    
    parser.add_argument(
        '--screenshot',
        action='store_true',
        help='生成PNG截图'
    )
    
    parser.add_argument(
        '--pdf',
        action='store_true',
        help='导出PDF报告'
    )
    
    parser.add_argument(
        '--output',
        help='输出路径（可选）'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='详细日志'
    )
    
    args = parser.parse_args()
    
    # 配置日志
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        manager = GStackDataManager()
        
        # 查询价格
        if args.query:
            result = manager.get_stock_price(args.query)
            if result:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(f"未找到数据: {args.query}")
                return 1
        
        # 生成持仓看板
        elif args.pool:
            html_path = manager.generate_portfolio_html(args.pool, args.output)
            print(f"✅ HTML看板: {html_path}")
            
            # 截图
            if args.screenshot:
                png_path = manager.screenshot_html(html_path)
                print(f"✅ PNG截图: {png_path}")
            
            # 导出PDF
            if args.pdf:
                pdf_path = manager.export_pdf(html_path)
                print(f"✅ PDF报告: {pdf_path}")
        
        else:
            parser.print_help()
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
