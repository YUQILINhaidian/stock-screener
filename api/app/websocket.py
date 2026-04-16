"""
WebSocket 连接管理器
"""

from fastapi import WebSocket

class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[task_id] = websocket
    
    def disconnect(self, task_id: str):
        if task_id in self.active_connections:
            del self.active_connections[task_id]
    
    async def send_message(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            await self.active_connections[task_id].send_json(message)

# 全局实例
manager = ConnectionManager()
