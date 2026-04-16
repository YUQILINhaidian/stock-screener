"""
应用配置管理
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "Stock Screener API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = f"sqlite:///{os.path.expanduser('~/.vntrader/database.db')}"
    FUNDAMENTAL_DB_URL: str = f"sqlite:///{os.path.expanduser('~/.vntrader/fundamental.db')}"
    
    # Redis 配置（用于缓存）
    REDIS_URL: Optional[str] = None
    REDIS_ENABLED: bool = False
    
    # 文件存储路径
    STOCK_POOL_DIR: str = os.path.expanduser("~/.vntrader/stock_pools")
    SCREEN_RESULTS_DIR: str = os.path.expanduser("~/.vntrader/screen_results")
    CHARTS_DIR: str = os.path.expanduser("~/.vntrader/charts")
    
    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 1
    
    # Claude API 配置（已废弃，使用下面的 LLM 配置）
    CLAUDE_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    CLAUDE_MAX_TOKENS: int = 4096
    
    # LLM 配置（支持多种模型）
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "claude")  # claude, openai, qwen, deepseek, generic
    LLM_API_KEY: Optional[str] = os.getenv("LLM_API_KEY", os.getenv("ANTHROPIC_API_KEY"))
    LLM_MODEL: Optional[str] = os.getenv("LLM_MODEL")  # 如果为空，使用提供商的默认模型
    LLM_BASE_URL: Optional[str] = os.getenv("LLM_BASE_URL")  # 用于 generic 提供商
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))
    
    # AkShare 配置
    AKSHARE_TIMEOUT: int = 30
    
    # 选股配置
    MAX_PARALLEL_STRATEGIES: int = 3  # 最多同时执行3个策略
    DEFAULT_TOP_N: int = 50  # 默认返回前50只股票
    
    # 回测配置
    DEFAULT_CAPITAL: float = 100000.0  # 默认初始资金10万
    DEFAULT_COMMISSION: float = 0.0003  # 默认手续费万3
    DEFAULT_SLIPPAGE: float = 0.0001  # 默认滑点0.01%
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 全局配置实例
settings = Settings()

# 确保必要目录存在
for dir_path in [settings.STOCK_POOL_DIR, settings.SCREEN_RESULTS_DIR, settings.CHARTS_DIR]:
    os.makedirs(dir_path, exist_ok=True)
