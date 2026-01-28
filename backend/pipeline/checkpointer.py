from langgraph.checkpoint.redis import RedisSaver
import os

_checkpointer = None

def get_checkpointer() -> RedisSaver:
    global _checkpointer
    if _checkpointer is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _checkpointer = RedisSaver.from_url(redis_url)
    return _checkpointer
