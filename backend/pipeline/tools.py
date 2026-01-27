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
        config, _, _, vram_mgr = _get_tool_dependencies(task_id)
        vram_mgr.cleanup() # Ensure fresh start
        executor = Step1Segmentation(vram_mgr)
        
        result = executor.execute(
            task_id=task_id,
            image_paths=[image_path],
            config={"segmentation": {"num_layers": num_layers, "resolution": resolution}}
        )
        
        # Convert paths to web paths for frontend
        result["segmented_layers"] = [task_paths.to_web_path(p) for p in result["segmented_layers"]]
        result["main_product_layer"] = task_paths.to_web_path(result["main_product_layer"])
        
        # Publish status for UI sync
        redis_mgr = RedisManager.from_env()
        redis_mgr.set_status(
            task_id=task_id,
            status="step1_completed",
            message="Segmentation finished",
            extra={"result": result}
        )
        redis_mgr.publish(f"task:{task_id}", {"type": "status", "status": "step1_completed", "data": result})
        
        return json.dumps(result)
    except Exception as e:
        logger.error(f"[Tool] segmentation_tool failed for task {task_id}: {e}")
        return json.dumps({"error": str(e)})

@tool
def video_generation_tool(task_id: str, main_product_layer: str, prompt: str, num_frames: int = 96) -> str:
    """
    Execute Step 2: Video Generation.
    Generates a video from the main product image and prompt.
    Args:
        task_id: Unique task identifier.
        main_product_layer: Path to the segmented product image.
        prompt: Description of the video to generate.
        num_frames: Number of frames to generate (default: 96).
    Returns:
        JSON string with result containing raw_video_path.
    """
    logger.info(f"[Tool] Executing video_generation_tool for task {task_id}")
    try:
        _, _, _, vram_mgr = _get_tool_dependencies(task_id)
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
        _, task_paths, _, _ = _get_tool_dependencies(task_id)
        result["raw_video_path"] = task_paths.to_web_path(result["raw_video_path"])

        # Publish status for UI sync
        redis_mgr = RedisManager.from_env()
        redis_mgr.set_status(
            task_id=task_id,
            status="step2_completed",
            message="Video generation finished",
            extra={"result": result}
        )
        redis_mgr.publish(f"task:{task_id}", {"type": "status", "status": "step2_completed", "data": result})
        
        return json.dumps(result)
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
        raw_video_path: Path to the raw generated video.
        rife_enabled: Whether to enable RIFE frame interpolation.
        cugan_enabled: Whether to enable Real-CUGAN upscaling.
    Returns:
        JSON string with result containing final_video_path and thumbnail_path.
    """
    logger.info(f"[Tool] Executing postprocess_tool for task {task_id}")
    try:
        config, _, _, vram_mgr = _get_tool_dependencies(task_id)
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
        _, task_paths, _, _ = _get_tool_dependencies(task_id)
        result["video_path"] = task_paths.to_web_path(result["video_path"])
        result["thumbnail_path"] = task_paths.to_web_path(result["thumbnail_path"])

        # Publish status for UI sync (FINAL)
        redis_mgr = RedisManager.from_env()
        redis_mgr.set_status(
            task_id=task_id,
            status="completed",
            message="Pipeline completed successfully",
            extra={"result": result}
        )
        redis_mgr.publish(f"task:{task_id}", {"type": "status", "status": "completed", "data": result})
        
        return json.dumps(result)
    except Exception as e:
        logger.error(f"[Tool] postprocess_tool failed for task {task_id}: {e}")
        return json.dumps({"error": str(e)})


@tool
def reflection_tool(task_id: str, step_name: str, result_summary: str, user_prompt: Optional[str] = None) -> str:
    """
    Reflect on the output of a pipeline step and decide if it meets the quality standards.
    Args:
        task_id: Unique task identifier.
        step_name: The name of the step (e.g., "step1", "step2", "step3").
        result_summary: A summary of the step's results.
        user_prompt: The original user prompt or goal.
    Returns:
        JSON string with decision (proceed/retry/fail) and reflection text.
    """
    logger.info(f"[Tool] Executing reflection_tool for {step_name}")
    
    # Setup Streaming Callback
    redis_mgr = RedisManager.from_env()
    callback = RedisStreamingCallback(redis_mgr, task_id)
    
    # Use GPT-4o with timeout & streaming
    llm = ChatOpenAI(
        model="gpt-4o", 
        temperature=0, 
        request_timeout=60,
        streaming=True,
        callbacks=[callback]
    )
    
    prompt = f"""
    You are a Supervisor Agent overseeing a video generation pipeline.
    Analyze the following result for '{step_name}':
    
    Result Summary: {result_summary}
    User Goal: {user_prompt or 'Create a high-quality product video'}
    
    Decide if the step was successful. Return a JSON object:
    - decision: "proceed", "retry", or "fail"
    - reflection: Your detailed analysis of the result.
    - next_step: The name of the next step to execute (or "end").
    - config_patch: (Optional) A dictionary of settings to update if retrying or proceeding.
    
    ONLY return the JSON object.
    """
    
    response = llm.invoke(prompt)
    content = response.content.strip()
    
    # Use robust shared utility
    from common.utils import extract_json_from_text
    result = extract_json_from_text(content)
    
    if not result:
        logger.error(f"[Tool] Failed to parse JSON from reflection tool. Raw content: {content}")
        # Default fail-safe response
        result = {
            "decision": "proceed",
            "reflection": "Failed to parse reflection, proceeding with caution.",
            "next_step": "end"
        }
    
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
    Formulate a step-by-step execution plan for the video generation task.
    This should be used after vision analysis to define the pipeline strategy.
    Args:
        task_id: Unique task identifier.
        plan_steps: A list of descriptive steps the agent will take (e.g., ["Segment the watch face", "Generate rotating motion", "Upscale to 4K"]).
        rationale: Brief explanation of why this plan was chosen.
    Returns:
        JSON string confirming the plan has been recorded.
    """
    logger.info(f"[Tool] Executing planning_tool for task {task_id}")
    try:
        from common.redis_manager import RedisManager
        redis_mgr = RedisManager.from_env()
        plan_data = {
            "steps": plan_steps,
            "rationale": rationale,
            "timestamp": datetime.now().isoformat()
        }
        
        # Publish to Redis so UI can render a "Plan" card
        redis_mgr.publish(f"task:{task_id}", {
            "type": "status", 
            "status": "planning_completed", 
            "data": plan_data
        })
        
        # Also set status in Redis for persistence
        redis_mgr.set_status(
            task_id=task_id,
            status="planning_completed",
            message="Strategic plan formulated",
            extra={"result": plan_data}
        )
        
        return json.dumps({"status": "plan_recorded", "plan": plan_data})
    except Exception as e:
        logger.error(f"[Tool] planning_tool failed: {e}")
        return json.dumps({"error": str(e)})


