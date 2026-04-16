"""
股票池管理器
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import pandas as pd

from app.config import settings
from app.models.portfolio import (
    PortfolioStockInput,
    PortfolioDetail,
    PortfolioStock,
    PortfolioSummary
)

class PortfolioManager:
    """股票池管理器"""
    
    def __init__(self):
        self.pool_dir = settings.STOCK_POOL_DIR
    
    async def create_portfolio(
        self,
        portfolio_id: str,
        name: str,
        stocks: List[PortfolioStockInput],
        strategy_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> PortfolioDetail:
        """创建股票池"""
        # 保存到文件
        pool_file = os.path.join(self.pool_dir, f"{portfolio_id}.json")
        
        pool_data = {
            "id": portfolio_id,
            "name": name,
            "strategy_id": strategy_id,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "stocks": [s.dict() for s in stocks]
        }
        
        with open(pool_file, "w", encoding="utf-8") as f:
            json.dump(pool_data, f, ensure_ascii=False, indent=2)
        
        # 返回详情
        return await self.get_portfolio(portfolio_id)
    
    async def get_portfolio(self, portfolio_id: str) -> Optional[PortfolioDetail]:
        """获取股票池详情"""
        pool_file = os.path.join(self.pool_dir, f"{portfolio_id}.json")
        
        if not os.path.exists(pool_file):
            return None
        
        with open(pool_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 获取最新价格（模拟）
        stocks = []
        for s in data["stocks"]:
            buy_price = s["buy_price"]
            current_price = buy_price * 1.05  # 模拟涨5%
            
            stocks.append(PortfolioStock(
                symbol=s["symbol"],
                name=s.get("name", s["symbol"]),
                buy_price=buy_price,
                buy_date=s["buy_date"],
                current_price=current_price,
                quantity=s.get("quantity", 100),
                market_value=current_price * s.get("quantity", 100) * 100,
                pnl=(current_price - buy_price) * s.get("quantity", 100) * 100,
                pnl_pct=(current_price - buy_price) / buy_price * 100,
                hold_days=(datetime.now().date() - date.fromisoformat(s["buy_date"])).days
            ))
        
        total_cost = sum(s.buy_price * s.quantity * 100 for s in stocks)
        total_value = sum(s.market_value for s in stocks)
        
        return PortfolioDetail(
            id=data["id"],
            name=data["name"],
            strategy_id=data.get("strategy_id"),
            description=data.get("description"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.now(),
            total_stocks=len(stocks),
            total_cost=total_cost,
            total_value=total_value,
            total_pnl=total_value - total_cost,
            total_return=(total_value - total_cost) / total_cost * 100,
            win_count=sum(1 for s in stocks if s.pnl > 0),
            lose_count=sum(1 for s in stocks if s.pnl <= 0),
            win_rate=sum(1 for s in stocks if s.pnl > 0) / len(stocks) * 100 if stocks else 0,
            stocks=stocks
        )
    
    async def update_prices(self, portfolio_id: str, force: bool = False) -> bool:
        """更新持仓价格"""
        # TODO: 调用 akshare 更新价格
        return True
    
    async def delete_portfolio(self, portfolio_id: str) -> bool:
        """删除股票池"""
        pool_file = os.path.join(self.pool_dir, f"{portfolio_id}.json")
        
        if os.path.exists(pool_file):
            os.remove(pool_file)
            return True
        return False
    
    async def get_all_portfolios(self) -> List[PortfolioSummary]:
        """获取所有股票池汇总"""
        portfolios = []
        
        for filename in os.listdir(self.pool_dir):
            if filename.endswith(".json"):
                portfolio_id = filename.replace(".json", "")
                detail = await self.get_portfolio(portfolio_id)
                
                if detail:
                    portfolios.append(PortfolioSummary(
                        id=detail.id,
                        name=detail.name,
                        strategy_id=detail.strategy_id,
                        total_stocks=detail.total_stocks,
                        total_return=detail.total_return,
                        win_rate=detail.win_rate,
                        created_at=detail.created_at,
                        last_updated=detail.updated_at
                    ))
        
        return portfolios
