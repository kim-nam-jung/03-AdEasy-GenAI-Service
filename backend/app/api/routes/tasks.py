from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import List, Optional
from app.schemas.task import TaskResponse
from app.worker import generate_video_task
from common.redis_manager import RedisManager
from common.paths import TaskPaths
from app.core.deps import verify_api_key
import uuid
import shutil
from pathlib import Path

router = APIRouter(dependencies=[Depends(verify_api_key)])

@router.post("/", response_model=TaskResponse)
async def create_task(
    files: List[UploadFile] = File(...),
    prompt: Optional[str] = Form("")
):
    """
    Create a new generation task with image uploads.
    """
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="No images uploaded")
    if len(files) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 images allowed")

    task_id = str(uuid.uuid4())
    
    # Init paths
    paths = TaskPaths.from_repo(task_id) # Using repo root from common.paths logic
    # Note: common.paths logic defaults to relative path. 
    # In Docker, we might want to ensure it points to /app/data which is mounted.
    # paths.inputs_task_dir handles creation.
    
    paths.ensure_dirs()
    
    saved_paths = []
    
    try:
        for idx, file in enumerate(files):
            # 1-based index (image_1.jpg)
            # Preserve extension or convert? simple approach: use extension
            ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
            dest_path = paths.input_image(idx + 1, ext)
            
            with open(dest_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            saved_paths.append(str(dest_path))
            
    except Exception as e:
        # Cleanup if failed
        shutil.rmtree(paths.inputs_task_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded files: {str(e)}")
    
    # Trigger Celery Task
    # Pass string paths
    generate_video_task.delay(
        task_id=task_id, 
        image_paths=saved_paths, 
        prompt=prompt
    )
    
    return {
        "task_id": task_id, 
        "status": "queued",
        "message": f"Task queued with {len(saved_paths)} images"
    }

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """
    Get task status from Redis.
    """
    redis_mgr = RedisManager.from_env()
    status_data = redis_mgr.get_status(task_id)
    
    if not status_data:
        # Task ID exists but no status in Redis (maybe expired or just created)
        # For now, return a default unknown/queued state
        return {
            "task_id": task_id,
            "status": "unknown",
            "message": "Task not found or expired"
        }
    
    return status_data
