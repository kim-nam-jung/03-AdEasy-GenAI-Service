from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from common.redis_manager import RedisManager
from common.logger import get_logger
import asyncio
import json

router = APIRouter()
logger = get_logger("WebSocket")

@router.websocket("/ws/{task_id}")
async def websocket_task(websocket: WebSocket, task_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected: {task_id}")
    
    redis_mgr = RedisManager.from_env()
    pubsub = redis_mgr.client.pubsub()
    
    # 1. Subscribe to main task channel
    channel = f"task:{task_id}"
    await pubsub.subscribe(channel)
    
    try:
        # 2. Send Initial State (Important for reconnection/refresh)
        current_status = redis_mgr.get_status(task_id)
        if current_status:
            # Construct a 'status' event to sync frontend
            initial_event = {
                "type": "status",
                "status": current_status.get("status", "unknown"),
                "message": current_status.get("message", ""),
                "data": current_status.get("result", {})
            }
            await websocket.send_text(json.dumps(initial_event))
            
            # If there are logs, we might want to send them too, but Redis doesn't store full logs in 'status' usually.
            # Assuming 'status' is enough to restore UI state (tabs, progress).
            
        while True:
            # 3. Listen for real-time updates
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    
                    # Forward directly to frontend
                    # The Agent publishes JSON strings, so we can just forward them.
                    # Or if they are raw strings, we wrap them.
                    # Our AdGenAgent uses redis_mgr.publish(channel, dict) which dumps to JSON.
                    await websocket.send_text(data)
            
            await asyncio.sleep(0.01)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
