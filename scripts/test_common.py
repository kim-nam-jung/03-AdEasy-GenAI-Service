# scripts/test_common.py
from common.paths import TaskPaths
from common.logger import TaskLogger
from common.redis_manager import RedisManager

def run_pipeline(task_id: str):
    paths = TaskPaths.from_repo(task_id)
    paths.ensure_dirs()

    log = TaskLogger(task_id, paths.run_log)
    rds = RedisManager.from_env()

    rds.set_status(task_id, status="processing", current_step=0, progress=0, message="start")
    log.info(f"✅ Task {task_id} start")

    log.step(5, "Wan I2V", "scene1 generating...")
    rds.set_status(task_id, status="processing", current_step=5, progress=55)

    rds.set_status(task_id, status="completed", current_step=9, progress=100, message="done")
    log.info("✅ completed")

if __name__ == "__main__":
    run_pipeline("smoke_001")
