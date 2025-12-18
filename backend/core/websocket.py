"""WebSocket 连接管理，用于实时推送新邮件通知"""
from fastapi import WebSocket
from typing import Dict, Set
import json
import logging

logger = logging.getLogger(__name__)

# 存储每个用户的 WebSocket 连接
# key: user_id, value: set of WebSocket connections
connections: Dict[int, Set[WebSocket]] = {}


async def connect(websocket: WebSocket, user_id: int):
    """添加用户连接"""
    await websocket.accept()
    if user_id not in connections:
        connections[user_id] = set()
    connections[user_id].add(websocket)
    logger.info(f"WebSocket 连接: user_id={user_id}, 当前连接数={len(connections[user_id])}")


def disconnect(websocket: WebSocket, user_id: int):
    """移除用户连接"""
    if user_id in connections:
        connections[user_id].discard(websocket)
        if not connections[user_id]:
            del connections[user_id]
    logger.info(f"WebSocket 断开: user_id={user_id}")


async def notify_new_email(user_id: int, email_data: dict = None):
    """通知用户有新邮件"""
    if user_id not in connections:
        return
    
    message = json.dumps({
        "type": "new_email",
        "data": email_data or {}
    })
    
    dead_connections = set()
    for ws in connections[user_id]:
        try:
            await ws.send_text(message)
        except Exception:
            dead_connections.add(ws)
    
    # 清理断开的连接
    for ws in dead_connections:
        connections[user_id].discard(ws)


async def broadcast_to_user(user_id: int, message_type: str, data: dict = None):
    """向用户广播消息"""
    if user_id not in connections:
        return
    
    message = json.dumps({
        "type": message_type,
        "data": data or {}
    })
    
    dead_connections = set()
    for ws in connections[user_id]:
        try:
            await ws.send_text(message)
        except Exception:
            dead_connections.add(ws)
    
    for ws in dead_connections:
        connections[user_id].discard(ws)