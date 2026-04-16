"""
AI 服务 - 使用灵活的 LLM 提供商架构

支持多种大模型：Claude、OpenAI、通义千问、DeepSeek等
"""

import os
from typing import Dict, Any, List, Optional
from app.config import settings
from app.services.llm_providers import get_default_llm_provider, LLMProvider, LLMFactory
from app.db import execute_query

class AIService:
    """AI 服务"""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """
        初始化 AI 服务
        
        Args:
            llm_provider: LLM 提供商（如果为空，使用默认配置）
        """
        self.llm_provider = llm_provider or get_default_llm_provider()
    
    async def analyze_market(self, index: str = "SSE", period: str = "1M") -> Dict[str, Any]:
        """
        市场环境分析
        
        Args:
            index: 指数代码 (SSE/SZSE)
            period: 分析周期 (1M/3M/6M)
        
        Returns:
            {
                "trend": "bull|bear|sideways",
                "confidence": 0.85,
                "reason": "分析理由",
                "recommended_strategies": ["策略1", "策略2"]
            }
        """
        # 获取指数数据
        index_data = self._get_index_data(index, period)
        
        # 构建 prompt
        prompt = f"""请分析当前A股市场环境：

【指数数据】
- 指数：{"上证指数" if index == "SSE" else "深证成指"}
- 周期：{period}
- 当前点位：{index_data.get('current', 'N/A')}
- 涨跌幅：{index_data.get('change_pct', 'N/A')}%
- 成交量变化：{index_data.get('volume_change', 'N/A')}

请分析：
1. 当前市场趋势（牛市/熊市/震荡市）
2. 判断置信度（0-1）
3. 分析理由（不超过100字）
4. 推荐2-3个适合当前市场的选股策略

请以 JSON 格式返回：
{{
  "trend": "bull/bear/sideways",
  "confidence": 0.85,
  "reason": "分析理由",
  "recommended_strategies": ["月线反转策略", "口袋支点策略"]
}}
"""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_provider.chat(
                messages,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS
            )
            
            # 解析 JSON 响应
            import json
            import re
            
            # 尝试提取 JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # 如果没有 JSON，返回默认结果
                result = {
                    "trend": "sideways",
                    "confidence": 0.7,
                    "reason": response[:100],
                    "recommended_strategies": ["月线反转策略", "口袋支点策略"]
                }
            
            return result
            
        except Exception as e:
            print(f"市场分析失败: {str(e)}")
            # 返回默认结果
            return {
                "trend": "sideways",
                "confidence": 0.5,
                "reason": f"分析失败: {str(e)}",
                "recommended_strategies": ["月线反转策略"]
            }
    
    async def analyze_stock(
        self,
        symbol: str,
        strategy: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        个股 AI 深度分析
        
        Args:
            symbol: 股票代码
            strategy: 关联策略（可选）
        
        Returns:
            {
                "symbol": "300185",
                "name": "通裕重工",
                "summary": "AI 综合评价",
                "fundamentals": {...},
                "technicals": {...},
                "risk": {...},
                "action": "buy|hold|sell",
                "score": 85.0
            }
        """
        # 获取股票数据
        stock_data = self._get_stock_data(symbol)
        
        if not stock_data:
            return {
                "symbol": symbol,
                "name": symbol,
                "summary": "股票数据不足",
                "fundamentals": {},
                "technicals": {},
                "risk": {},
                "action": "hold",
                "score": 50.0
            }
        
        # 构建 prompt
        prompt = f"""请分析股票 {stock_data['name']} ({symbol})：

【技术指标】
- 收盘价：{stock_data.get('close', 'N/A')}
- 涨跌幅：{stock_data.get('change_pct', 'N/A')}%
- RPS50：{stock_data.get('rps_50', 'N/A')}
- RPS120：{stock_data.get('rps_120', 'N/A')}
- RPS250：{stock_data.get('rps_250', 'N/A')}
- 量比：{stock_data.get('volume_ratio', 'N/A')}
- 最大回撤：{stock_data.get('max_dd', 'N/A')}%

{"【策略匹配】\n" + strategy if strategy else ""}

请分析：
1. 技术面评价（20字以内）
2. 综合评分（0-100分）
3. 建议操作（buy/hold/sell）
4. 风险提示

以 JSON 格式返回：
{{
  "summary": "技术面强势，RPS高位",
  "score": 85,
  "action": "buy",
  "risk": {{"stop_loss": -8, "position_size": 0.1}},
  "reason": "详细理由"
}}
"""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_provider.chat(
                messages,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS
            )
            
            # 解析 JSON
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                ai_result = json.loads(json_match.group())
            else:
                ai_result = {
                    "summary": response[:50],
                    "score": 70,
                    "action": "hold",
                    "risk": {"stop_loss": -8, "position_size": 0.1}
                }
            
            return {
                "symbol": symbol,
                "name": stock_data['name'],
                "summary": ai_result.get("summary", ""),
                "fundamentals": stock_data.get("fundamentals", {}),
                "technicals": {
                    "rps_50": stock_data.get("rps_50"),
                    "rps_120": stock_data.get("rps_120"),
                    "rps_250": stock_data.get("rps_250"),
                    "volume_ratio": stock_data.get("volume_ratio"),
                },
                "risk": ai_result.get("risk", {}),
                "action": ai_result.get("action", "hold"),
                "score": ai_result.get("score", 70.0)
            }
            
        except Exception as e:
            print(f"个股分析失败: {str(e)}")
            return {
                "symbol": symbol,
                "name": stock_data['name'],
                "summary": f"分析失败: {str(e)}",
                "fundamentals": {},
                "technicals": {},
                "risk": {},
                "action": "hold",
                "score": 50.0
            }
    
    async def nl_screen(self, query: str) -> Dict[str, Any]:
        """
        自然语言智能选股
        
        Args:
            query: 自然语言描述
        
        Returns:
            {
                "generated_conditions": {...},
                "results": [...]
            }
        """
        prompt = f"""用户想要选股，需求如下：

"{query}"

请将这个自然语言需求转换为结构化的筛选条件。

可用的筛选条件：
- industry: 行业（如：新能源、半导体、医药）
- rps_120: RPS120 阈值（如：>= 90）
- rps_250: RPS250 阈值
- volume_ratio: 量比（如：>= 1.5）
- market_cap: 市值范围（如：large/mid/small）
- change_pct: 涨跌幅（如：> 5）
- breakout: 是否突破（recent_high/year_high）

以 JSON 格式返回：
{{
  "industry": ["新能源", "半导体"],
  "rps_120": ">= 90",
  "volume_ratio": ">= 1.5",
  "breakout": "recent_high"
}}
"""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_provider.chat(
                messages,
                temperature=0.3,  # 降低温度，提高准确性
                max_tokens=1000
            )
            
            # 解析 JSON
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                conditions = json.loads(json_match.group())
            else:
                conditions = {}
            
            return {
                "generated_conditions": conditions,
                "results": []  # TODO: 实际执行筛选
            }
            
        except Exception as e:
            print(f"自然语言选股失败: {str(e)}")
            return {
                "generated_conditions": {},
                "results": []
            }
    
    # ========== 辅助方法 ==========
    
    def _get_index_data(self, index: str, period: str) -> Dict[str, Any]:
        """获取指数数据（模拟）"""
        # TODO: 从数据库获取真实指数数据
        return {
            "current": 3000,
            "change_pct": -1.2,
            "volume_change": -15
        }
    
    def _get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取股票数据"""
        try:
            # 从数据库获取股票数据
            query = """
                SELECT symbol, close_price, volume, turnover
                FROM dbbardata
                WHERE symbol = ? AND interval = 'd'
                ORDER BY datetime DESC
                LIMIT 1
            """
            code = symbol.split('.')[0].lstrip('0')
            rows = execute_query(query, (code,), db_type="kline")
            
            if not rows:
                return None
            
            row = rows[0]
            return {
                "name": symbol,  # TODO: 获取股票名称
                "close": row.get("close_price"),
                "volume": row.get("volume"),
                "turnover": row.get("turnover"),
                # TODO: 获取 RPS 等指标
                "rps_50": None,
                "rps_120": None,
                "rps_250": None,
                "volume_ratio": None,
                "max_dd": None,
                "change_pct": 0,
                "fundamentals": {}
            }
            
        except Exception as e:
            print(f"获取股票数据失败: {str(e)}")
            return None
