"""
Step 1: Image Segmentation
Uses Qwen-Image-Layered to extract product layers from input image.
"""
from PIL import Image
from pathlib import Path
from typing import Dict, Any, List
import logging
from datetime import datetime

from pipeline.models.qwen_image_layered_loader import QwenImageLayeredLoader
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
            self.loader = QwenImageLayeredLoader()
            self.vram_manager.load_model("qwen_layered", self.loader)
            
            # Perform segmentation
            layers = self.loader.segment(
                image_path=input_image,
                num_layers=num_layers,
                resolution=resolution
            )
            
            # Save layers to disk
            output_dir = TaskPaths.from_repo(task_id).outputs_task_dir / "segmentation"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            layer_paths = []
            for idx, layer in enumerate(layers):
                layer_path = output_dir / f"layer_{idx}.png"
                layer.save(layer_path)
                layer_paths.append(str(layer_path))
                
            # Assume first layer is main product
            main_product_layer = layer_paths[0]
            
            # Unload model
            self.vram_manager.unload_model("qwen_layered")
            
            logger.info(f"[Step 1] Segmentation complete: {len(layers)} layers extracted")
            
            return {
                "segmented_layers": layer_paths,
                "main_product_layer": main_product_layer,
                "metadata": {
                    "num_layers": len(layers),
                    "resolution": resolution,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"[Step 1] Segmentation failed: {e}")
            # Ensure cleanup
            if self.loader:
                self.vram_manager.unload_model("qwen_layered")
            raise
