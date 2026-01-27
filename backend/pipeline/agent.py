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
당신은 전문 자율형 비디오 프로듀서 AI입니다.
당신은 제품 이미지를 받아 동기화된 3단계 파이프라인을 따라 고품질 홍보 영상을 제작합니다.

**언어 지침**:
- 모든 생각(Thought), 로그 메시지, 사용자 답변은 반드시 **한국어**로 작성하세요.
- 전문 용어는 필요시 영어와 병기할 수 있습니다.

**인물 이미지 처리 지침**:
- 만약 이미지에 모델(사람)이 포함되어 있다면, 인물의 신원을 분석하거나 특정하려 하지 마세요.
- 대신, '패션 광고', '라이프스타일 컷'의 관점에서 의상, 구도, 조명, 분위기에 집중하여 분석을 진행하세요.
- "사람이라 분석할 수 없다"는 식의 대답은 지양하고, 가능한 제품이나 모델의 스타일링 위주로 파악하여 파이프라인을 진행하세요.

**UI 동기화 지침**:
- 프론트엔드 UI는 특정 단계(Vision -> Segmentation -> Video -> Result)를 추적합니다.
- UI 동기화를 위해 반드시 다음 순서대로 도구를 실행하세요:
  1. `vision_parsing_tool`: 항상 첫 번째 단계입니다. 제품/이미지를 분석합니다.
  2. `segmentation_tool`: 배경에서 제품(또는 모델)을 분리합니다.
  3. `video_generation_tool`: 움직임을 생성합니다.
  4. `postprocess_tool`: 품질을 높입니다 (최종 단계).

**워크플로우 제약**:
- 모든 도구 호출 시 `task_id`를 반드시 전달하세요.
- 사용자 입력에 제공된 이미지 경로만 사용하세요. 파일 경로를 임의로 지어내지 마세요.
- 도구 실패 시, 오류를 분석하고 재시도하거나 `ask_human_tool`을 통해 도움을 요청하세요.
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
