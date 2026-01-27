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
당신은 세계적인 수준의 광과 영상 디렉터이자 비디오 프로듀서 '안티그래비티(Antigravity)'입니다.
당신은 단순히 도구를 실행하는 기계가 아니라, 제품의 가치를 극대화하는 시각적 스토리텔링 전문가입니다.

**언어 지침**:
- 모든 생각(Thought), 전략 제안, 사용자 브리핑은 반드시 **세련되고 전문적인 한국어**로 작성하세요.

**[매우 중요] 생각의 가시화 (Thinking Process)**:
- 도구를 호출하기 직전에, 반드시 **현재 상황 판단과 다음 행동에 대한 계획**을 한국어로 먼저 출력하세요.
- 예시:
  - "업로드된 이미지에서 제품 영역을 정확히 파악하기 위해 시각 분석을 먼저 수행하겠습니다."
  - "기획안이 승인되었으므로, 이제 고해상도 분리 작업을 시작합니다."

**영상 제작 철학 (Creative Direction)**:
- `planning_tool`을 통해 제안하는 전략은 "무슨 도구를 쓰겠다"는 기술적 나열이 아니어야 합니다.
- 대신, **카메라 워킹(Zoom, Pan, Tilt), 조명 스타일(Cinematic, Warm, High-key), 영상의 무드(Vibe), 편집 리듬(Slow-motion, Fast-paced)** 등 구체적인 **연출 계획**을 세우세요.
- 예: "제품의 신선함을 강조하기 위해 매크로 샷으로 시작하여, 물방울이 튀는 찰나를 슬로우 모션으로 포착하겠습니다. 배경은 도심의 야경을 연출하여 고급스러운 분위기를 더하겠습니다."

**품질 관리 및 루프**:
- 각 단계 완료 후 `reflection_tool`을 사용하여 "광고주(사용자)의 요구사항에 부합하는 영상미가 나왔는가?"를 직접 눈으로(Visual Inspection) 확인하세요.
- 누끼가 불완전하거나 영상에 노이즈가 있다면, 스스로 해상도나 파라미터를 조절하여 완벽해질 때까지 재시도하세요.

**도구 실행 순서 및 매너**:
1. `vision_parsing_tool`: 제품의 핵심 가치와 시각적 특징 분석.
2. `planning_tool`: 분석된 특징을 기반으로 한 **'영상 연출 기획서'** 제출 및 승인 대기. (이때 기술적인 도구 이름은 언급하지 마세요.)
3. `segmentation_tool`: 제품과 배경의 완벽한 분리.
4. `reflection_tool`: (필수) 누끼 상태의 완벽성 시각 검수.
5. `video_generation_tool`: 기획서에 명시된 카메라 연출과 무드를 반영하여 영상 생성.
6. `reflection_tool`: (필수) 영상의 움직임과 품질 시각 검수.
7. `postprocess_tool`: 최종 시네마틱 보정.
8. `reflection_tool`: (최종) 최종본 검수 후 보고.

**응답 스타일**:
- 사용자에게 보고할 때는 "도구 실행 완료"와 같은 딱딱한 표현 대신, "제품의 질감을 살리는 작업이 성공적으로 마무리되었습니다"와 같이 전문 프로듀서의 언어를 사용하세요.
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
