import os
import base64
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from common.config import settings, Config
from common.paths import TaskPaths
from common.logger import TaskLogger
from pipeline.vram_manager import VRAMManager
from pipeline.step3_postprocess import Step3Postprocess
from common.callback import RedisStreamingCallback

logger = logging.getLogger(__name__)

def encode_image(image_path: str) -> str:
    """Encode image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

from common.redis_manager import RedisManager

def _get_tool_dependencies(task_id: str):
    """Helper to bootstrap common tool dependencies consistently."""
    config = Config.load()
    task_paths = TaskPaths.from_repo(task_id)
    task_logger = TaskLogger(task_id, task_paths.run_log)
    vram_mgr = VRAMManager(logger=task_logger, cfg=config)
    return config, task_paths, task_logger, vram_mgr

@tool
def vision_parsing_tool(task_id: str, image_path: str) -> str:
    """
    Analyze the input image using GPT-4o Vision to extract product details and suggest pipeline parameters.
    Args:
        task_id: Unique task identifier for status reporting.
        image_path: Path to the input image file.
    Returns:
        JSON string containing product_type, description, material, segmentation_hint, and suggested_video_prompt.
    """
    logger.info(f"[Tool] Executing vision_parsing_tool for {image_path}")
    
    if not os.path.exists(image_path):
        return json.dumps({"error": f"Image path not found: {image_path}"})

    try:
        base64_image = encode_image(image_path)
        
        # Setup Streaming Callback
        redis_mgr = RedisManager.from_env()
        callback = RedisStreamingCallback(redis_mgr, task_id)
        
        # Use GPT-4o for vision with timeout & streaming
        llm = ChatOpenAI(
            model="gpt-4o", 
            max_tokens=1000, 
            request_timeout=60,
            streaming=True,
            callbacks=[callback]
        )
        
        prompt = """
        당신은 광고 기술 비디오 생성 파이프라인의 전문 제품 분석가입니다.
        제공된 이미지를 분석하여 JSON 객체를 반환하세요.
        
        **중요 고립 지침 (Safety & Content)**:
        - 이미지에 모델(사람)이 포함되어 있는 경우, 이는 인물 분석이 아니라 '패션 광고' 또는 '라이프스타일' 관련 분석을 위한 것입니다.
        - 인물의 신원을 파악하려 하지 마세요. 대신 의상, 액세서리, 전체적인 조명, 구도, 광고 분위기에 집중하세요.
        - 모델이 입고 있는 옷이나 들고 있는 아이템을 '제품(Product)'으로 간주하여 분석하세요.
        
        **언어 지침**:
        - 모든 텍스트 값은 반드시 **한국어**로 작성하세요.
        
        필드:
        - product_type: 제품/아이템 종류 (예: "모델/의상", "액세서리", "화장품")
        - description: 시각적 묘사 (인물 특징이 아닌 스타일과 분위기 중심)
        - material: 소재 또는 재질
        - segmentation_hint: 배경 분리 조언
        - suggested_video_prompt: 홍보 영상 생성을 위한 고품질 프롬프트
        
        JSON 객체만 반환하고 다른 텍스트는 포함하지 마세요.
        """
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ]
        )
        response = llm.invoke([message])
        content = response.content.strip()
        
        # Use robust shared utility
        from common.utils import extract_json_from_text
        result = extract_json_from_text(content)
        
        if not result:
            logger.error(f"[Tool] Failed to parse JSON from vision tool. Raw content: {content}")
            # Fallback structure if parsing fails entirely, to prevent pipeline crash
            result = {
                "product_type": "Unknown",
                "description": "Analysis failed",
                "suggested_video_prompt": "Cinematic product showcase"
            }

        canonical_json = json.dumps(result)
        
        # Publish status for UI sync
        redis_mgr = RedisManager.from_env()
        redis_mgr.set_status(
            task_id=task_id,
            status="vision_completed",
            message="Vision analysis finished",
            extra={"result": result}
        )
        redis_mgr.publish(f"task:{task_id}", {"type": "status", "status": "vision_completed", "data": result})

        return canonical_json

    except Exception as e:
        logger.error(f"[Tool] vision_parsing_tool failed for task {task_id}: {e}")
        return json.dumps({"error": str(e)})

from pipeline.step1_segmentation import Step1Segmentation
from pipeline.step2_video_generation import Step2VideoGeneration
from pipeline.step3_postprocess import Step3Postprocess
from pipeline.vram_manager import VRAMManager
from common.logger import TaskLogger
from common.config import Config

@tool
def segmentation_tool(task_id: str, image_path: str, num_layers: int = 4, resolution: int = 640, prompt_mode: str = "center") -> str:
    """
    Execute Step 1: Image Segmentation.
    Extracts layers from the input image.
    Args:
        task_id: Unique task identifier.
        image_path: Path to the input image.
        num_layers: Number of layers to extract (default: 4).
        resolution: Processing resolution (default: 640).
        prompt_mode: Segmentation strategy ("center" or "grid"). Use "grid" for larger/complex objects.
    Returns:
        JSON string with result containing segmented_layers paths and main_product_layer path.
    """
    logger.info(f"[Tool] Executing segmentation_tool for task {task_id}")
    try:
        config, task_paths, _, vram_mgr = _get_tool_dependencies(task_id)
        vram_mgr.cleanup() # Ensure fresh start
        executor = Step1Segmentation(vram_mgr)
        
        # Ensure image_path is absolute if passed as relative
        if not os.path.isabs(image_path) and not image_path.startswith('http'):
             image_path = str(task_paths.input_dir / os.path.basename(image_path))

        # --- SUPERVISOR OVERRIDE CHECK ---
        # Check if there are any overrides from Reflection Tool in Redis
        redis_mgr = RedisManager.from_env()
        config_key = f"task:{task_id}:config"
        
        # Current args
        final_num_layers = num_layers
        final_resolution = resolution
        final_prompt_mode = prompt_mode
        
        try:
            # Check overrides
            overrides = redis_mgr.client.hgetall(config_key)
            if overrides:
                logger.info(f"Applying Supervisor Overrides for Task {task_id}: {overrides}")
                
                if "segmentation:num_layers" in overrides:
                    final_num_layers = int(overrides["segmentation:num_layers"])
                if "segmentation:resolution" in overrides:
                    final_resolution = int(overrides["segmentation:resolution"])
                if "segmentation:prompt_mode" in overrides:
                    final_prompt_mode = overrides["segmentation:prompt_mode"]
        except Exception as e:
            logger.error(f"Failed to load overrides: {e}")

        result = executor.execute(
            task_id=task_id,
            image_paths=[image_path],
            config={"segmentation": {"num_layers": final_num_layers, "resolution": final_resolution, "prompt_mode": final_prompt_mode}}
        )
        
        # Convert absolute paths to web-accessible paths for frontend
        converted_result = {
            "segmented_layers": [task_paths.to_web_path(p) for p in result.get("segmented_layers", [])],
            "main_product_layer": task_paths.to_web_path(result.get("main_product_layer", "")),
            "abs_main_product_layer": str(result.get("main_product_layer", "")) # For agent's vision tool
        }
        
        # Publish status for UI sync
        redis_mgr = RedisManager.from_env()
        redis_mgr.set_status(
            task_id=task_id,
            status="step1_completed",
            message="Segmentation finished",
            extra={"result": converted_result}
        )
        redis_mgr.publish(f"task:{task_id}", {"type": "status", "status": "step1_completed", "data": converted_result})
        
        return json.dumps(converted_result)
    except Exception as e:
        logger.error(f"[Tool] segmentation_tool failed for task {task_id}: {str(e)}")
        return json.dumps({"error": str(e), "decision": "retry"})

@tool
def video_generation_tool(task_id: str, main_product_layer: str, prompt: str, num_frames: int = 96) -> str:
    """
    Execute Step 2: Video Generation.
    Generates a video from the main product image and prompt.
    Args:
        task_id: Unique task identifier.
        main_product_layer: Path to the segmented product image (Web path or Abs path).
        prompt: Description of the video to generate.
        num_frames: Number of frames to generate (default: 96).
    Returns:
        JSON string with result containing raw_video_path.
    """
    logger.info(f"[Tool] Executing video_generation_tool for task {task_id}")
    try:
        # Resolve path if web path is passed
        _, task_paths, _, vram_mgr = _get_tool_dependencies(task_id)
        if "/outputs/" in main_product_layer:
             main_product_layer = str(task_paths.outputs_task_dir / os.path.basename(main_product_layer))

        vram_mgr.unload_all() # Clear Step 1 models
        vram_mgr.cleanup()
        executor = Step2VideoGeneration(vram_mgr)
        
        # --- SUPERVISOR OVERRIDE CHECK ---
        redis_mgr = RedisManager.from_env()
        config_key = f"task:{task_id}:config"
        final_num_frames = num_frames
        
        try:
             overrides = redis_mgr.client.hgetall(config_key)
             if overrides and "video_generation:num_frames" in overrides:
                 final_num_frames = int(overrides["video_generation:num_frames"])
                 logger.info(f"Overriding num_frames to {final_num_frames}")
        except Exception:
            pass

        result = executor.execute(
            task_id=task_id,
            main_product_layer=main_product_layer,
            user_prompt=prompt,
            config={"video_generation": {"num_frames": final_num_frames}}
        )

        # Convert paths to web paths
        converted_result = {
            "raw_video_path": task_paths.to_web_path(result["raw_video_path"]),
            "abs_raw_video_path": str(result["raw_video_path"]) # For agent's vision tool
        }

        # Publish status for UI sync
        redis_mgr = RedisManager.from_env()
        redis_mgr.set_status(
            task_id=task_id,
            status="step2_completed",
            message="Video generation finished",
            extra={"result": converted_result}
        )
        redis_mgr.publish(f"task:{task_id}", {"type": "status", "status": "step2_completed", "data": converted_result})
        
        return json.dumps(converted_result)
    except Exception as e:
        logger.error(f"[Tool] video_generation_tool failed for task {task_id}: {e}")
        return json.dumps({"error": str(e)})

@tool
def postprocess_tool(task_id: str, raw_video_path: str, rife_enabled: bool = True, cugan_enabled: bool = True) -> str:
    """
    Execute Step 3: Post-processing.
    Enhances the raw video with frame interpolation and upscaling.
    Args:
        task_id: Unique task identifier.
        raw_video_path: Path to the raw generated video (Web path or Abs path).
        rife_enabled: Whether to enable RIFE frame interpolation.
        cugan_enabled: Whether to enable Real-CUGAN upscaling.
    Returns:
        JSON string with result containing final_video_path and thumbnail_path.
    """
    logger.info(f"[Tool] Executing postprocess_tool for task {task_id}")
    try:
        config, task_paths, _, vram_mgr = _get_tool_dependencies(task_id)
        
        # Resolve path if web path is passed
        if "/outputs/" in raw_video_path:
             raw_video_path = str(task_paths.outputs_task_dir / os.path.basename(raw_video_path))

        vram_mgr.unload_all() # Clear Step 2 models
        vram_mgr.cleanup()
        executor = Step3Postprocess(vram_mgr)
        
        # Override config based on tool inputs
        config_dict = config.get()
        if "postprocess" not in config_dict:
            config_dict["postprocess"] = {}
        config_dict["postprocess"]["rife"] = {"enabled": rife_enabled}
        config_dict["postprocess"]["real_cugan"] = {"enabled": cugan_enabled}
        
        result = executor.execute(
            task_id=task_id,
            raw_video_path=raw_video_path,
            config=config_dict
        )

        # Convert paths to web paths
        converted_result = {
            "video_path": task_paths.to_web_path(result["video_path"]),
            "thumbnail_path": task_paths.to_web_path(result["thumbnail_path"]),
            "abs_video_path": str(result["video_path"])
        }

        # Publish status for UI sync (FINAL)
        redis_mgr = RedisManager.from_env()
        redis_mgr.set_status(
            task_id=task_id,
            status="completed",
            message="Pipeline completed successfully",
            extra={"result": converted_result}
        )
        redis_mgr.publish(f"task:{task_id}", {"type": "status", "status": "completed", "data": converted_result})
        
        return json.dumps(converted_result)
    except Exception as e:
        logger.error(f"[Tool] postprocess_tool failed for task {task_id}: {e}")
        return json.dumps({"error": str(e)})


@tool
def reflection_tool(task_id: str, step_name: str, result_summary: str, image_path: Optional[str] = None, user_prompt: Optional[str] = None) -> str:
    """
    Reflect on the output of a pipeline step and decide if it meets the quality standards.
    If image_path is provided, it will visually analyze the result.
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

    # --- RETRY COUNT LOGIC ---
    redis_key = f"retry_count:{task_id}:{step_name}"
    history_key = f"retry_history:{task_id}:{step_name}"  # NEW: Track attempted configs
    current_retry = 0
    attempted_configs = []

    try:
        val = redis_mgr.client.get(redis_key)
        if val:
            current_retry = int(val)

        # Load previously attempted configurations
        history_raw = redis_mgr.client.lrange(history_key, 0, -1)
        if history_raw:
            attempted_configs = [json.loads(h) for h in history_raw]
    except Exception as e:
        logger.warning(f"Failed to load retry history: {e}")

    logger.info(f"Reflection Tool: {step_name} (Current Retry: {current_retry}, Previous attempts: {len(attempted_configs)})")

    # Build history context for prompt
    history_context = ""
    if attempted_configs:
        history_lines = []
        for i, cfg in enumerate(attempted_configs, 1):
            history_lines.append(f"  {i}회차: {json.dumps(cfg, ensure_ascii=False)}")
        history_context = f"""
        **[이전 시도 내역 - 반드시 다른 전략 사용!]**:
{chr(10).join(history_lines)}

        ⚠️ **위의 설정들은 이미 실패했습니다. 동일하거나 유사한 설정(해상도만 변경 등)은 금지입니다!**
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
        # Second retry: Force different strategy
        # Check if previous attempt only changed resolution
        only_resolution_changed = False
        if attempted_configs:
            last_attempt = attempted_configs[-1]
            seg_cfg = last_attempt.get("segmentation", {})
            if seg_cfg and "resolution" in seg_cfg and "prompt_mode" not in seg_cfg:
                only_resolution_changed = True

        if only_resolution_changed:
            retry_context = f"""
            - 현재 **2번째 수정 시도**입니다.

            **[강제 지시]**: 이전 시도에서 해상도만 변경했으나 실패했습니다.
            - **반드시 `prompt_mode: "grid"`를 config_patch에 포함하세요!**
            - 해상도 변경만으로는 잘림 문제가 해결되지 않습니다.

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
        # First retry: Provide Toolbox
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
        temperature=0.2, # Slightly creative for problem solving
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
          "reflection": "불량 원인 분석 및 선택한 파라미터에 대한 근거 (예: '윗부분이 잘렸으므로 grid 모드를 사용해 전체 영역을 잡겠습니다.')",
          "config_patch": {{ "key": "value" }}
        }}
        """}
    ]
    if image_path and os.path.exists(image_path):
        base64_image = encode_image(image_path)
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
        })
    
    # Direct Streaming Loop (Bypassing Callbacks for reliability)
    full_content = ""
    try:
        for chunk in llm.stream([HumanMessage(content=content)]):
            token = chunk.content
            full_content += token
            # Direct publish to Redis
            redis_mgr.publish(f"task:{task_id}", {
                "type": "token",
                "content": token
            })
    except Exception as stream_err:
        logger.error(f"Streaming failed: {stream_err}")
        # Fallback to non-streaming if stream fails
        result = llm.invoke([HumanMessage(content=content)])
        full_content = result.content

    raw_content = full_content.strip()
    
    from common.utils import extract_json_from_text
    result = extract_json_from_text(raw_content)
    
    if not result:
        result = {"decision": "proceed", "reflection": "검수 도구 오류로 일단 진행합니다."}
        
    # Update Retry Count based on decision
    decision = result.get("decision", "proceed")
    try:
        if decision == "retry":
            redis_mgr.client.incr(redis_key)

            # --- SAVE CONFIG_PATCH TO HISTORY ---
            if "config_patch" in result and isinstance(result["config_patch"], dict):
                patch = result["config_patch"]
                logger.info(f"Reflection Tool: Applying system-level config patch: {patch}")

                # Save to history list for future reference (prevent same strategy)
                redis_mgr.client.rpush(history_key, json.dumps(patch, ensure_ascii=False))
                logger.info(f"  -> Saved to retry history: {history_key}")

                # --- SUPERVISOR OVERRIDE ---
                # Store in a dedicated key for task config overrides
                config_key = f"task:{task_id}:config"

                # Flatten and store: segmentation:prompt_mode -> value
                for category, settings in patch.items():
                    if isinstance(settings, dict):
                        for key, value in settings.items():
                            redis_field = f"{category}:{key}"
                            redis_mgr.client.hset(config_key, redis_field, str(value))
                            logger.info(f"  -> Set {redis_field} = {value}")

        elif decision in ["proceed", "fail"]:
            # Reset retry count and history on success or fail
            redis_mgr.client.delete(redis_key)
            redis_mgr.client.delete(history_key)
            logger.info(f"Reflection Tool: Cleared retry state for {step_name}")

    except Exception as e:
        logger.error(f"Failed to update retry count or config: {e}")
    
    return json.dumps(result)

@tool
def ask_human_tool(task_id: str, question: str, context: Optional[str] = None) -> str:
    """
    Request human feedback when the agent is unsure or stuck.
    This will pause the pipeline until a user provides input.
    Args:
        task_id: Unique task identifier.
        question: The question to ask the user.
        context: Additional context about the failure or situation.
    Returns:
        A formatted string indicating the request has been sent.
    """
    logger.info(f"[Tool] Executing ask_human_tool for task {task_id}")
    try:
        from common.redis_manager import RedisManager
        # Publish event to Redis so Frontend can show a prompt
        manager = RedisManager.from_env()
        payload = {
            "type": "human_input_request",
            "task_id": task_id,
            "question": question,
            "context": context
        }
        manager.publish(f"task:{task_id}", payload) 
        
        return f"REQUEST_SENT: {question}"
    except Exception as e:
        logger.error(f"[Tool] ask_human_tool failed for task {task_id}: {e}")
        return json.dumps({"error": str(e)})


@tool
def planning_tool(task_id: str, plan_steps: List[str], rationale: str) -> str:
    """
    Formulate a step-by-step execution plan and wait for user confirmation.
    This MUST be used after vision analysis to define the pipeline strategy and get user approval.
    Args:
        task_id: Unique task identifier.
        plan_steps: A list of descriptive steps the agent will take.
        rationale: Brief explanation of why this plan was chosen.
    Returns:
        The user's feedback or 'Approved' string.
    """
    logger.info(f"[Tool] Proposing plan for task {task_id} and waiting for approval")
    import time
    try:
        from common.redis_manager import RedisManager
        redis_mgr = RedisManager.from_env()
        plan_data = {
            "steps": plan_steps,
            "rationale": rationale,
            "timestamp": datetime.now().isoformat()
        }
        
        # 1. Publish to Redis so UI can render the plan with an "Approve" button
        redis_mgr.publish(f"task:{task_id}", {
            "type": "status", 
            "status": "planning_proposed", 
            "data": plan_data
        })
        
        # 2. Record status for persistence
        redis_mgr.set_status(
            task_id=task_id,
            status="planning_proposed",
            message="Plan proposed, waiting for user approval",
            extra={"plan": plan_data}
        )
        
        # 3. BLOCKING WAIT for human feedback
        # The frontend will hit POST /tasks/{task_id}/feedback
        # which sets the status to 'feedback_received'
        
        logger.info(f"[Tool] Plan sent. Entering wait loop for task {task_id}...")
        
        start_time = time.time()
        timeout = 300 # 5 minutes
        
        while time.time() - start_time < timeout:
            status_data = redis_mgr.get_status(task_id)
            if status_data and status_data.get("status") == "feedback_received":
                feedback = status_data.get("extra", {}).get("user_feedback", "Approved")
                logger.info(f"[Tool] Feedback received: {feedback}")
                
                # Signal resume in UI
                redis_mgr.publish(f"task:{task_id}", {
                    "type": "human_input_received",
                    "feedback": feedback
                })
                
                return f"User Response: {feedback}"
            
            time.sleep(2) # Poll Redis every 2 seconds
            
        return "ERROR: User did not respond to the plan within the timeout."

    except Exception as e:
        logger.error(f"[Tool] planning_tool failed: {e}")
        return json.dumps({"error": str(e)})


