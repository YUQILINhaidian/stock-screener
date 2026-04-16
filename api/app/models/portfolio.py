"""
股票池模块 - Pydantic 数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class PortfolioStockInput(BaseModel):
    """创建股票池时的股票输入"""
    symbol: str
    buy_price: float
    buy_date: str = Field(..., description="买入日期 (YYYY-MM-DD)")
    quantity: Optional[int] = Field(100, description="数量（手）")

class PortfolioStock(BaseModel):
    """股票池中的股票"""
    symbol: str
    name: str
    buy_price: float
    buy_date: date
    current_price: float
    quantity: int
    market_value: float = Field(..., description="市值")
    pnl: float = Field(..., description="盈亏金额")
    pnl_pct: float = Field(..., description="盈亏比例 (%)")
    hold_days: int = Field(..., description="持仓天数")
    stop_loss: Optional[float] = Field(None, description="止损价")
    hit_stop: bool = Field(False, description="是否触及止损")

class CreatePortfolioRequest(BaseModel):
    """创建股票池请求"""
    name: str = Field(..., description="股票池名称")
    stocks: List[PortfolioStockInput]
    strategy_id: Optional[str] = Field(None, description="关联的策略ID")
    description: Optional[str] = Field(None, description="描述")

class PortfolioDetail(BaseModel):
    """股票池详情"""
    id: str
    name: str
    strategy_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # 持仓统计
    total_stocks: int = Field(..., description="持仓数量")
    total_cost: float = Field(..., description="总成本")
    total_value: float = Field(..., description="总市值")
    total_pnl: float = Field(..., description="总盈亏")
    total_return: float = Field(..., description="总收益率 (%)")
    
    # 胜率统计
    win_count: int
    lose_count: int
    win_rate: float = Field(..., description="胜率 (%)")
    
    # 最佳/最差
    best_performer: Optional[Dict[str, Any]] = None
    worst_performer: Optional[Dict[str, Any]] = None
    
    # 持仓明细
    stocks: List[PortfolioStock]
    
    # 收益曲线
    performance_chart: List[Dict[str, Any]] = Field(default_factory=list)

class PortfolioSummary(BaseModel):
    """股票池汇总（列表）"""
    id: str
    name: str
    strategy_id: Optional[str] = None
    total_stocks: int
    total_return: float = Field(..., description="总收益率 (%)")
    win_rate: float = Field(..., description="胜率 (%)")
    created_at: datetime
    last_updated: datetime

class UpdatePortfolioRequest(BaseModel):
    """更新股票池请求（更新价格）"""
    force: bool = Field(False, description="强制更新（跳过缓存）")
