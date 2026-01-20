"""
Step 3: Post-processing
Applies RIFE frame interpolation and Real-CUGAN upscaling to finalize video.
"""
from pathlib import Path
from typing import Dict, Any
import logging
from datetime import datetime
import subprocess

from pipeline.models.rife_loader import RIFELoader
from pipeline.models.real_cugan_loader import RealCUGANLoader
from common.paths import TaskPaths

logger = logging.getLogger(__name__)

class Step3Postprocess:
    def __init__(self, vram_manager):
        """
        Initialize Step 3 - Post-processing.
        
        Args:
            vram_manager: VRAM manager instance
        """
        self.vram_manager = vram_manager
        self.rife_loader = None
        self.cugan_loader = None
        
    def execute(
        self,
        task_id: str,
        raw_video_path: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute post-processing step.
        
        Args:
            task_id: Unique task identifier
            raw_video_path: Path to raw video from Step 2
            config: Configuration dictionary
            
        Returns:
            Dictionary containing:
                - final_video_path: Path to final processed video
                - thumbnail_path: Path to video thumbnail
                - metadata: Additional metadata
        """
        logger.info(f"[Step 3] Starting post-processing for task {task_id}")
        
        try:
            # Get post-process config
            postprocess_config = config.get("postprocess", {})
            rife_config = postprocess_config.get("rife", {})
            cugan_config = postprocess_config.get("real_cugan", {})
            output_config = postprocess_config.get("output", {})
            
            output_dir = TaskPaths.from_repo(task_id).outputs_task_dir / "final"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            current_video = raw_video_path
            
            # Step 3.1: RIFE Frame Interpolation (if enabled)
            if rife_config.get("enabled", True):
                logger.info("[Step 3.1] Applying RIFE frame interpolation")
                
                target_fps = rife_config.get("target_fps", 48)
                
                self.rife_loader = RIFELoader()
                self.vram_manager.load_model("rife", self.rife_loader)
                
                interpolated_path = str(output_dir / "interpolated.mp4")
                self.rife_loader.interpolate_video(
                    input_video_path=current_video,
                    output_video_path=interpolated_path,
                    target_fps=target_fps
                )
                
                self.vram_manager.unload_model("rife")
                current_video = interpolated_path
            
            # Step 3.2: Real-CUGAN Upscaling (if enabled)
            if cugan_config.get("enabled", True):
                logger.info("[Step 3.2] Applying Real-CUGAN upscaling")
                
                scale = cugan_config.get("scale", 2)
                model_name = cugan_config.get("model", "pro")
                
                self.cugan_loader = RealCUGANLoader(model_name=model_name)
                self.vram_manager.load_model("real_cugan", self.cugan_loader)
                
                upscaled_path = str(output_dir / "upscaled.mp4")
                self.cugan_loader.upscale_video(
                    input_video_path=current_video,
                    output_video_path=upscaled_path,
                    scale=scale
                )
                
                self.vram_manager.unload_model("real_cugan")
                current_video = upscaled_path
            
            # Step 3.3: Final encoding with FFmpeg
            logger.info("[Step 3.3] Final encoding with FFmpeg")
            
            final_width = output_config.get("width", 1080)
            final_height = output_config.get("height", 1920)
            final_fps = output_config.get("fps", 24)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_video_path = str(output_dir / f"final_{timestamp}.mp4")
            
            # Use FFmpeg for final encoding and resolution adjustment
            ffmpeg_cmd = [
                "ffmpeg", "-i", current_video,
                "-vf", f"scale={final_width}:{final_height}",
                "-r", str(final_fps),
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-y",
                final_video_path
            ]
            
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            
            # Generate thumbnail
            thumbnail_path = str(output_dir / f"thumbnail_{timestamp}.jpg")
            thumb_cmd = [
                "ffmpeg", "-i", final_video_path,
                "-vf", "select=eq(n\\,0)",
                "-vframes", "1",
                "-y",
                thumbnail_path
            ]
            subprocess.run(thumb_cmd, check=True, capture_output=True)
            
            logger.info(f"[Step 3] Post-processing complete: {final_video_path}")
            
            return {
                "final_video_path": final_video_path,
                "thumbnail_path": thumbnail_path,
                "metadata": {
                    "resolution": f"{final_width}x{final_height}",
                    "fps": final_fps,
                    "rife_applied": rife_config.get("enabled", True),
                    "cugan_applied": cugan_config.get("enabled", True),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"[Step 3] Post-processing failed: {e}")
            # Ensure cleanup
            if self.rife_loader:
                self.vram_manager.unload_model("rife")
            if self.cugan_loader:
                self.vram_manager.unload_model("real_cugan")
            raise
