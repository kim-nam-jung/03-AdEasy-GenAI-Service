"""
Step 1: Image Segmentation
Uses Qwen-Image-Layered to extract product layers from input image.
"""
from PIL import Image
from pathlib import Path
from typing import Dict, Any, List
import logging
from datetime import datetime

from pipeline.models.sam2_loader import SAM2Loader
from common.paths import TaskPaths

logger = logging.getLogger(__name__)

class Step1Segmentation:
    def __init__(self, vram_manager):
        """
        Initialize Step 1 - Segmentation.
        
        Args:
            vram_manager: VRAM manager instance
        """
        self.vram_manager = vram_manager
        self.loader = None
        
    def execute(
        self,
        task_id: str,
        image_paths: List[str],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute segmentation step.
        
        Args:
            task_id: Unique task identifier
            image_paths: List of input image paths
            config: Configuration dictionary
            
        Returns:
            Dictionary containing:
                - segmented_layers: List of layer image paths
                - main_product_layer: Path to main product layer
                - metadata: Additional metadata
        """
        logger.info(f"[Step 1] Starting segmentation for task {task_id}")
        
        try:
            # Get segmentation config
            seg_config = config.get("segmentation", {})
            num_layers = seg_config.get("num_layers", 4)
            resolution = seg_config.get("resolution", 640)
            
            # Use first image (assuming single product image)
            input_image = image_paths[0]
            
            # Load model
            self.loader = SAM2Loader()
            self.vram_manager.load_model("sam2", self.loader)
            
            # Get detailed config
            prompt_mode = seg_config.get("prompt_mode", "center")
            
            # Perform segmentation (Product only)
            product_image = self.loader.segment_product(
                image_path=input_image,
                prompt_mode=prompt_mode
            )
            
            # Save results
            output_dir = TaskPaths.from_repo(task_id).outputs_task_dir / "segmentation"
            output_dir.mkdir(parents=True, exist_ok=True)

            product_layer_path = output_dir / "product_layer.png"
            product_image.save(product_layer_path)

            # Unload model
            self.vram_manager.unload_model("sam2")

            logger.info(f"[Step 1] Segmentation complete: Product extracted")

            return {
                "segmented_layers": [str(product_layer_path)],
                "main_product_layer": str(product_layer_path),
                "metadata": {
                    "method": "SAM 2",
                    "resolution": resolution,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"[Step 1] Segmentation failed: {e}")
            # Ensure cleanup
            if self.loader:
                self.vram_manager.unload_model("sam2")
            raise
