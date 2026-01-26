from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from common.redis_manager import RedisManager
from common.logger import get_logger
from app.core.config import settings
import redis.asyncio as async_redis
import asyncio
import json

router = APIRouter()
logger = get_logger("WebSocket")

@router.websocket("/ws_v2/task/{task_id}")
@router.websocket("/ws_v2/{task_id}")
@router.websocket("/ws/task/{task_id}")
@router.websocket("/ws/{task_id}")
async def websocket_task(websocket: WebSocket, task_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected: {task_id}")
    
    redis_mgr = RedisManager.from_env()
    async_client = async_redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = async_client.pubsub()
    
    channel = f"task:{task_id}"
    await pubsub.subscribe(channel)
    
    seq_id = 0
    
    async def send_heartbeat():
        while True:
            try:
                await asyncio.sleep(30)
                await websocket.send_json({"type": "ping", "timestamp": asyncio.get_event_loop().time()})
            except Exception:
                break

    heartbeat_task = asyncio.create_task(send_heartbeat())
    
    try:
        # Send Initial State
        current_status = redis_mgr.get_status(task_id)
        if current_status:
            seq_id += 1
            initial_event = {
                "type": "status",
                "status": current_status.get("status", "unknown"),
                "message": current_status.get("message", ""),
                "data": current_status.get("result", {})
            }
            await websocket.send_json({"seq": seq_id, "data": initial_event})
            
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                
                # Try to parse if it's already a JSON string to avoid double-encoding
                try:
                    event_data = json.loads(data)
                except:
                    event_data = data
                
                seq_id += 1
                await websocket.send_json({"seq": seq_id, "data": event_data})
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
    finally:
        heartbeat_task.cancel()
        await pubsub.unsubscribe(channel)
        await async_client.close()
        try:
            await websocket.close()
        except:
            pass
