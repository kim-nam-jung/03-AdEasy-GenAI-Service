# common/redis_manager.py
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import redis


@dataclass
class RedisManager:
    redis_url: str
    ttl_seconds: int = 60 * 60 * 24  # 24h

    @classmethod
    def from_env(cls) -> "RedisManager":
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        ttl = int(os.getenv("REDIS_TTL_SECONDS", str(60 * 60 * 24)))
        return cls(redis_url=url, ttl_seconds=ttl)

    def __post_init__(self) -> None:
        self._r = redis.from_url(self.redis_url, decode_responses=True)

    def ping(self) -> bool:
        return bool(self._r.ping())

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

        self._r.setex(self._key(task_id), self.ttl_seconds, json.dumps(payload, ensure_ascii=False))
        return payload

    def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        raw = self._r.get(self._key(task_id))
        if not raw:
            return None
        return json.loads(raw)
