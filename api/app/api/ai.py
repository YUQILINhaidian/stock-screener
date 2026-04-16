"""
AI 助手 API 路由
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.services.ai_service import AIService

router = APIRouter()

# 全局 AI 服务
ai_service = AIService()

# ========== 请求/响应模型 ==========

class MarketAnalysisRequest(BaseModel):
    """市场分析请求"""
    index: str = Field("SSE", description="指数代码 (SSE/SZSE)")
    period: str = Field("1M", description="分析周期 (1M/3M/6M)")

class MarketAnalysisResponse(BaseModel):
    """市场分析响应"""
    trend: str = Field(..., description="趋势 (bull/bear/sideways)")
    confidence: float = Field(..., description="置信度 (0-1)")
    reason: str = Field(..., description="分析理由")
    recommended_strategies: List[str] = Field(..., description="推荐策略")

class StockAnalysisRequest(BaseModel):
    """个股分析请求"""
    symbol: str = Field(..., description="股票代码")
    strategy: Optional[str] = Field(None, description="关联策略")

class StockAnalysisResponse(BaseModel):
    """个股分析响应"""
    symbol: str
    name: str
    summary: str = Field(..., description="综合评价")
    fundamentals: Dict[str, Any] = Field(..., description="基本面")
    technicals: Dict[str, Any] = Field(..., description="技术面")
    risk: Dict[str, Any] = Field(..., description="风险提示")
    action: str = Field(..., description="建议操作 (buy/hold/sell)")
    score: float = Field(..., description="AI评分 (0-100)")

class NLScreenRequest(BaseModel):
    """自然语言选股请求"""
    query: str = Field(..., description="自然语言描述")

class NLScreenResponse(BaseModel):
    """自然语言选股响应"""
    generated_conditions: Dict[str, Any] = Field(..., description="生成的筛选条件")
    results: List[Dict[str, Any]] = Field(..., description="筛选结果")

# ========== API 端点 ==========

@router.post("/market-analysis", response_model=MarketAnalysisResponse)
async def analyze_market(request: MarketAnalysisRequest):
    """
    市场环境分析
    
    使用 Claude API 分析当前大盘趋势，给出策略建议
    """
    try:
        result = await ai_service.analyze_market(
            index=request.index,
            period=request.period
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"市场分析失败: {str(e)}")

@router.post("/stock-analysis", response_model=StockAnalysisResponse)
async def analyze_stock(request: StockAnalysisRequest):
    """
    个股 AI 深度分析
    
    对单只股票进行基本面+技术面综合分析，给出评分和建议
    """
    try:
        result = await ai_service.analyze_stock(
            symbol=request.symbol,
            strategy=request.strategy
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"个股分析失败: {str(e)}")

@router.post("/nl-screen", response_model=NLScreenResponse)
async def natural_language_screen(request: NLScreenRequest):
    """
    自然语言智能选股
    
    用户用自然语言描述需求，AI 解析为筛选条件并执行
    
    例如：
    - "找出最近突破的新能源龙头股"
    - "RPS高的科技股，成交额大于5亿"
    """
    try:
        result = await ai_service.nl_screen(query=request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"智能选股失败: {str(e)}")
