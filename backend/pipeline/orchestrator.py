# pipeline/orchestrator.py
"""
영상 생성 파이프라인 오케스트레이터 (Updated 2026-01-06)

Step 0: 입력 전처리 (FastSAM)
Step 1: 이미지 이해 (Qwen2-VL-7B)
Step 1.5: 프롬프트 증강 (Qwen2.5-14B) ← 추가!
Step 2: 광고 기획 (Qwen2.5-14B)
Step 3: 제어맵 생성 (ControlNet Canny + MiDaS Depth)
Step 4: 키프레임 생성 (SDXL 1.0 + ControlNet)
Step 5: 영상 생성 (LTX-Video 13B Distilled I2V)
Step 6: 후처리 (RIFE + Real-ESRGAN)
Step 7-8: 최종 조립 (FFmpeg)
Step 9: 품질 검증 (Identity Score)
"""

from pathlib import Path
from typing import List, Dict, Optional
from common.paths import TaskPaths
from common.logger import TaskLogger
from common.config import Config
from common.redis_manager import RedisManager
from common.schema import AdPlan

# Step imports
from pipeline.step0_preprocessing import step0_preprocessing
from pipeline.step1_understanding import step1_understanding
from pipeline.step1_5_prompt_expansion import step1_5_prompt_expansion  # ← 추가
from pipeline.step2_planning import step2_planning
from pipeline.step3_control import step3_control
from pipeline.step4_generation import step4_generation
from pipeline.step5_video import step5_video
from pipeline.step6_postprocess import step6_postprocess
from pipeline.step7_8_assembly import step7_8_assembly
from pipeline.step9_validation import step9_validation
from pipeline.vram_manager import VRAMManager


class PipelineOrchestrator:
    """
    영상 생성 파이프라인 총괄 관리자 (v2.5)
    """
    
    def __init__(
        self, 
        task_id: str, 
        image_paths: List[str], 
        prompt: str = "",
        redis_mgr: Optional[RedisManager] = None
    ):
        """
        초기화
        
        Args:
            task_id: 작업 ID
            image_paths: 입력 이미지 경로 리스트
            prompt: 텍스트 프롬프트
            redis_mgr: Redis 관리자 (선택)
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
        self.logger.info(f"🎬 PipelineOrchestrator v2.5 initialized")
        self.logger.info(f"   Task ID: {task_id}")
        self.logger.info(f"   Images: {len(image_paths)}")
        self.logger.info(f"   Prompt: '{prompt}'")
        self.logger.info("=" * 60)
    
    def _update_status(self, step: float, progress: int, message: str):
        """
        Redis 상태 업데이트 헬퍼
        
        Args:
            step: 현재 Step 번호 (1.5 지원)
            progress: 진행률 (0~100)
            message: 상태 메시지
        """
        self.redis_mgr.set_status(
            task_id=self.task_id,
            status="processing",
            current_step=int(step),  # Redis는 정수만 지원
            progress=progress,
            message=message
        )
    
    def run(self) -> Dict:
        """
        전체 파이프라인 실행 (Agentic Workflow v3.0)
        """
        self.logger.info("=" * 60)
        self.logger.info("🚀 Starting Agentic Pipeline execution (v3.0)...")
        self.logger.info("=" * 60)
        
        try:
            from pipeline.graph import create_agent_graph
            
            # Initial State
            initial_state = {
                "task_id": self.task_id,
                "user_prompt": self.prompt,
                "image_paths": self.image_paths,
                "config": self.cfg._data, # Pass dict
                "current_step": "start",
                "step_results": {},
                "retry_count": {},
                "reflection_history": []
            }
            
            # Compile Graph
            app = create_agent_graph(self.task_id, self.redis_mgr)
            
            # Invoke Graph
            # recursions limit can be increased if many retries needed
            final_state = app.invoke(initial_state, {"recursion_limit": 50})
            
            # Extract Results
            results = final_state.get("step_results", {})
            
            # Check for failure
            if final_state.get("error"):
                 raise Exception(final_state["error"])
                 
            # Retrieve final step outputs (Step 7-8 and Step 9)
            step7_8_res = results.get("step7_8", {})
            step9_res = results.get("step9", {})
            
            if not step7_8_res:
                raise Exception("Pipeline finished but no video generated (Step 7-8 missing)")
                
            final_video = step7_8_res.get("final_video")
            thumbnail = step7_8_res.get("thumbnail")
            identity_score = step9_res.get("identity_score", 0.0)
            passed = step9_res.get("passed", False)

            self.logger.info("")
            self.logger.info("=" * 60)
            self.logger.info("✅ Agentic Pipeline completed successfully!")
            self.logger.info(f"   Final video: {final_video}")
            self.logger.info(f"   Thumbnail: {thumbnail}")
            self.logger.info(f"   Identity Score: {identity_score:.4f}")
            self.logger.info(f"   Validation: {'✅ PASSED' if passed else '❌ FAILED'}")
            self.logger.info("=" * 60)
            
            # Redis Update provided by Graph nodes? 
            # Nodes handle updates, but final 'completed' status is good here.
            self.redis_mgr.set_status(
                task_id=self.task_id,
                status="completed",
                current_step=9,
                progress=100,
                message="Pipeline completed",
                extra={
                    "output_path": f"outputs/{self.task_id}/final.mp4",
                    "thumbnail_path": f"outputs/{self.task_id}/thumb.jpg"
                }
            )
            
            return {
                "status": "success",
                "task_id": self.task_id,
                "final_video": str(final_video),
                "thumbnail": str(thumbnail),
                "identity_score": identity_score,
                "passed": passed,
                "reflection_history": final_state.get("reflection_history")
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
