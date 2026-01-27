# backend/celery_config.py
"""
Celery 설정 및 초기화
Redis를 브로커/백엔드로 사용
"""

from celery import Celery
from common.config import Config

# Config 로드
cfg = Config.load()

# Redis URL 가져오기
# Resolve env var first (happens in Config.load)
redis_url = cfg.get('redis.url') or cfg.get('redis.default_url', 'redis://localhost:6379/0')

# Celery 앱 생성
celery_app = Celery(
    'adeasy_shorts',
    broker=redis_url,
    backend=redis_url,
    include=['app.worker']  # tasks 모듈 자동 로드
)

# Celery 설정
celery_app.conf.update(
    # 타임존
    timezone='Asia/Seoul',
    enable_utc=True,
    
    # 결과 저장 설정
    result_expires=86400,  # 24시간 후 결과 삭제
    result_persistent=True,  # Redis 재시작 시에도 유지
    
    # Task 설정
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    task_track_started=True,  # Task 시작 시점 추적
    task_time_limit=14400,  # 4시간 최대 실행 시간
    task_soft_time_limit=13800,  # 3시간 50분 소프트 타임아웃
    
    # Worker 설정
    worker_prefetch_multiplier=1,  # 한 번에 1개 Task만 가져오기 (GPU 작업용)
    worker_max_tasks_per_child=50,  # 50개 작업 후 워커 재시작 (메모리 누수 방지)
    
    # 로그
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

# 설정 확인용
if __name__ == '__main__':
    print("🔧 Celery Config:")
    print(f"   Broker: {celery_app.conf.broker_url}")
    print(f"   Backend: {celery_app.conf.result_backend}")
    print(f"   Timezone: {celery_app.conf.timezone}")
