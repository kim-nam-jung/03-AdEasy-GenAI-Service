import os
from pathlib import Path
from typing import Dict
from common.logger import TaskLogger
from common.paths import TaskPaths
from common.config import Config
from pipeline.step3_api import ControlMapGeneratorAPI

def step3_control(
    task_id: str,
    paths: TaskPaths,
    logger: TaskLogger,
    cfg: Config,
    processed_images: list,
    **kwargs
) -> Dict:
    """
    Step 3: Control Map Generation Adapter (API)
    """
    logger.info("[Step 3] Adapter: Generating Control Maps via API...")
    
    generator = ControlMapGeneratorAPI()
    control_maps = []
    
    # Process only the first image for now as keyframe source? 
    # Or for each processed image?
    # Usually AdEasy pipeline generates specific keyframes in Step 4 based on constraints.
    # Step 3 generates control maps for the INPUT processed images (Step 0 output).
    
    output_dir = paths.data_dir / "step3_control"
    
    for idx, img_path in enumerate(processed_images):
        logger.info(f"  Generating maps for: {img_path}")
        try:
            res = generator.run(img_path, str(output_dir))
            control_maps.append(res)
        except Exception as e:
            logger.error(f"  Failed step3 for {img_path}: {e}")
            raise e
            
    return {
        "control_maps": control_maps
    }
