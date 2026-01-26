import logging
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from common.config import Config
from common.redis_manager import RedisManager
from common.callback import RedisStreamingCallback
from pipeline.tools import (
    vision_parsing_tool,
    segmentation_tool,
    video_generation_tool,
    postprocess_tool,
    reflection_tool,
    ask_human_tool
)

logger = logging.getLogger(__name__)

class AdGenAgent:
    """
    Autonomous Video Generation Agent.
    Uses GPT-4o and tools to produce high-quality product videos.
    """
    def __init__(self, task_id: str, redis_mgr: RedisManager):
        self.task_id = task_id
        self.redis_mgr = redis_mgr
        
    def _handle_error(self, error) -> str:
        """Custom error handler for the AgentExecutor."""
        return f"Tool execution failed with error: {str(error)}. Please analyzing the error. If it is a transient error, retry with different parameters. If it persists (or if you have retried already), call 'ask_human_tool' to request manual intervention."

    def create_executor(self) -> AgentExecutor:
        # 1. Define Tools
        tools = [
            vision_parsing_tool,
            segmentation_tool,
            video_generation_tool,
            postprocess_tool,
            reflection_tool,
            ask_human_tool
        ]
        
        # 2. Configure LLM
        # Always use smart model for orchestration
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            streaming=True,
            callbacks=[RedisStreamingCallback(self.redis_mgr, self.task_id)]
        )
        
        # 3. Define System Prompt
        system_prompt = """
You are an expert Autonomous Video Producer AI.
Your goal is to take a product image and generate a high-quality promotional video.

**Workflow Guidelines**:
1. **Analyze**: ALWAYS start by using `vision_parsing_tool` to understand the product and get prompt suggestions.
2. **Segment**: Use `segmentation_tool` to isolate the product. Check `vision_parsing_tool` output for 'segmentation_hint'.
3. **Generate**: Use `video_generation_tool` to create the video. Use 'suggested_video_prompt' from vision analysis if available.
4. **Post-process**: Use `postprocess_tool` to enhance quality (RIFE/Real-CUGAN).
5. **Verify**: At each critical step, you MAY use `reflection_tool` to self-critique. If quality is bad, retry with different parameters.
6. **Fallback**: If you fail repeatedly (e.g. 2 retries), you MUST use `ask_human_tool` to ask the user for help.

**Constraints**:
- Do not make up file paths. Use the paths returned by the tools.
- If `ask_human_tool` is called, STOP and wait (the system handles the pause).
- When finished, ensure the final video path is clearly returned or stated.
- If a tool fails, analyze the error message. Do not immediately give up. Try a fallback parameter (e.g., lower resolution) or call ask_human_tool if stuck.

**Tools**: {tools}
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # 4. Create Agent
        agent = create_openai_tools_agent(llm, tools, prompt)
        
        # 5. Create Executor
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=self._handle_error,
            max_iterations=15, # Prevent infinite loops
            return_intermediate_steps=True
        )
        
        return executor
