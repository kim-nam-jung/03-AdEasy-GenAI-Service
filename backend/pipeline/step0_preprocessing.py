from pathlib import Path
from typing import List, Dict
from common.logger import TaskLogger
from common.paths import TaskPaths
from common.config import Config
from pipeline.step0_agentic import Step0_Agentic_Preprocessing

def step0_preprocessing(
    task_id: str,
    paths: TaskPaths,
    logger: TaskLogger,
    cfg: Config,
    image_paths: List[str],
    **kwargs
) -> Dict:
    """
    Step 0: Preprocessing Adapter (Agentic SAM 2)
    """
    logger.info("[Step 0] Adapter: Starting Agentic Background Removal...")
    
    agent = Step0_Agentic_Preprocessing()
    processed_images = []
    
    for idx, img_path in enumerate(image_paths):
        logger.info(f"  Processing image {idx+1}/{len(image_paths)}: {img_path}")
        
        # Use task specific output dir
        output_dir = paths.data_dir / "step0_processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Step0_Agentic handles one file at a time
            processed_path = agent.run(task_id, img_path, str(output_dir))
            processed_images.append(processed_path)
            logger.info(f"  Processed: {processed_path}")
        except Exception as e:
            logger.error(f"  Failed to process {img_path}: {e}")
            # Fallback? Or fail? Fail for now.
            raise e
            
    return {
        "processed_images": processed_images
    }
