"""
Stock Screener API - FastAPI Main Entry Point

提供选股、回测、股票池管理、AI 助手的 RESTful API 和 WebSocket 接口
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.config import settings
from app.websocket import manager

# 创建 FastAPI 应用
app = FastAPI(
    title="Stock Screener API",
    description="量化选股系统 API - 提供选股、回测、股票池管理、AI 策略分析",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React 开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "service": "Stock Screener API",
        "version": "1.0.0"
    }

# 根路径
@app.get("/", tags=["系统"])
async def root():
    """API 根路径"""
    return {
        "message": "Stock Screener API is running",
        "docs": "/docs",
        "health": "/health"
    }

# 注册路由（延迟导入避免循环依赖）
from app.api import screener, backtest, portfolio, ai

app.include_router(screener.router, prefix="/api", tags=["选股 (Screener)"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["回测 (Backtest)"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["股票池 (Portfolio)"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI 助手 (AI Assistant)"])

# WebSocket 端点（选股进度推送）
@app.websocket("/ws/screen/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket 端点 - 实时推送选股进度
    
    客户端连接后会收到：
    {
        "progress": 35.5,  # 进度百分比
        "current": "正在处理第1800/5189只股票...",
        "found": 12,  # 已找到符合条件的股票数
        "status": "running"  # running / completed / error
    }
    """
    await manager.connect(task_id, websocket)
    try:
        while True:
            # 保持连接，等待客户端消息（心跳包）
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(task_id)

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc)
        }
    )

if __name__ == "__main__":
    # 开发模式启动
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
