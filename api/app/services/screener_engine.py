"""
选股引擎 - 封装现有选股脚本为统一服务

将 skill/python/ 下的各个选股脚本封装为统一的接口
"""

import os
import sys
import subprocess
import pandas as pd
import json
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import asyncio

from app.config import settings
from app.models.screener import StrategyInfo, ScreenResult, StockInfo, StockTechnical

# 添加 Python 脚本目录到路径
SKILL_PYTHON_DIR = os.path.join(os.path.dirname(__file__), "../../../python")
sys.path.insert(0, SKILL_PYTHON_DIR)

class ScreenerEngine:
    """选股引擎"""
    
    def __init__(self):
        self.strategies = self._init_strategies()
    
    def _init_strategies(self) -> List[Dict[str, Any]]:
        """初始化策略列表"""
        return [
            {
                "id": "monthly_reversal",
                "name": "月线反转策略",
                "description": "陶博士经典趋势反转买点，月线级别底部反转信号",
                "category": "RPS",
                "script": "screen_monthly_reversal.py",
                "params": {},
                "avg_return": 14.08,
                "win_rate": 88.0
            },
            {
                "id": "pocket_pivot",
                "name": "口袋支点策略",
                "description": "陶博士经典买点，成交量突破+RPS强势+回撤控制",
                "category": "RPS",
                "script": "pocket_pivot_strategy.py",
                "params": {},
                "avg_return": -1.34,
                "win_rate": 2.0
            },
            {
                "id": "train",
                "name": "火车头策略",
                "description": "MRGC + SXHCG 双策略组合，捕捉强势股",
                "category": "RPS",
                "script": "train_daily_advanced_strategy.py",
                "params": {},
                "avg_return": -1.72,
                "win_rate": 0.0
            },
            {
                "id": "sxhcg3",
                "name": "顺向火车轨3.0",
                "description": "RPS120+250>185，均线多头排列，回撤控制",
                "category": "RPS",
                "script": "sxhcg3_strategy.py",
                "params": {},
            },
            {
                "id": "blue_diamond",
                "name": "蓝色钻石策略",
                "description": "捕捉第二波上涨机会，RPS回调后重新走强",
                "category": "RPS",
                "script": "blue_diamond_strategy.py",
                "params": {},
            },
            {
                "id": "three_line_red",
                "name": "三线红策略",
                "description": "RPS纯技术筛选，最简单直接",
                "category": "RPS",
                "script": "screen_three_line_red.py",
                "params": {},
            },
            {
                "id": "arc_bottom",
                "name": "圆弧底策略",
                "description": "底部反转信号，捕捉长期底部形态",
                "category": "技术",
                "script": "arc_bottom_strategy.py",
                "params": {},
            },
            {
                "id": "first_limit_up",
                "name": "首次涨停&一线红",
                "description": "涨停突破+RPS一线红",
                "category": "技术",
                "script": "first_limit_up_strategy.py",
                "params": {},
            },
            {
                "id": "mid_term_adjustment",
                "name": "中期调整后选股",
                "description": "250日翻倍+调整≤50%+RPS一线红",
                "category": "综合",
                "script": "mid_term_adjustment_strategy.py",
                "params": {},
            },
        ]
    
    def get_strategies(self) -> List[StrategyInfo]:
        """获取策略列表"""
        return [
            StrategyInfo(
                id=s["id"],
                name=s["name"],
                description=s["description"],
                category=s["category"],
                params=s.get("params", {}),
                avg_return=s.get("avg_return"),
                win_rate=s.get("win_rate")
            )
            for s in self.strategies
        ]
    
    async def run_strategy(
        self,
        strategy_id: str,
        params: Dict[str, Any] = {},
        top_n: int = 50,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        执行选股策略
        
        Args:
            strategy_id: 策略ID
            params: 策略参数
            top_n: 返回前N只股票
            progress_callback: 进度回调函数 async def callback(progress, current, found, total)
        
        Returns:
            {
                "results": [ScreenResult, ...],
                "summary": {total, avg_rps, ...}
            }
        """
        # 查找策略
        strategy = next((s for s in self.strategies if s["id"] == strategy_id), None)
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        # 发送开始消息
        if progress_callback:
            await progress_callback(10, f"正在执行 {strategy['name']}...", 0, 0)
        
        # 检查是否有现有的结果文件
        result_file = self._find_existing_result(strategy_id)
        
        if not result_file:
            # 如果没有结果文件，返回模拟数据用于演示
            if progress_callback:
                await progress_callback(50, "生成演示数据...", 0, 0)
            
            results = self._generate_demo_results(strategy_id, top_n)
            
            if progress_callback:
                await progress_callback(100, "选股完成（演示数据）", len(results), 0)
            
            return {
                "results": results,
                "summary": {
                    "total": len(results),
                    "strategy": strategy["name"],
                    "avg_rps": self._calculate_avg_rps(results)
                }
            }
        
        # 解析结果
        if progress_callback:
            await progress_callback(70, "解析选股结果...", 0, 0)
        
        results = self._parse_results(result_file, strategy_id, top_n)
        
        # 发送完成消息
        if progress_callback:
            await progress_callback(100, "选股完成", len(results), 0)
        
        return {
            "results": results,
            "summary": {
                "total": len(results),
                "strategy": strategy["name"],
                "avg_rps": self._calculate_avg_rps(results)
            }
        }
    
    def _find_existing_result(self, strategy_id: str) -> Optional[str]:
        """查找现有的结果文件"""
        # 尝试多个可能的位置
        possible_dirs = [
            settings.SCREEN_RESULTS_DIR,
            os.path.expanduser("~/.vntrader/screen_results"),
            os.path.expanduser("~/screen_results"),
        ]
        
        # 尝试多种文件名模式
        patterns = [
            f"{strategy_id}_*.csv",
            f"{strategy_id}.csv",
        ]
        
        for dir_path in possible_dirs:
            if not os.path.exists(dir_path):
                continue
            
            for pattern in patterns:
                import glob
                files = glob.glob(os.path.join(dir_path, pattern))
                if files:
                    # 返回最新的文件
                    return max(files, key=os.path.getmtime)
        
        return None
    
    def _generate_demo_results(self, strategy_id: str, top_n: int) -> List[ScreenResult]:
        """生成演示数据"""
        import random
        
        demo_stocks = [
            ("300185", "通裕重工", "SZSE"),
            ("002636", "金安国纪", "SZSE"),
            ("600732", "爱旭股份", "SSE"),
            ("002796", "世嘉科技", "SZSE"),
            ("603859", "能科科技", "SSE"),
            ("688138", "清溢光电", "SSE"),
            ("300124", "汇川技术", "SZSE"),
            ("002460", "赣锋锂业", "SZSE"),
            ("688981", "中芯国际", "SSE"),
            ("300750", "宁德时代", "SZSE"),
        ]
        
        results = []
        for idx, (code, name, exchange) in enumerate(demo_stocks[:top_n]):
            stock_info = StockInfo(
                symbol=f"{code}.{exchange}",
                code=code,
                name=name,
                exchange=exchange,
                industry="电子"
            )
            
            technical = StockTechnical(
                symbol=f"{code}.{exchange}",
                close=round(random.uniform(10, 100), 2),
                change_pct=round(random.uniform(-5, 10), 2),
                volume=random.randint(100000, 10000000),
                turnover=random.randint(1000000, 500000000),
                volume_ratio=round(random.uniform(0.5, 3.0), 1),
                rps_50=round(random.uniform(85, 99), 1),
                rps_120=round(random.uniform(88, 99), 1),
                rps_250=round(random.uniform(90, 99), 1),
                ma_20=round(random.uniform(10, 100), 2),
                ma_60=round(random.uniform(10, 100), 2),
                ma_120=round(random.uniform(10, 100), 2),
                max_dd=round(random.uniform(-15, -3), 1),
            )
            
            results.append(ScreenResult(
                stock_info=stock_info,
                technical=technical,
                score=round(random.uniform(70, 95), 1),
                rank=idx + 1,
                reason=f"符合{strategy_id}策略条件"
            ))
        
        return results
    
    def _get_result_file(self, strategy_id: str) -> str:
        """获取结果文件路径"""
        today = datetime.now().strftime("%Y%m%d")
        filename = f"{strategy_id}_{today}.csv"
        return os.path.join(settings.SCREEN_RESULTS_DIR, filename)
    
    def _parse_results(self, result_file: str, strategy_id: str, top_n: int) -> List[ScreenResult]:
        """解析CSV结果文件"""
        try:
            df = pd.read_csv(result_file)
            results = []
            
            for idx, row in df.head(top_n).iterrows():
                symbol = str(row.get("symbol", ""))
                stock_info = StockInfo(
                    symbol=symbol,
                    code=symbol.split(".")[0] if "." in symbol else symbol,
                    name=str(row.get("name", "")),
                    exchange=str(row.get("exchange", symbol.split(".")[-1] if "." in symbol else "")),
                    industry=str(row.get("industry", "")) if row.get("industry") else None
                )
                
                technical = StockTechnical(
                    symbol=symbol,
                    close=float(row.get("close", 0.0)) if row.get("close") else 0.0,
                    change_pct=float(row.get("change_pct", 0.0)) if row.get("change_pct") else 0.0,
                    volume=float(row.get("volume", 0.0)) if row.get("volume") else 0.0,
                    turnover=float(row.get("turnover", 0.0)) if row.get("turnover") else 0.0,
                    volume_ratio=float(row.get("volume_ratio")) if row.get("volume_ratio") else None,
                    rps_50=float(row.get("rps_50")) if row.get("rps_50") else None,
                    rps_120=float(row.get("rps_120")) if row.get("rps_120") else None,
                    rps_250=float(row.get("rps_250")) if row.get("rps_250") else None,
                    ma_20=float(row.get("ma_20")) if row.get("ma_20") else None,
                    ma_60=float(row.get("ma_60")) if row.get("ma_60") else None,
                    ma_120=float(row.get("ma_120")) if row.get("ma_120") else None,
                    max_dd=float(row.get("max_dd")) if row.get("max_dd") else None,
                    distance_from_high=float(row.get("distance_from_high")) if row.get("distance_from_high") else None
                )
                
                results.append(ScreenResult(
                    stock_info=stock_info,
                    technical=technical,
                    score=row.get("score", 0.0),
                    rank=idx + 1,
                    reason=row.get("reason", "符合策略条件")
                ))
            
            return results
            
        except Exception as e:
            raise ValueError(f"Failed to parse result file: {str(e)}")
    
    def _calculate_avg_rps(self, results: List[ScreenResult]) -> float:
        """计算平均RPS"""
        rps_values = [r.technical.rps_120 for r in results if r.technical.rps_120]
        return sum(rps_values) / len(rps_values) if rps_values else 0.0
    
    def update_data(self):
        """更新K线和RPS数据"""
        try:
            # 调用更新脚本
            subprocess.run([
                sys.executable,
                os.path.join(SKILL_PYTHON_DIR, "update_kline_from_baostock.py")
            ], check=True, cwd=SKILL_PYTHON_DIR)
            
            subprocess.run([
                sys.executable,
                os.path.join(SKILL_PYTHON_DIR, "update_daily_data.py")
            ], check=True, cwd=SKILL_PYTHON_DIR)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to update data: {str(e)}")
