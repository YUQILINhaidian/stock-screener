"""
选股模块 - Pydantic 数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# ========== 策略相关 ==========

class StrategyInfo(BaseModel):
    """策略信息"""
    id: str = Field(..., description="策略唯一标识")
    name: str = Field(..., description="策略名称")
    description: str = Field(..., description="策略描述")
    category: str = Field(..., description="策略类别（RPS/技术/基本面）")
    params: Dict[str, Any] = Field(default_factory=dict, description="可配置参数")
    last_run: Optional[datetime] = Field(None, description="最后一次运行时间")
    avg_return: Optional[float] = Field(None, description="平均收益率（回测）")
    win_rate: Optional[float] = Field(None, description="胜率（回测）")

class ScreenRequest(BaseModel):
    """选股请求"""
    strategy_id: str = Field(..., description="策略ID")
    params: Dict[str, Any] = Field(default_factory=dict, description="筛选参数")
    top_n: int = Field(50, description="返回前N只股票")
    parallel: bool = Field(False, description="是否并行执行多个策略")
    update_data: bool = Field(False, description="是否先更新数据")

class ScreenTask(BaseModel):
    """选股任务"""
    task_id: str = Field(..., description="任务ID")
    strategy_id: str = Field(..., description="策略ID")
    status: str = Field(..., description="任务状态 (pending/running/completed/error)")
    progress: float = Field(0.0, description="进度百分比")
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

# ========== 股票相关 ==========

class StockInfo(BaseModel):
    """股票基本信息"""
    symbol: str = Field(..., description="股票代码（带后缀，如 000001.SZSE）")
    code: str = Field(..., description="股票代码（6位）")
    name: str = Field(..., description="股票名称")
    exchange: str = Field(..., description="交易所（SSE/SZSE）")
    industry: Optional[str] = Field(None, description="所属行业")
    market_cap: Optional[float] = Field(None, description="总市值（亿元）")

class StockTechnical(BaseModel):
    """股票技术指标"""
    symbol: str
    close: float = Field(..., description="收盘价")
    change_pct: float = Field(..., description="涨跌幅")
    volume: float = Field(..., description="成交量")
    turnover: float = Field(..., description="成交额")
    volume_ratio: Optional[float] = Field(None, description="量比")
    
    # RPS 指标
    rps_50: Optional[float] = Field(None, description="RPS50")
    rps_120: Optional[float] = Field(None, description="RPS120")
    rps_250: Optional[float] = Field(None, description="RPS250")
    
    # 均线
    ma_20: Optional[float] = Field(None, description="20日均线")
    ma_60: Optional[float] = Field(None, description="60日均线")
    ma_120: Optional[float] = Field(None, description="120日均线")
    
    # 其他指标
    max_dd: Optional[float] = Field(None, description="最大回撤")
    distance_from_high: Optional[float] = Field(None, description="距离年内新高的距离")

class ScreenResult(BaseModel):
    """选股结果（单只股票）"""
    stock_info: StockInfo
    technical: StockTechnical
    score: float = Field(..., description="综合评分")
    rank: int = Field(..., description="排名")
    reason: str = Field(..., description="入选理由")

class ScreenResponse(BaseModel):
    """选股响应"""
    task_id: str
    strategy_id: str
    status: str
    results: List[ScreenResult] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict, description="汇总统计")
    created_at: datetime
    completed_at: Optional[datetime] = None

# ========== WebSocket 消息 ==========

class ProgressMessage(BaseModel):
    """进度推送消息"""
    progress: float = Field(..., description="进度百分比 (0-100)")
    current: str = Field(..., description="当前状态描述")
    found: int = Field(0, description="已找到的股票数")
    total: int = Field(0, description="总股票数")
    status: str = Field("running", description="任务状态")
