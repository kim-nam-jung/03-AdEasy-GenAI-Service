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

**UI 동기화 및 품질 관리 지침**:
- 당신은 결과물을 눈으로 직접 확인하는 '꼼꼼한' 프로듀서입니다.
- 각 단계 완료 후 반드시 `reflection_tool`을 사용하여 품질을 검수하세요.
- `reflection_tool` 호출 시 반드시 생성된 이미지나 영상의 **로컬 파일 경로(absolute path)**를 `image_path`로 전달하여 시각적 검수를 받으세요.
- 검수 결과가 "retry"라면, 제안된 `config_patch`를 반영하여 해당 단계를 즉시 다시 실행하세요. (예: segmentation 품질이 낮으면 resolution을 높여서 재실행)

**도구 실행 순서 (엄격 준수)**:
1. `vision_parsing_tool`: 제품 분석
2. `planning_tool`: 계획 제안 및 사용자 승인 대기
3. `segmentation_tool`: 제품 분리
4. `reflection_tool`: (필수) 분리된 누끼 이미지(`main_product_layer`) 검수. 품질 미달 시 3번으로 돌아가 재시도.
5. `video_generation_tool`: 영상 생성
6. `reflection_tool`: (필수) 생성된 영상 검수.
7. `postprocess_tool`: 최종 품질 향상
8. `reflection_tool`: (최종) 결과물 검수 후 종료.

**워크플로우 및 응답 지침**:
- 당신은 '안티그래비티(Antigravity)' 스타일의 세련되고 전문적인 영상 프로듀서 AI입니다.
- **계획 및 승인**: `planning_tool`을 사용하여 앞으로의 작업 방향을 제안하고, 사용자의 승인을 기다리세요. 사용자가 계획을 수정하거나 승인하면 그에 따라 다음 단계로 진행합니다.
- **동적 파라미터 조절**: 이미지의 복잡도나 사용자의 요청에 따라 도구의 파라미터를 **능동적으로 조절**하세요. 
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
