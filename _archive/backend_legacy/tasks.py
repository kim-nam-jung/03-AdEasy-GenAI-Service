# backend/tasks.py
"""
Celery 비동기 작업 정의
영상 생성 파이프라인 실행
"""

from celery import Task
from backend.celery_config import celery_app
from common.paths import TaskPaths
from common.redis_manager import RedisManager
from common.logger import TaskLogger
from pathlib import Path
import time
import traceback

# Redis Manager
redis_mgr = RedisManager.from_env()


class CallbackTask(Task):
    """
    Celery Task 기본 클래스
    성공/실패 시 Redis 상태 업데이트
    """
    def on_success(self, retval, task_id, args, kwargs):
        """Task 성공 시 호출"""
        user_task_id = kwargs.get('task_id')
        if user_task_id:
            redis_mgr.set_status(
                task_id=user_task_id,
                status="completed",
                current_step=9,
                progress=100,
                message="Video generation completed"
            )
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Task 실패 시 호출"""
        user_task_id = kwargs.get('task_id')
        if user_task_id:
            error_msg = str(exc)[:200]  # 에러 메시지 200자 제한
            redis_mgr.set_status(
                task_id=user_task_id,
                status="failed",
                current_step=-1,
                progress=0,
                message=f"Error: {error_msg}"
            )


@celery_app.task(base=CallbackTask, bind=True, name='backend.tasks.generate_video_task')
def generate_video_task(self, task_id: str, image_paths: list, prompt: str = ""):
    """
    영상 생성 비동기 작업
    
    Args:
        task_id: 작업 ID (16자)
        image_paths: 입력 이미지 경로 리스트
        prompt: 텍스트 프롬프트
    
    Returns:
        dict: 결과 정보
    """
    paths = TaskPaths.from_repo(task_id)
    logger = TaskLogger(task_id, paths.run_log)
    
    try:
        logger.info("=" * 60)
        logger.info(f"🎬 Starting video generation: {task_id}")
        logger.info(f"📷 Images: {len(image_paths)}")
        logger.info(f"✏️  Prompt: '{prompt}'")
        logger.info("=" * 60)
        
        # Redis 상태 업데이트: processing
        redis_mgr.set_status(
            task_id=task_id,
            status="processing",
            current_step=0,
            progress=5,
            message="Pipeline starting..."
        )
        
        # ==================== 더미 파이프라인 (Phase 4 테스트용) ====================
        # 실제 파이프라인은 Phase 5+에서 구현
        
        steps = [
            (0, 10, "Step 0: Preparing inputs..."),
            (1, 20, "Step 1: FastSAM segmentation..."),
            (2, 30, "Step 2: Qwen3-VL understanding..."),
            (3, 40, "Step 3: AdPlan generation..."),
            (4, 50, "Step 4: ControlNet maps..."),
            (5, 60, "Step 5: SDXL keyframe generation..."),
            (6, 70, "Step 6: Wan I2V scene1..."),
            (7, 80, "Step 7: Wan I2V scene2..."),
            (8, 90, "Step 8: Wan I2V scene3..."),
            (9, 95, "Step 9: Final assembly..."),
        ]
        
        for step_num, progress, message in steps:
            logger.info(f"[Step {step_num}] {message}")
            
            # Redis 상태 업데이트
            redis_mgr.set_status(
                task_id=task_id,
                status="processing",
                current_step=step_num,
                progress=progress,
                message=message
            )
            
            # 더미 처리 시간 (실제로는 모델 실행 시간)
            time.sleep(2)  # 2초씩 대기
        
        # ==================== 더미 출력 파일 생성 ====================
        # 실제 파이프라인에서는 real final.mp4가 생성됨
        
        # final.mp4 생성 (더미)
        dummy_video = paths.final_mp4
        with open(dummy_video, 'wb') as f:
            f.write(b'DUMMY_VIDEO_DATA')  # 실제로는 FFmpeg 출력
        
        logger.info(f"✅ Dummy video created: {dummy_video}")
        
        # thumb.jpg 생성 (더미)
        dummy_thumb = paths.thumb_jpg
        with open(dummy_thumb, 'wb') as f:
            f.write(b'DUMMY_THUMBNAIL_DATA')  # 실제로는 첫 프레임 추출
        
        logger.info(f"✅ Dummy thumbnail created: {dummy_thumb}")
        
        # ==================== 완료 ====================
        logger.info("=" * 60)
        logger.info(f"🎉 Pipeline completed: {task_id}")
        logger.info(f"📹 Output: {dummy_video}")
        logger.info(f"🖼️  Thumbnail: {dummy_thumb}")
        logger.info("=" * 60)
        
        # 최종 상태 업데이트 (on_success에서도 호출되지만 명시적으로)
        redis_mgr.set_status(
            task_id=task_id,
            status="completed",
            current_step=9,
            progress=100,
            message="Video generation completed"
        )
        
        return {
            "task_id": task_id,
            "status": "completed",
            "output_path": str(dummy_video),
            "thumbnail_path": str(dummy_thumb)
        }
        
    except Exception as e:
        # 에러 로깅
        error_trace = traceback.format_exc()
        logger.error("=" * 60)
        logger.error(f"❌ Pipeline failed: {task_id}")
        logger.error(f"Error: {str(e)}")
        logger.error(error_trace)
        logger.error("=" * 60)
        
        # Redis 상태 업데이트
        redis_mgr.set_status(
            task_id=task_id,
            status="failed",
            current_step=-1,
            progress=0,
            message=f"Error: {str(e)[:200]}"
        )
        
        # 에러 재발생 (Celery가 처리)
        raise
