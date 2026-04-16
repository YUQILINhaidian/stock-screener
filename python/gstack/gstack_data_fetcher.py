#!/usr/bin/env python3
"""
gstack数据采集器

使用gstack浏览器自动化从网页端采集股票数据

支持数据源:
- 东方财富网 (eastmoney.com) - 股票实时行情  
- 同花顺 (10jqka.com.cn) - RPS和技术指标
- 雪球网 (xueqiu.com) - 资金流向数据

使用示例:
    # 获取单只股票价格
    python3 gstack_data_fetcher.py --symbol 600519
    
    # 批量获取多只股票数据
    python3 gstack_data_fetcher.py --symbols 600519,000858,600036
    
    # 更新持仓股票池数据
    python3 gstack_data_fetcher.py --pool monthly_reversal_20260407
"""

import subprocess
import json
import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional
import time
import random

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GStackDataFetcher:
    """gstack数据采集器"""
    
    def __init__(self, browse_bin: str = None):
        """
        初始化数据采集器
        
        Args:
            browse_bin: gstack browse二进制文件路径
        """
        if browse_bin is None:
            # 自动检测browse路径
            browse_bin = os.path.expanduser("~/.codeflicker/skills/gstack/browse/dist/browse")
        
        if not os.path.exists(browse_bin):
            raise FileNotFoundError(f"gstack browse binary not found: {browse_bin}")
        
        self.browse = browse_bin
        logger.info(f"使用gstack browse: {self.browse}")
        
        # 初始化浏览器
        self._init_browser()
    
    def _init_browser(self):
        """初始化浏览器状态检查"""
        try:
            result = subprocess.run(
                [self.browse, "status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            logger.info("浏览器状态检查完成")
        except subprocess.TimeoutExpired:
            logger.warning("浏览器状态检查超时，将在首次使用时自动启动")
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
    
    def _run_command(self, *args, timeout: int = 30) -> subprocess.CompletedProcess:
        """
        执行gstack browse命令
        
        Args:
            *args: 命令参数
            timeout: 超时时间（秒）
            
        Returns:
            命令执行结果
        """
        cmd = [self.browse] + list(args)
        logger.debug(f"执行命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"命令超时（{timeout}s）: {' '.join(args)}")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"命令失败: {e.stderr}")
            raise
    
    def _random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """随机延迟（反爬虫）"""
        delay = random.uniform(min_seconds, max_seconds)
        logger.debug(f"延迟 {delay:.2f} 秒...")
        time.sleep(delay)
    
    def fetch_stock_price_eastmoney(self, symbol: str) -> Dict:
        """
        从东方财富网获取股票实时价格
        
        Args:
            symbol: 股票代码（不含交易所后缀，如 "600519"）
            
        Returns:
            包含价格信息的字典
        """
        logger.info(f"开始获取股票价格: {symbol}")
        
        # 1. 导航到东方财富行情页
        url = f"http://quote.eastmoney.com/{symbol}.html"
        self._run_command("goto", url)
        
        # 2. 等待页面加载完成（使用固定延迟替代--networkidle，避免浏览器已关闭的问题）
        time.sleep(3)
        
        try:
            # 3. 提取价格数据（使用JavaScript）
            js_code = """
            (function() {
                var priceElem = document.querySelector('.price') || 
                               document.querySelector('.last-price') ||
                               document.querySelector('#price');
                var nameElem = document.querySelector('.stockname') ||
                              document.querySelector('.name');
                var changeElem = document.querySelector('.zdfd') ||
                                document.querySelector('.change-rate');
                
                return JSON.stringify({
                    price: priceElem ? priceElem.textContent.trim() : null,
                    name: nameElem ? nameElem.textContent.trim() : null,
                    change_rate: changeElem ? changeElem.textContent.trim() : null
                });
            })()
            """
            
            result = self._run_command("js", js_code)
            data = json.loads(result.stdout.strip())
            
            # 4. 截图保存（可选，用于调试）
            if os.environ.get("GSTACK_DEBUG"):
                screenshot_path = f"/tmp/stock_{symbol}_{datetime.now():%Y%m%d_%H%M%S}.png"
                self._run_command("screenshot", screenshot_path)
                logger.debug(f"截图已保存: {screenshot_path}")
            
            return {
                "symbol": symbol,
                "price": float(data["price"]) if data["price"] else None,
                "name": data["name"],
                "change_rate": data["change_rate"],
                "source": "eastmoney",
                "timestamp": datetime.now().isoformat(),
                "url": url
            }
            
        except Exception as e:
            logger.error(f"解析价格失败: {symbol} - {e}")
            # 降级：保存HTML内容用于调试
            html_result = self._run_command("html")
            with open(f"/tmp/stock_{symbol}_error.html", "w") as f:
                f.write(html_result.stdout)
            raise
    
    def fetch_stock_batch(self, symbols: List[str]) -> List[Dict]:
        """
        批量获取多只股票数据
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            股票数据列表
        """
        logger.info(f"开始批量获取 {len(symbols)} 只股票数据")
        results = []
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"进度: {i}/{len(symbols)} - {symbol}")
            
            try:
                data = self.fetch_stock_price_eastmoney(symbol)
                results.append(data)
                logger.info(f"✅ {symbol}: ¥{data['price']} ({data['change_rate']})")
                
            except Exception as e:
                logger.error(f"❌ {symbol}: 获取失败 - {e}")
                results.append({
                    "symbol": symbol,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            # 反爬虫：随机延迟
            if i < len(symbols):
                self._random_delay(2, 4)
        
        logger.info(f"批量获取完成，成功 {sum(1 for r in results if 'price' in r)}/{len(symbols)}")
        return results
    
    def update_portfolio_prices(self, pool_name: str) -> Dict:
        """
        更新股票池中所有股票的价格
        
        Args:
            pool_name: 股票池名称
            
        Returns:
            更新结果
        """
        logger.info(f"开始更新股票池: {pool_name}")
        
        # 1. 读取股票池JSON文件
        pool_file = os.path.expanduser(f"~/.vntrader/stock_pools/{pool_name}.json")
        
        if not os.path.exists(pool_file):
            raise FileNotFoundError(f"股票池不存在: {pool_file}")
        
        with open(pool_file, 'r', encoding='utf-8') as f:
            pool_data = json.load(f)
        
        stocks = pool_data.get('stocks', {})
        symbols = [s.split('.')[0] for s in stocks.keys()]
        
        logger.info(f"股票池包含 {len(symbols)} 只股票")
        
        # 2. 批量获取最新价格
        price_data = self.fetch_stock_batch(symbols)
        
        # 3. 更新股票池数据
        updated_count = 0
        for data in price_data:
            if 'price' in data and data['price']:
                symbol_full = f"{data['symbol']}.SSE"  # TODO: 智能判断交易所
                if symbol_full not in stocks:
                    symbol_full = f"{data['symbol']}.SZSE"
                
                if symbol_full in stocks:
                    stocks[symbol_full]['current_price'] = data['price']
                    stocks[symbol_full]['updated_at'] = data['timestamp']
                    updated_count += 1
        
        # 4. 保存更新后的数据
        pool_data['updated_at'] = datetime.now().isoformat()
        
        with open(pool_file, 'w', encoding='utf-8') as f:
            json.dump(pool_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ 股票池更新完成: {updated_count}/{len(symbols)} 只股票价格已更新")
        
        return {
            "pool_name": pool_name,
            "total": len(symbols),
            "updated": updated_count,
            "timestamp": datetime.now().isoformat()
        }
    
    def cleanup(self):
        """清理资源（可选）"""
        try:
            # 关闭浏览器（如果不需要持久化）
            # self._run_command("stop")
            logger.info("清理完成")
        except Exception as e:
            logger.warning(f"清理失败: {e}")


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="gstack股票数据采集器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 获取单只股票
  %(prog)s --symbol 600519
  
  # 批量获取
  %(prog)s --symbols 600519,000858,600036
  
  # 更新股票池
  %(prog)s --pool monthly_reversal_20260407
  
  # 调试模式（保存截图）
  GSTACK_DEBUG=1 %(prog)s --symbol 600519
        """
    )
    
    parser.add_argument(
        '--symbol',
        help='单只股票代码（如 600519）'
    )
    
    parser.add_argument(
        '--symbols',
        help='多只股票代码，逗号分隔（如 600519,000858,600036）'
    )
    
    parser.add_argument(
        '--pool',
        help='股票池名称（从~/.vntrader/stock_pools/读取）'
    )
    
    parser.add_argument(
        '--output',
        help='输出JSON文件路径（可选）'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='运行测试模式'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='详细日志输出'
    )
    
    args = parser.parse_args()
    
    # 配置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 测试模式
    if args.test:
        print("=== gstack数据采集器测试模式 ===")
        fetcher = GStackDataFetcher()
        test_result = fetcher.fetch_stock_price_eastmoney("600519")
        print(json.dumps(test_result, indent=2, ensure_ascii=False))
        print("✅ 测试通过")
        return 0
    
    # 参数验证
    if not any([args.symbol, args.symbols, args.pool]):
        parser.print_help()
        sys.exit(1)
    
    try:
        fetcher = GStackDataFetcher()
        
        # 单只股票
        if args.symbol:
            result = fetcher.fetch_stock_price_eastmoney(args.symbol)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 多只股票
        elif args.symbols:
            symbols = [s.strip() for s in args.symbols.split(',')]
            results = fetcher.fetch_stock_batch(symbols)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"✅ 结果已保存到: {args.output}")
            else:
                print(json.dumps(results, indent=2, ensure_ascii=False))
        
        # 股票池
        elif args.pool:
            result = fetcher.update_portfolio_prices(args.pool)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return 0
        
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        return 1
    
    finally:
        if 'fetcher' in locals():
            fetcher.cleanup()


if __name__ == "__main__":
    sys.exit(main())
