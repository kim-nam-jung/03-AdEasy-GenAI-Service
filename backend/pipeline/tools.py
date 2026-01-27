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
def segmentation_tool(task_id: str, image_path: str, num_layers: int = 4, resolution: int = 640) -> str:
    """
    Execute Step 1: Image Segmentation.
    Extracts layers from the input image.
    Args:
        task_id: Unique task identifier.
        image_path: Path to the input image.
        num_layers: Number of layers to extract (default: 4).
        resolution: Processing resolution (default: 640).
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

        result = executor.execute(
            task_id=task_id,
            image_paths=[image_path],
            config={"segmentation": {"num_layers": num_layers, "resolution": resolution}}
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
        
        result = executor.execute(
            task_id=task_id,
            main_product_layer=main_product_layer,
            user_prompt=prompt,
            config={"video_generation": {"num_frames": num_frames}}
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
    
    # Setup Streaming Callback
    redis_mgr = RedisManager.from_env()
    callback = RedisStreamingCallback(redis_mgr, task_id)
    
    # Use GPT-4o with Vision
    llm = ChatOpenAI(
        model="gpt-4o", 
        temperature=0, 
        max_tokens=500,
        request_timeout=60,
        streaming=True,
        callbacks=[callback]
    )
    
    content = [
        {"type": "text", "text": f"""
        당신은 영상 제작 파이프라인의 최고 품질 관리 감독관(QC)입니다.
        '{step_name}' 단계의 결과물이 다음 기준을 충족하는지 엄격하게 검수하세요.
        
        결과 요약: {result_summary}
        사용자 목표: {user_prompt or '고품질 영상 제작'}
        
        **이미지를 제공한 경우 시각적 검수 지침**:
        1. Segmentation 단계라면: 제품(햄버거, 가방 등)이 온전하게 분리되었는가? 잘린 부분이 없는가? 배경이 섞이지 않았는가?
        2. Video 단계라면: 물체가 자연스럽게 움직이는가? 시각적 붕괴(artifact)가 없는가?
        
        **결정 지침**:
        - 품질이 미흡하면 무조건 "retry"를 선택하고, 구체적인 해결책(예: 'resolution을 1024로 높이세요')을 config_patch에 제안하세요.
        - 완벽하면 "proceed"를 선택하세요.
        - 기술적 한계로 도저히 불가능하면 "fail"을 선택하세요.
        
        JSON 형식으로만 응답하세요:
        {{
          "decision": "proceed" | "retry" | "fail",
          "reflection": "한국어로 작성된 상세한 검수 의견",
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
    
    # Explicitly pass callbacks to invoke to guarantee streaming
    response = llm.invoke([HumanMessage(content=content)], config={"callbacks": [callback]})
    raw_content = response.content.strip()
    
    from common.utils import extract_json_from_text
    result = extract_json_from_text(raw_content)
    
    if not result:
        result = {"decision": "proceed", "reflection": "검수 도구 오류로 일단 진행합니다."}
    
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


