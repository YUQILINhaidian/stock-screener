"""
回测模块 - Pydantic 数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class BacktestRequest(BaseModel):
    """回测请求"""
    strategy_id: str = Field(..., description="策略ID")
    start_date: str = Field(..., description="回测开始日期 (YYYY-MM-DD)")
    end_date: str = Field(..., description="回测结束日期 (YYYY-MM-DD)")
    initial_capital: float = Field(100000.0, description="初始资金")
    hold_days: int = Field(20, description="持仓天数")
    stop_loss: float = Field(-8.0, description="止损比例 (%)")
    position_size: float = Field(0.1, description="单只股票仓位 (0-1)")
    commission: float = Field(0.0003, description="手续费率")
    slippage: float = Field(0.0001, description="滑点")

class BacktestTask(BaseModel):
    """回测任务"""
    task_id: str
    strategy_id: str
    status: str = Field("pending", description="pending/running/completed/error")
    progress: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class Trade(BaseModel):
    """单笔交易记录"""
    entry_date: date = Field(..., description="买入日期")
    exit_date: Optional[date] = Field(None, description="卖出日期")
    symbol: str
    name: str
    entry_price: float
    exit_price: Optional[float] = None
    quantity: int
    pnl: Optional[float] = Field(None, description="盈亏金额")
    pnl_pct: Optional[float] = Field(None, description="盈亏比例 (%)")
    hold_days: Optional[int] = Field(None, description="持仓天数")
    exit_reason: Optional[str] = Field(None, description="卖出原因 (stop_loss/take_profit/time_exit)")

class BacktestMetrics(BaseModel):
    """回测指标"""
    total_return: float = Field(..., description="总收益率 (%)")
    annual_return: float = Field(..., description="年化收益率 (%)")
    sharpe_ratio: float = Field(..., description="夏普比率")
    max_drawdown: float = Field(..., description="最大回撤 (%)")
    win_rate: float = Field(..., description="胜率 (%)")
    total_trades: int = Field(..., description="总交易次数")
    avg_win: float = Field(..., description="平均盈利 (%)")
    avg_loss: float = Field(..., description="平均亏损 (%)")
    profit_factor: float = Field(..., description="盈亏比")

class BacktestResponse(BaseModel):
    """回测响应"""
    task_id: str
    strategy_id: str
    status: str
    metrics: Optional[BacktestMetrics] = None
    trades: List[Trade] = Field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = Field(default_factory=list, description="[[date, value], ...]")
    monthly_returns: Dict[str, float] = Field(default_factory=dict, description="{2025-01: 5.2, ...}")
    created_at: datetime
    completed_at: Optional[datetime] = None
