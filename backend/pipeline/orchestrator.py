# pipeline/orchestrator.py
"""
Video Generation Pipeline Orchestrator (3-Step Simplified)

Step 1: Segmentation (SAM 2)
Step 2: Video Generation (LTX-2 FP8)
Step 3: Post-processing (RIFE + Real-CUGAN + FFmpeg)
"""

from pathlib import Path
from typing import List, Dict, Optional
from common.paths import TaskPaths
from common.logger import TaskLogger
from common.config import Config
from common.redis_manager import RedisManager
from pipeline.vram_manager import VRAMManager


class PipelineOrchestrator:
    """
    Orchestrator for 3-step video generation pipeline
    """
    
    def __init__(
        self, 
        task_id: str, 
        image_paths: List[str], 
        prompt: str = "",
        redis_mgr: Optional[RedisManager] = None
    ):
        """
        Initialize orchestrator
        
        Args:
            task_id: Task ID
            image_paths: Input image paths
            prompt: Text prompt
            redis_mgr: Redis manager (optional)
        """
        self.task_id = task_id
        self.image_paths = image_paths
        self.prompt = prompt
        
        # Paths & Logger
        self.paths = TaskPaths.from_repo(task_id)
        self.logger = TaskLogger(task_id, self.paths.run_log)
        
        # Config & Redis & VRAM
        self.cfg = Config.load()
        self.redis_mgr = redis_mgr or RedisManager.from_env()
        self.vram_mgr = VRAMManager(logger=self.logger, cfg=self.cfg)
        
        self.logger.info("=" * 60)
        self.logger.info(f"🎬 PipelineOrchestrator v3.0 (3-Step) initialized")
        self.logger.info(f"   Task ID: {task_id}")
        self.logger.info(f"   Images: {len(image_paths)}")
        self.logger.info(f"   Prompt: '{prompt}'")
        self.logger.info("=" * 60)
    
    def _update_status(self, step: int, progress: int, message: str):
        """
        Redis status update helper
        """
        self.redis_mgr.set_status(
            task_id=self.task_id,
            status="processing",
            current_step=step,
            progress=progress,
            message=message
        )
    
    def run(self) -> Dict:
        """
        Execute 3-step agentic pipeline
        """
        self.logger.info("=" * 60)
        self.logger.info("🚀 Starting 3-Step Pipeline...")
        self.logger.info("=" * 60)
        
        try:
            from pipeline.graph import create_agent_graph
            
            # Initial State for 3-step pipeline
            initial_state = {
                "task_id": self.task_id,
                "user_prompt": self.prompt,
                "image_paths": self.image_paths,
                "config": self.cfg._data,
                "current_step": "start",
                "next_step": "vision",
                "step_results": {},
                "vision_analysis": {},
                "segmented_layers": [],
                "main_product_layer": "",
                "raw_video_path": "",
                "final_video_path": "",
                "thumbnail_path": "",
                "error": None,
                "retry_count": {},
                "reflection_history": [],
                "final_output": {}
            }
            
            # Compile and run graph
            app = create_agent_graph(self.task_id)
            final_state = app.invoke(initial_state, {"recursion_limit": 50})
            
            # Check for errors
            if final_state.get("error"):
                raise Exception(final_state["error"])
            
            # Extract final outputs
            final_output = final_state.get("final_output", {})
            final_video = final_state.get("final_video_path", "")
            thumbnail = final_state.get("thumbnail_path", "")
            
            if not final_video:
                raise Exception("Pipeline completed but no final video generated")
            
            self.logger.info("")
            self.logger.info("=" * 60)
            self.logger.info("✅ 3-Step Pipeline completed successfully!")
            self.logger.info(f"   Final video: {final_video}")
            self.logger.info(f"   Thumbnail: {thumbnail}")
            self.logger.info("=" * 60)
            
            # Update Redis status
            self.redis_mgr.set_status(
                task_id=self.task_id,
                status="completed",
                current_step=3,
                progress=100,
                message="Pipeline completed",
                extra={
                    "output_path": final_video,
                    "thumbnail_path": thumbnail
                }
            )
            
            return {
                "status": "success",
                "task_id": self.task_id,
                "final_video": str(final_video),
                "thumbnail": str(thumbnail),
                "final_output": final_output,
                "reflection_history": final_state.get("reflection_history", [])
            }
            
        except Exception as e:
            self.logger.error("")
            self.logger.error("=" * 60)
            self.logger.error(f"❌ Pipeline failed: {str(e)}")
            self.logger.error("=" * 60)
            
            self.redis_mgr.set_status(
                task_id=self.task_id,
                status="failed",
                current_step=-1,
                progress=0,
                message=f"Error: {str(e)[:200]}"
            )
            
            raise
