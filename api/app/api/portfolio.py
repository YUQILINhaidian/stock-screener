"""
股票池管理 API 路由
"""

from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from datetime import datetime

from app.models.portfolio import (
    CreatePortfolioRequest,
    UpdatePortfolioRequest,
    PortfolioDetail,
    PortfolioSummary
)
from app.services.portfolio_manager import PortfolioManager

router = APIRouter()

# 全局股票池管理器
portfolio_manager = PortfolioManager()

@router.post("/create", response_model=PortfolioDetail)
async def create_portfolio(request: CreatePortfolioRequest):
    """
    创建新股票池
    
    从选股结果或手动输入创建股票池
    """
    portfolio_id = str(uuid.uuid4())
    
    portfolio = await portfolio_manager.create_portfolio(
        portfolio_id=portfolio_id,
        name=request.name,
        stocks=request.stocks,
        strategy_id=request.strategy_id,
        description=request.description
    )
    
    return portfolio

@router.get("/{portfolio_id}", response_model=PortfolioDetail)
async def get_portfolio(portfolio_id: str):
    """获取股票池详情"""
    portfolio = await portfolio_manager.get_portfolio(portfolio_id)
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return portfolio

@router.post("/{portfolio_id}/update")
async def update_portfolio(portfolio_id: str, request: UpdatePortfolioRequest):
    """
    更新股票池持仓价格
    
    从 akshare 获取最新价格，重新计算盈亏
    """
    success = await portfolio_manager.update_prices(portfolio_id, force=request.force)
    
    if not success:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return {"message": "Portfolio updated successfully"}

@router.delete("/{portfolio_id}")
async def delete_portfolio(portfolio_id: str):
    """删除股票池"""
    success = await portfolio_manager.delete_portfolio(portfolio_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return {"message": "Portfolio deleted successfully"}

@router.get("/summary", response_model=List[PortfolioSummary])
async def get_portfolios_summary():
    """获取所有股票池汇总列表"""
    return await portfolio_manager.get_all_portfolios()
