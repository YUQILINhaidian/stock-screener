"""
选股 API 路由
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import uuid
from datetime import datetime

from app.models.screener import (
    StrategyInfo,
    ScreenRequest,
    ScreenTask,
    ScreenResponse,
    ScreenResult
)
from app.services.screener_engine import ScreenerEngine
from app.websocket import manager

router = APIRouter()

# 全局选股引擎实例
screener_engine = ScreenerEngine()

# 任务存储（生产环境应使用 Redis）
tasks: dict[str, ScreenTask] = {}
results: dict[str, ScreenResponse] = {}

@router.get("/strategies", response_model=List[StrategyInfo])
async def get_strategies():
    """
    获取所有可用的选股策略列表
    
    返回策略的基本信息、参数说明、历史收益等
    """
    return screener_engine.get_strategies()

@router.post("/screen/run", response_model=ScreenTask)
async def run_screen(request: ScreenRequest, background_tasks: BackgroundTasks):
    """
    执行选股任务（异步）
    
    1. 创建任务ID
    2. 后台执行选股
    3. 通过 WebSocket 推送进度
    4. 完成后可通过 /screen/result/{task_id} 获取结果
    """
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 创建任务记录
    task = ScreenTask(
        task_id=task_id,
        strategy_id=request.strategy_id,
        status="pending",
        created_at=datetime.now()
    )
    tasks[task_id] = task
    
    # 后台执行选股
    background_tasks.add_task(
        execute_screen_task,
        task_id,
        request
    )
    
    return task

@router.get("/screen/result/{task_id}", response_model=ScreenResponse)
async def get_screen_result(task_id: str):
    """
    获取选股任务结果
    
    如果任务还在运行，返回状态信息
    如果任务完成，返回完整的选股结果
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    if task.status == "completed" and task_id in results:
        return results[task_id]
    elif task.status == "error":
        raise HTTPException(status_code=500, detail=task.error)
    else:
        # 任务还在运行
        return ScreenResponse(
            task_id=task_id,
            strategy_id=task.strategy_id,
            status=task.status,
            results=[],
            created_at=task.created_at
        )

@router.delete("/screen/result/{task_id}")
async def delete_screen_result(task_id: str):
    """删除选股任务和结果"""
    if task_id in tasks:
        del tasks[task_id]
    if task_id in results:
        del results[task_id]
    return {"message": "Task deleted successfully"}

# ========== 后台任务执行函数 ==========

async def execute_screen_task(task_id: str, request: ScreenRequest):
    """
    后台执行选股任务
    
    1. 更新任务状态为 running
    2. 调用选股引擎
    3. 通过 WebSocket 推送进度
    4. 保存结果
    """
    task = tasks[task_id]
    
    try:
        # 更新状态
        task.status = "running"
        task.started_at = datetime.now()
        
        # 如果需要更新数据
        if request.update_data:
            await manager.send_message(task_id, {
                "progress": 0,
                "current": "正在更新 K 线数据...",
                "status": "running"
            })
            screener_engine.update_data()
        
        # 执行选股，带进度回调
        async def progress_callback(progress: float, current: str, found: int, total: int):
            task.progress = progress
            await manager.send_message(task_id, {
                "progress": progress,
                "current": current,
                "found": found,
                "total": total,
                "status": "running"
            })
        
        screen_results = await screener_engine.run_strategy(
            strategy_id=request.strategy_id,
            params=request.params,
            top_n=request.top_n,
            progress_callback=progress_callback
        )
        
        # 保存结果
        response = ScreenResponse(
            task_id=task_id,
            strategy_id=request.strategy_id,
            status="completed",
            results=screen_results["results"],
            summary=screen_results["summary"],
            created_at=task.created_at,
            completed_at=datetime.now()
        )
        results[task_id] = response
        
        # 更新任务状态
        task.status = "completed"
        task.completed_at = datetime.now()
        task.progress = 100.0
        
        # 发送完成消息
        await manager.send_message(task_id, {
            "progress": 100,
            "current": f"选股完成！共找到 {len(screen_results['results'])} 只股票",
            "found": len(screen_results["results"]),
            "status": "completed"
        })
        
    except Exception as e:
        # 错误处理
        task.status = "error"
        task.error = str(e)
        await manager.send_message(task_id, {
            "progress": task.progress,
            "current": f"选股失败: {str(e)}",
            "status": "error"
        })
