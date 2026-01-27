from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish
from common.redis_manager import RedisManager
from common.logger import get_logger
import json

logger = get_logger("RedisCallback")

# Tool descriptions in Korean for user-friendly messages
TOOL_DESCRIPTIONS = {
    "vision_parsing_tool": "업로드된 이미지를 분석하여 제품의 특성과 최적의 연출 방향을 파악하고 있습니다...",
    "planning_tool": "분석 결과를 바탕으로 영상 연출 기획안을 작성하고 있습니다...",
    "segmentation_tool": "배경에서 제품을 정교하게 분리하고 있습니다...",
    "reflection_tool": "작업 결과물의 품질을 검수하고 있습니다...",
    "video_generation_tool": "AI 영상 생성 모델을 사용하여 제품 영상을 제작하고 있습니다...",
    "postprocess_tool": "최종 영상의 해상도와 품질을 향상시키고 있습니다...",
    "ask_human_tool": "사용자의 피드백을 요청하고 있습니다...",
}

class RedisStreamingCallback(BaseCallbackHandler):
    """
    Callback handler that streams LLM tokens, thoughts, and tool events to Redis Pub/Sub.
    """
    def __init__(self, redis_mgr: RedisManager, task_id: str):
        self.redis = redis_mgr
        self.task_id = task_id
        # We publish to the main task channel so UI can multiplex
        self.channel = f"task:{task_id}"
    
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token."""
        try:
            self.redis.client.publish(self.channel, json.dumps({
                "type": "token", 
                "content": token
            }, ensure_ascii=False))
        except Exception as e:
            logger.error(f"[Task:{self.task_id}] on_llm_new_token failed: {e}")

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Run when LLM ends."""
        try:
            self.redis.client.publish(self.channel, json.dumps({
                "type": "end", 
                "content": ""
            }))
        except Exception as e:
            logger.error(f"[Task:{self.task_id}] on_llm_end failed: {e}")

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """Run when an agent action is taken (tool call selected)."""
        try:
            # Send a user-friendly thought message before tool call
            tool_desc = TOOL_DESCRIPTIONS.get(action.tool, f"{action.tool}을(를) 실행하고 있습니다...")
            self.redis.client.publish(self.channel, json.dumps({
                "type": "thought",
                "message": tool_desc
            }, ensure_ascii=False))

            # Then send the tool call event
            self.redis.client.publish(self.channel, json.dumps({
                "type": "tool_call",
                "tool": action.tool,
                "tool_input": str(action.tool_input),
                "log": action.log
            }, ensure_ascii=False))
        except Exception as e:
            logger.error(f"[Task:{self.task_id}] on_agent_action failed: {e}")

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> Any:
        """Run when tool starts running."""
        # Already handled by on_agent_action mostly, but good for confirmation
        pass

    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """Run when tool ends running."""
        try:
            # We only send tool results to the log if they aren't private/too large.
            # For now, send everything for transparency.
            self.redis.client.publish(self.channel, json.dumps({
                "type": "tool_result",
                "output": output
            }, ensure_ascii=False))
        except Exception as e:
            logger.error(f"[Task:{self.task_id}] on_tool_end failed: {e}")

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        """Run when agent finishes."""
        try:
            self.redis.client.publish(self.channel, json.dumps({
                "type": "thought",
                "message": finish.return_values.get("output", "Agent finished task.")
            }, ensure_ascii=False))
        except Exception as e:
            logger.error(f"[Task:{self.task_id}] on_agent_finish failed: {e}")
