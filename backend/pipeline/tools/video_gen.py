import os
import json
import logging
from langchain_core.tools import tool
from common.config import Config
from common.paths import TaskPaths
from common.logger import TaskLogger
from common.redis_manager import RedisManager
from pipeline.vram_manager import VRAMManager
from pipeline.step2_video_generation import Step2VideoGeneration
from pipeline.step3_postprocess import Step3Postprocess
from pipeline.tools.decorators import use_supervisor_config

logger = logging.getLogger(__name__)

def _get_tool_dependencies(task_id: str):
    config = Config.load()
    task_paths = TaskPaths.from_repo(task_id)
    task_logger = TaskLogger(task_id, task_paths.run_log)
    vram_mgr = VRAMManager(logger=task_logger, cfg=config)
    return config, task_paths, task_logger, vram_mgr

@tool
@use_supervisor_config
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
        
        # Note: @use_supervisor_config checks 'video_generation:num_frames' in Redis and overrides kwargs['num_frames']
        
        result = executor.execute(
            task_id=task_id,
            main_product_layer=main_product_layer,
            user_prompt=prompt,
            config={"video_generation": {"num_frames": num_frames}}
        )

        # Convert paths to web paths
        converted_result = {
            "raw_video_path": task_paths.to_web_path(result["raw_video_path"]),
            "abs_raw_video_path": str(result["raw_video_path"]), # For agent's vision tool
            "_instruction": "Video generated. execute 'reflection_tool' to verify motion quality."
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
@use_supervisor_config
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
