import os
import json
import logging
from langchain_core.tools import tool
from common.config import Config
from common.paths import TaskPaths
from common.logger import TaskLogger
from common.redis_manager import RedisManager
from pipeline.vram_manager import VRAMManager
from pipeline.step1_segmentation import Step1Segmentation
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
def segmentation_tool(task_id: str, image_path: str, num_layers: int = 4, resolution: int = 640, prompt_mode: str = "center") -> str:
    """
    Execute Step 1: Image Segmentation.
    Extracts layers from the input image.
    Args:
        task_id: Unique task identifier.
        image_path: Path to the input image.
        num_layers: Number of layers to extract (default: 4).
        resolution: Processing resolution (default: 640).
        prompt_mode: Segmentation strategy ("center" or "grid"). Use "grid" for complex objects.
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

        # Note: @use_supervisor_config handles the override logic automatically now!
        
        result = executor.execute(
            task_id=task_id,
            image_paths=[image_path],
            config={"segmentation": {"num_layers": num_layers, "resolution": resolution, "prompt_mode": prompt_mode}}
        )
        
        # Convert absolute paths to web-accessible paths for frontend
        converted_result = {
            "segmented_layers": [task_paths.to_web_path(p) for p in result.get("segmented_layers", [])],
            "main_product_layer": task_paths.to_web_path(result.get("main_product_layer", "")),
            "abs_main_product_layer": str(result.get("main_product_layer", "")), # For agent's vision tool
            "_instruction": "STOP! Do NOT proceed to video generation yet. You MUST execute 'reflection_tool' now to verify this segmentation. If the reflection tool returns 'retry', you must try again with new parameters."
        }
        
        # Publish status for UI sync
        redis_mgr = RedisManager.from_env()
        redis_mgr.set_status(
            task_id=task_id,
            status="step1_completed",
            message="Segmentation finished, verifying quality...",
            extra={"result": converted_result}
        )
        redis_mgr.publish(f"task:{task_id}", {"type": "status", "status": "step1_completed", "data": converted_result})
        
        return json.dumps(converted_result)
    except Exception as e:
        logger.error(f"[Tool] segmentation_tool failed for task {task_id}: {str(e)}")
        return json.dumps({"error": str(e), "decision": "retry"})
