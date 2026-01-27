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
    ask_human_tool,
    planning_tool
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
            ask_human_tool,
            planning_tool
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
  2. `planning_tool`: 분석 결과를 바탕으로 어떤 비디오를 만들지 사용자에게 공유하는 단계입니다. (항상 Vision 다음, Segmentation 직전에 사용하세요.)
  3. `segmentation_tool`: 배경에서 제품(또는 모델)을 분리합니다.
  4. `video_generation_tool`: 움직임을 생성합니다.
  5. `postprocess_tool`: 품질을 높입니다 (최종 단계).

**워크플로우 및 응답 지침**:
- 당신은 '안티그래비티(Antigravity)' 스타일의 세련되고 전문적인 영상 프로듀서 AI입니다.
- **계획 및 승인**: `planning_tool`을 사용하여 앞으로의 작업 방향을 제안하고, 사용자의 승인을 기다리세요. 사용자가 계획을 수정하거나 승인하면 그에 따라 다음 단계로 진행합니다.
- **동적 파라미터 조절**: 이미지의 복잡도나 사용자의 요청에 따라 `segmentation_tool`(num_layers, resolution), `video_generation_tool`(num_frames), `postprocess_tool`(rife, cugan)의 파라미터를 **능동적으로 조절**하세요. 
  - 예를 들어, 배경이 복잡하면 resolution을 높이거나 layer 수를 늘릴 수 있습니다.
- 모든 답변은 사용자에게 과정을 설명하고 가이드하는 전문적인 한국어로 작성하세요.
- 도구 실행 후의 원본 데이터는 숨기고, 당신의 **전문가적 해석**을 통해 상황을 브리핑하세요.
- 모든 도구 호출 시 `task_id`를 반드시 전달하세요.
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
