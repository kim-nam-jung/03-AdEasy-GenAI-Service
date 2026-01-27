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
    
    redis_mgr = None
    async_client = None
    pubsub = None
    heartbeat_task = None

    try:
        logger.info(f"Initializing Redis for task {task_id} with URL: {settings.REDIS_URL}")
        redis_mgr = RedisManager.from_env()
        async_client = async_redis.from_url(settings.REDIS_URL, decode_responses=True)
        pubsub = async_client.pubsub()
        
        channel = f"task:{task_id}"
        logger.info(f"Subscribing to channel: {channel}")
        await pubsub.subscribe(channel)
        logger.info(f"Subscribed to {channel}")
        
        seq_id = 0
        
        async def send_heartbeat():
            while True:
                try:
                    await asyncio.sleep(30)
                    if websocket.client_state == 1: # WebSocketState.CONNECTED
                        await websocket.send_json({"type": "ping", "timestamp": asyncio.get_event_loop().time()})
                    else:
                        break
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
                    break

        heartbeat_task = asyncio.create_task(send_heartbeat())
        
        # Send Initial State
        current_status = redis_mgr.get_status(task_id)
        if current_status:
            logger.info(f"Found initial status for {task_id}: {current_status.get('status')}")
            seq_id += 1
            initial_event = {
                "type": "status",
                "status": current_status.get("status", "unknown"),
                "message": current_status.get("message", ""),
                "data": current_status.get("result", {})
            }
            await websocket.send_json({"seq": seq_id, "data": initial_event})
        else:
            logger.info(f"No initial status found for {task_id}")
            
        logger.info("Entering PubSub loop")
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
        logger.info(f"WebSocket disconnected by client: {task_id}")
    except Exception as e:
        import traceback
        logger.error(f"WebSocket error for task {task_id}: {e}\n{traceback.format_exc()}")
    finally:
        logger.info(f"Cleaning up WebSocket for {task_id}")
        if heartbeat_task:
            heartbeat_task.cancel()
        if pubsub:
            await pubsub.unsubscribe(channel)
        if async_client:
            await async_client.close()
        try:
            await websocket.close()
        except:
            pass
