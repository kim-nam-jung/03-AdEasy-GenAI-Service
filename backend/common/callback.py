from typing import Any, Dict, List, Optional
from uuid import UUID
from langchain_core.callbacks import BaseCallbackHandler
from common.redis_manager import RedisManager
import json

class RedisStreamingCallback(BaseCallbackHandler):
    """
    Callback handler that streams LLM tokens (or thoughts) to Redis Pub/Sub.
    Used for showing the Supervisor's "Reflection" in real-time on the frontend.
    """
    def __init__(self, redis_mgr: RedisManager, task_id: str, channel_suffix: str = "reflection"):
        self.redis = redis_mgr
        self.task_id = task_id
        self.channel = f"task:{task_id}:{channel_suffix}"
    
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""
        # Optional: Notify start
        pass

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        # Publish token to Redis Channel
        # self.redis.publish(self.channel, token)
        # Note: RedisManager might not have publish method exposed directly, 
        # or we might need to use the underlying client.
        
        # Assuming RedisManager has a 'get_client()' or we extend it.
        # Check RedisManager implementation first.
        # For now, let's assume valid client access.
        try:
            self.redis.client.publish(self.channel, json.dumps({"type": "token", "content": token}))
        except Exception as e:
            # Silently fail to avoid breaking the pipeline
            pass

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Run when LLM ends running."""
        try:
            self.redis.client.publish(self.channel, json.dumps({"type": "end", "content": ""}))
        except Exception:
            pass
            
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None:
        """Run when chain starts running."""
        pass

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Run when chain ends running."""
        pass
        
    def on_custom_event(self, name: str, data: Any, **kwargs: Any) -> Any:
        # Support for custom events if needed
        pass
