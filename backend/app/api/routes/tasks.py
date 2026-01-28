from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import List, Optional
from app.schemas.task import TaskResponse
from app.worker import generate_video_task, resume_video_task
from common.redis_manager import RedisManager
from common.paths import TaskPaths
from app.core.deps import verify_api_key
import uuid
import shutil
from pathlib import Path

router = APIRouter(dependencies=[Depends(verify_api_key)], redirect_slashes=False)

@router.post("", response_model=TaskResponse)
async def create_task(
    files: List[UploadFile] = File(...),
    prompt: Optional[str] = Form("")
):
    """
    Create a new generation task with image uploads.
    """
    MAX_FILE_SIZE = 50 * 1024 * 1024 # 50MB
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="No images uploaded")
    if len(files) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 images allowed")

    # Disk space check
    data_dir = Path("data") # Adjust if data dir is different
    data_dir.mkdir(exist_ok=True)
    usage = shutil.disk_usage(data_dir)
    free_gb = usage.free / (1024**3)
    if free_gb < 5.0:
        raise HTTPException(
            status_code=507, 
            detail=f"Insufficient disk space on server. (Free: {free_gb:.1f}GB, Required: 5GB)"
        )

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
            # 1. Check size (roughly, UploadFile doesn't always show size directly but we can read/seek or check header)
            # Fastapi SpooledTemporaryFile might not expose easy size check without reading.
            # But we can check content-length header if reliable, or count bytes while reading.
            # Simple check: Content-Type header
            if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
                 raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}. Only JPG/PNG/WEBP allowed.")
            
            # Simple extension check
            ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
            if ext not in ALLOWED_EXTENSIONS:
                 raise HTTPException(status_code=400, detail=f"Invalid extension: {file.filename}")
            
            # 1-based index (image_1.jpg)
            dest_path = paths.input_image(idx + 1, ext)
            
            # Write and validate size
            size = 0
            with open(dest_path, "wb") as buffer:
                while content := await file.read(1024 * 1024): # Read in 1MB chunks
                    size += len(content)
                    if size > MAX_FILE_SIZE:
                        # cleanup
                        buffer.close()
                        shutil.rmtree(paths.inputs_task_dir, ignore_errors=True)
                        raise HTTPException(status_code=400, detail=f"File too large: {file.filename} (Max 50MB)")
                    buffer.write(content)
            
            saved_paths.append(str(dest_path))
            await file.close()
            
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

@router.post("/{task_id}/feedback")
async def submit_feedback(task_id: str, feedback: str = Form(...), action: str = Form("retry")):
    """
    Submit human feedback for a paused/failed task.
    Action: "retry" (default) or "proceed"
    """
    redis_mgr = RedisManager.from_env()
    
    # Log the feedback
    redis_mgr.set_status(
        task_id=task_id,
        status="feedback_received", 
        message="User provided feedback. Resuming...",
        extra={"user_feedback": feedback, "action": action}
    )
    
    # Publish event to clear UI
    redis_mgr.publish(f"task:{task_id}", {
        "type": "human_input_received",
        "feedback": feedback
    })
    
    # Trigger Resume Task
    feedback_data = {"action": action, "message": feedback}
    resume_video_task.delay(task_id=task_id, feedback=feedback_data)
    
    return {"status": "resuming", "feedback": feedback, "action": action}
