import os
import json
import logging
from typing import Optional
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from common.redis_manager import RedisManager
from common.utils import extract_json_from_text
from pipeline.tools.common import encode_image

logger = logging.getLogger(__name__)

@tool
def reflection_tool(task_id: str, step_name: str, result_summary: str, image_path: Optional[str] = None, user_prompt: Optional[str] = None) -> str:
    """
    Reflect on the output of a pipeline step and decide if it meets the quality standards.
    If image_path is provided, it will visually analyze the result using GPT-4 Vision.
    It manages retry counts and persists configuration overrides to Redis if improvements are needed.
    
    Args:
        task_id: Unique task identifier.
        step_name: The name of the step (e.g., "segmentation", "video_gen").
        result_summary: A summary of the step's results.
        image_path: (Optional) Path to the result image or frame to visually inspect.
        user_prompt: The original user prompt or goal.
    Returns:
        JSON string with decision (proceed/retry/fail) and reflection text.
    """
    logger.info(f"[Tool] Executing vision-based reflection for {step_name}")

    # Setup Redis
    redis_mgr = RedisManager.from_env()

    # --- RETRY & HISTORY LOGIC ---
    redis_key = f"retry_count:{task_id}:{step_name}"
    history_key = f"retry_history:{task_id}:{step_name}"  
    current_retry = 0
    attempted_configs = []

    try:
        val = redis_mgr.client.get(redis_key)
        if val:
            current_retry = int(val)

        # Load previously attempted configurations from Redis List
        history_raw = redis_mgr.client.lrange(history_key, 0, -1)
        if history_raw:
            attempted_configs = [json.loads(h) for h in history_raw]
    except Exception as e:
        logger.warning(f"Failed to load retry history: {e}")

    logger.info(f"Reflection Tool: {step_name} (Current Retry: {current_retry}, Previous attempts: {len(attempted_configs)})")

    # Build history context string for the prompt
    history_context = ""
    if attempted_configs:
        history_lines = []
        for i, cfg in enumerate(attempted_configs, 1):
            history_lines.append(f"  {i}회차: {json.dumps(cfg, ensure_ascii=False)}")
        history_context = f"""
        **[이전 시도 내역 - 반드시 전과 다른 전략을 사용해야 함]**:
{chr(10).join(history_lines)}

        ⚠️ **위의 설정들은 이미 실패했습니다. 동일하거나 유사한 설정(ex: 해상도만 미세하게 변경)은 금지입니다!**
        """

    # Dynamic instruction based on retry count
    retry_context = ""
    if current_retry >= 2:
        # Third failure: Force Fail
        retry_context = """
        - **[CRITICAL]**: 이미 2회 이상 재시도했으나 실패했습니다. 더 이상의 자동 수정은 무의미합니다.
        - **무조건 `decision: "fail"`을 선택하고, reflection에 "Human Intervention Required"를 적으세요.**
        """
    elif current_retry == 1:
        # Second retry: Force different strategy logic
        
        # Heuristic: Check if previous attempt only changed resolution
        only_resolution_changed = False
        if attempted_configs:
            last_attempt = attempted_configs[-1]
            # Assumes patch structure: {"segmentation": {"resolution": ...}}
            seg_cfg = last_attempt.get("segmentation", {})
            if seg_cfg and "resolution" in seg_cfg and "prompt_mode" not in seg_cfg:
                only_resolution_changed = True

        if only_resolution_changed:
            retry_context = f"""
            - 현재 **2번째 수정 시도**입니다.

            **[강제 지시]**: 이전 시도에서 해상도만 변경했으나 실패했습니다.
            - **반드시 `prompt_mode: "grid"`를 config_patch에 포함하세요!**
            - 해상도 변경만으로는 잘림 문제가 해결되지 않습니다. Grid 모드는 여러 포인트를 사용하여 객체 전체를 커버합니다.

            {history_context}

            **config_patch 필수 형식**:
            {{"segmentation": {{"prompt_mode": "grid", "resolution": 1024}}}}
            """
        else:
            retry_context = f"""
            - 현재 **2번째 수정 시도**입니다. 이전과 완전히 다른 접근이 필요합니다.

            {history_context}

            **[가용 파라미터 도구함]**:
            - `prompt_mode`: `"grid"` 사용 권장 (잘림 문제 해결)
            - `resolution`: `1024` ~ `2048`
            - `num_layers`: `6` ~ `10`
            """
    else:
        # First retry (current_retry == 0): Provide Toolbox
        retry_context = f"""
        - 현재 **1번째 수정 시도**입니다.

        {history_context}

        **[가용 파라미터 도구함 (Parameter Toolbox)]**:
        문제를 해결하기 위해 아래 파라미터들을 조합하여 `config_patch`를 만드세요.

        **1. Segmentation (잘림, 파먹음, 배경 잔여물)**
        - `prompt_mode`:
          - `"center"` (기본값): 중앙에 있는 물체 하나만 따냄.
          - `"grid"` (**강력 권장**): **물체의 일부가 잘려 나갈 때 필수.** 여러 지점을 찍어 전체를 커버함.
        - `resolution`: `640` (기본) ~ `2048`. 해상도를 높이면 디테일이 살아남.
        - `num_layers`: `4` (기본) ~ `10`. 레이어가 많으면 더 정교하게 분리될 수 있음.

        **2. Video Generation (무너짐, 기괴함)**
        - `num_frames`: `96` (기본) ~ `255`. 프레임을 늘리면 더 부드러워질 수 있음.

        **[중요 판단 가이드]**:
        - ⚠️ **해상도만 높이는 것은 대부분 효과가 없습니다!**
        - **잘림(Clipping)** 현상 → `prompt_mode: "grid"` 필수
        - 해상도 변경은 부가적인 옵션일 뿐, 핵심 해결책이 아닙니다.
        """
    
    # Use GPT-4o with Vision
    llm = ChatOpenAI(
        model="gpt-4o", 
        temperature=0.2, 
        max_tokens=500,
        request_timeout=60,
        streaming=True
    )
    
    content = [
        {"type": "text", "text": f"""
        당신은 영상 제작 파이프라인의 **'악독하고 까다로운' 품질 관리자(QC)**입니다.
        현재 '{step_name}' 단계의 결과물을 검수 중입니다.
        
        결과 요약: {result_summary}
        사용자 목표: {user_prompt or '고품질 영상 제작'}
        
        **[안전 지침]**:
        본 이미지는 상업용 음식/상품 사진입니다. 순수한 품질 관리 관점에서 분석하세요.

        **[불량 기준]**:
        1. Segmentation: 잘림(Clipping), 파먹음(Missing), 배경 잔여물 -> 즉시 RETRY
        2. Video Generation: 무너짐, 괴기한 변형 -> 즉시 RETRY
        
        **[처방 지침]**:
        {retry_context}
        
        JSON 형식으로만 응답하세요:
        {{
          "decision": "proceed" | "retry" | "fail",
          "reflection": "불량 원인 분석 및 선택한 파라미터에 대한 근거",
          "config_patch": {{ "key": "value" }}
        }}
        """}
    ]
    if image_path and os.path.exists(image_path):
        base64_image = encode_image(image_path)
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            # Note: encode_image replaces transparent background with Magenta to highlight clipping
        })
    
    # Direct Streaming Loop
    full_content = ""
    try:
        for chunk in llm.stream([HumanMessage(content=content)]):
            token = chunk.content
            full_content += token
            redis_mgr.publish(f"task:{task_id}", {
                "type": "token",
                "content": token
            })
    except Exception as stream_err:
        logger.error(f"Streaming failed: {stream_err}")
        result = llm.invoke([HumanMessage(content=content)])
        full_content = result.content

    raw_content = full_content.strip()
    result = extract_json_from_text(raw_content)
    
    if not result:
        result = {"decision": "proceed", "reflection": "검수 도구 오류로 일단 진행합니다."}
        
    # [LOGIC] Update Retry Count & Save Config Patch logic
    decision = result.get("decision", "proceed")
    try:
        if decision == "retry":
            redis_mgr.client.incr(redis_key)

            # --- SAVE CONFIG_PATCH TO HISTORY ---
            if "config_patch" in result and isinstance(result["config_patch"], dict):
                patch = result["config_patch"]
                logger.info(f"Reflection Tool: Applying system-level config patch: {patch}")

                # Save to history list
                redis_mgr.client.rpush(history_key, json.dumps(patch, ensure_ascii=False))
                
                # --- SUPERVISOR OVERRIDE (Core Logic) ---
                # Store in a dedicated key for task config overrides
                config_key = f"task:{task_id}:config"

                # Flatten and store: "segmentation:prompt_mode" -> "grid"
                for category, settings in patch.items():
                    if isinstance(settings, dict):
                        for key, value in settings.items():
                            redis_field = f"{category}:{key}"
                            redis_mgr.client.hset(config_key, redis_field, str(value))
                            logger.info(f"  -> Supervisor Set {redis_field} = {value}")

        elif decision in ["proceed", "fail"]:
            # On Success or Human-Handover, clear the retry context steps
            # but we KEEP the config overrides because they represent the "Winning Settings"
            redis_mgr.client.delete(redis_key)
            redis_mgr.client.delete(history_key)
            logger.info(f"Reflection Tool: Cleared retry state for {step_name}")
            
    except Exception as e:
        logger.error(f"Failed to update retry count or config: {e}")
    
    return json.dumps(result)
