# backend/tasks.py
"""
Celery 비동기 작업 정의
영상 생성 파이프라인 실행
"""

from celery import Task
from app.core.celery_config import celery_app
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


from pipeline.orchestrator import PipelineOrchestrator

@celery_app.task(base=CallbackTask, bind=True, name='app.worker.generate_video_task')
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
    try:
        # Pipeline Orchestrator 초기화 및 실행
        orchestrator = PipelineOrchestrator(
            task_id=task_id,
            image_paths=image_paths,
            prompt=prompt,
            redis_mgr=redis_mgr
        )
        
        # 파이프라인 실행
        result = orchestrator.run()
        
        return result
        
    except Exception as e:
        # 에러 로깅 (Orchestrator 내부에서도 로깅하지만, 여기서 한 번 더 안전장치)
        logger_err = TaskLogger(task_id, TaskPaths.from_repo(task_id).run_log)
        logger_err.error(f"❌ Worker failed: {str(e)}")
        
        # Redis 상태 업데이트 (실패)
        redis_mgr.set_status(
            task_id=task_id,
            status="failed",
            current_step=-1,
            progress=0,
            message=f"System Error: {str(e)[:200]}"
        )
        raise
        

