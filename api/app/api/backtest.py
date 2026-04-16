"""
回测 API 路由
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
import uuid
from datetime import datetime

from app.models.backtest import (
    BacktestRequest,
    BacktestTask,
    BacktestResponse
)
from app.services.backtest_engine import BacktestEngine

router = APIRouter()

# 全局回测引擎
backtest_engine = BacktestEngine()

# 任务存储
tasks: dict[str, BacktestTask] = {}
results: dict[str, BacktestResponse] = {}

@router.post("/create", response_model=BacktestTask)
async def create_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """
    创建回测任务
    
    提交回测参数后，系统会在后台执行回测
    通过 /backtest/result/{task_id} 获取结果
    """
    task_id = str(uuid.uuid4())
    
    task = BacktestTask(
        task_id=task_id,
        strategy_id=request.strategy_id,
        status="pending",
        created_at=datetime.now()
    )
    tasks[task_id] = task
    
    # 后台执行回测
    background_tasks.add_task(execute_backtest, task_id, request)
    
    return task

@router.get("/result/{task_id}", response_model=BacktestResponse)
async def get_backtest_result(task_id: str):
    """获取回测结果"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    if task.status == "completed" and task_id in results:
        return results[task_id]
    elif task.status == "error":
        raise HTTPException(status_code=500, detail=task.error)
    else:
        return BacktestResponse(
            task_id=task_id,
            strategy_id=task.strategy_id,
            status=task.status,
            created_at=task.created_at
        )

async def execute_backtest(task_id: str, request: BacktestRequest):
    """后台执行回测"""
    task = tasks[task_id]
    
    try:
        task.status = "running"
        
        # 调用回测引擎
        result = await backtest_engine.run_backtest(request)
        
        # 保存结果
        results[task_id] = result
        task.status = "completed"
        task.completed_at = datetime.now()
        
    except Exception as e:
        task.status = "error"
        task.error = str(e)
