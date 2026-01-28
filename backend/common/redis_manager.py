# common/redis_manager.py
from __future__ import annotations

import json
import os
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, ClassVar

import redis
from common.logger import get_logger

logger = get_logger("RedisManager")

@dataclass
class RedisManager:
    redis_url: str
    ttl_seconds: int = 60 * 60 * 24  # 24h
    
    # Class-level connection pool to ensure it's shared across instances
    _pool: ClassVar[Optional[redis.ConnectionPool]] = None

    @classmethod
    def from_env(cls) -> "RedisManager":
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        ttl = int(os.getenv("REDIS_TTL_SECONDS", str(60 * 60 * 24)))
        return cls(redis_url=url, ttl_seconds=ttl)

    def __post_init__(self) -> None:
        if RedisManager._pool is None:
            logger.info(f"Initializing Redis connection pool: {self.redis_url}")
            RedisManager._pool = redis.ConnectionPool.from_url(
                self.redis_url, 
                decode_responses=True,
                max_connections=50  # Limit max connections
            )
        
        self.client = redis.Redis(connection_pool=RedisManager._pool)
        self._r = self.client

    def publish(self, channel: str, message: Any) -> int:
        """Publish a message to a channel."""
        try:
            if not isinstance(message, str):
                message = json.dumps(message, ensure_ascii=False)
            return self._r.publish(channel, message)
        except Exception as e:
            logger.error(f"Failed to publish to {channel}: {e}")
            return 0

    def publish_event(self, task_id: str, event: Dict[str, Any]) -> int:
        """Publish an event to the task's WebSocket channel."""
        channel = f"task:{task_id}"
        return self.publish(channel, event)

    def ping(self) -> bool:
        try:
            return bool(self._r.ping())
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    def _key(self, task_id: str) -> str:
        return f"task:{task_id}"

    def set_status(
        self,
        task_id: str,
        *,
        status: str,
        current_step: Optional[int] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "task_id": task_id,
            "status": status,  # queued | processing | completed | failed
        }
        if current_step is not None:
            payload["current_step"] = current_step
        if progress is not None:
            payload["progress"] = int(progress)
        if message is not None:
            payload["message"] = message
        if extra:
            payload.update(extra)

        try:
            self._r.setex(self._key(task_id), self.ttl_seconds, json.dumps(payload, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Failed to set status for {task_id}: {e}")
            
        return payload

    def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        try:
            raw = self._r.get(self._key(task_id))
            if not raw:
                return None
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Failed to get status for {task_id}: {e}")
            return None
