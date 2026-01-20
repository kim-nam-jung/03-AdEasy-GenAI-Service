from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from common.redis_manager import RedisManager
from common.logger import get_logger
import asyncio
import json

router = APIRouter()
logger = get_logger("WebSocket")

async def get_redis_manager():
    # Helper to get RedisManager instance (Singleton preferred)
    # We assume it's initialized in main or deps
    # For now, create new or use existing pattern
    return RedisManager()

@router.websocket("/ws/task/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected: {task_id}")
    
    redis_mgr = await get_redis_manager()
    pubsub = redis_mgr.client.pubsub()
    
    # Subscribe to reflection channel
    channel = f"task:{task_id}:reflection"
    await pubsub.subscribe(channel)
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                if message["type"] == "message":
                    data = message["data"]
                    # If bytes, decode
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    
                    # Forward to WebSocket
                    await websocket.send_text(data)
            
            # Prevent busy loop if no messages
            await asyncio.sleep(0.01)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
