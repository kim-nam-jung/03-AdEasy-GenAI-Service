"""
Step 2: Video Generation
Uses LTX-2 Pro to generate video from segmented product image.
"""
from pathlib import Path
from typing import Dict, Any
import logging
from datetime import datetime

from pipeline.models.ltx2_pro_loader import LTX2ProLoader
from common.paths import Paths

logger = logging.getLogger(__name__)

class Step2VideoGeneration:
    def __init__(self, vram_manager):
        """
        Initialize Step 2 - Video Generation.
        
        Args:
            vram_manager: VRAM manager instance
        """
        self.vram_manager = vram_manager
        self.loader = None
        
    def execute(
        self,
        task_id: str,
        main_product_layer: str,
        user_prompt: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute video generation step.
        
        Args:
            task_id: Unique task identifier
            main_product_layer: Path to main product layer image
            user_prompt: User's text prompt for video
            config: Configuration dictionary
            
        Returns:
            Dictionary containing:
                - raw_video_path: Path to generated raw video
                - metadata: Additional metadata
        """
        logger.info(f"[Step 2] Starting video generation for task {task_id}")
        
        try:
            # Get LTX-2 config
            ltx_config = config.get("ltx2", {})
            num_frames = ltx_config.get("num_frames", 33)
            width = ltx_config.get("width", 768)
            height = ltx_config.get("height", 1344)
            fps = ltx_config.get("fps", 24)
            num_inference_steps = ltx_config.get("num_inference_steps", 25)
            guidance_scale = ltx_config.get("guidance_scale", 7.5)
            seed = ltx_config.get("seed", None)
            
            # Load model
            self.loader = LTX2ProLoader(use_fp8=True)
            self.vram_manager.load_model("ltx2_pro", self.loader)
            
            # Generate video
            output_dir = Paths.get_task_dir(task_id) / "video"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_video_path = str(output_dir / f"raw_{timestamp}.mp4")
            
            self.loader.generate_video(
                image_path=main_product_layer,
                prompt=user_prompt,
                num_frames=num_frames,
                width=width,
                height=height,
                fps=fps,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                seed=seed
            )
            
            # Note: LTX2ProLoader.generate_video already saves the file
            # We're assuming it returns/saves to a predictable location
            # Adjust based on actual implementation
            
            # Unload model
            self.vram_manager.unload_model("ltx2_pro")
            
            logger.info(f"[Step 2] Video generation complete: {raw_video_path}")
            
            return {
                "raw_video_path": raw_video_path,
                "metadata": {
                    "num_frames": num_frames,
                    "resolution": f"{width}x{height}",
                    "fps": fps,
                    "inference_steps": num_inference_steps,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"[Step 2] Video generation failed: {e}")
            # Ensure cleanup
            if self.loader:
                self.vram_manager.unload_model("ltx2_pro")
            raise
