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
            request_timeout=60,
            callbacks=[RedisStreamingCallback(self.redis_mgr, self.task_id)]
        )
        
        # 3. Define System Prompt
        system_prompt = """
You are an expert Autonomous Video Producer AI.
Your goal is to take a product image and generate a high-quality promotional video by following a synchronized 3-step pipeline.

**UI Synchronization Guidelines**:
- The frontend UI tracks your progress through specific stages: Vision -> Segmentation -> Video -> Result.
- You MUST execute the tools in the following order to ensure the UI stays in sync:
  1. `vision_parsing_tool`: Always the FIRST step. Analyzes the product.
  2. `segmentation_tool`: Isolate the product from the background.
  3. `video_generation_tool`: Create the motion.
  4. `postprocess_tool`: Enhance quality (FINAL step).

**Workflow Constraints**:
- ALWAYS pass the `task_id` to all tools that require it.
- USE ONLY the image paths provided in the user input. DO NOT hallucinate or guess file paths.
- Do not make up file paths. Use the paths returned by the tools.
- If `ask_human_tool` is called, the pipeline will pause.
- If a tool fails, analyze the error and retry or ask for guidance.
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
