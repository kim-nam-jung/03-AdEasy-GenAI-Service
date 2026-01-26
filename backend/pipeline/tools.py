import os
import base64
import json
import logging
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from common.config import settings, Config
from common.paths import TaskPaths
from common.logger import TaskLogger
from pipeline.vram_manager import VRAMManager
from pipeline.step3_postprocess import Step3Postprocess

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
        
        # Use GPT-4o for vision with timeout
        llm = ChatOpenAI(model="gpt-4o", max_tokens=1000, request_timeout=60)
        
        prompt = """
        You are an expert product analyst for an ad-tech video generation pipeline.
        Analyze the provided image and return a JSON object with the following fields:
        - product_type: Short name of the product (e.g., "Sneakers", "Watch")
        - description: Detailed visual description of the product.
        - material: Key materials identified (e.g., "Leather", "Glass", "Stainless Steel")
        - segmentation_hint: Advice for background removal (e.g., "Complex edges, use high resolution", "Simple background")
        - suggested_video_prompt: A high-quality prompt for generating a promotional video for this product (e.g., "Cinematic lighting, 360 rotation, soft shadows")
        
        ONLY return the JSON object, no other text.
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
        
        # Robust JSON extraction
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()
            
        result = json.loads(json_str)
        content = json.dumps(result) # Canonical JSON string
        
        # Publish status for UI sync
        redis_mgr = RedisManager.from_env()
        redis_mgr.set_status(
            task_id=task_id,
            status="vision_completed",
            message="Vision analysis finished",
            extra={"result": result}
        )
        redis_mgr.publish(f"task:{task_id}", {"type": "status", "status": "vision_completed", "data": result})

        return content

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
        executor = Step1Segmentation(vram_mgr)
        
        result = executor.execute(
            task_id=task_id,
            image_paths=[image_path],
            config={"segmentation": {"num_layers": num_layers, "resolution": resolution}}
        )
        
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
        executor = Step2VideoGeneration(vram_mgr)
        
        result = executor.execute(
            task_id=task_id,
            main_product_layer=main_product_layer,
            user_prompt=prompt,
            config={"video_generation": {"num_frames": num_frames}}
        )

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
def reflection_tool(step_name: str, result_summary: str, user_prompt: Optional[str] = None) -> str:
    """
    Reflect on the output of a pipeline step and decide if it meets the quality standards.
    Args:
        step_name: The name of the step (e.g., "step1", "step2", "step3").
        result_summary: A summary of the step's results.
        user_prompt: The original user prompt or goal.
    Returns:
        JSON string with decision (proceed/retry/fail) and reflection text.
    """
    logger.info(f"[Tool] Executing reflection_tool for {step_name}")
    
    # Use GPT-4o with timeout
    llm = ChatOpenAI(model="gpt-4o", temperature=0, request_timeout=60)
    
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
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    
    return content

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

