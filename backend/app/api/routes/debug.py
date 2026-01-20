from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, List
import shutil
import os
import json
import uuid
from pathlib import Path

from pipeline.step1_segmentation import Step1Segmentation
from pipeline.step2_video_generation import Step2VideoGeneration
from pipeline.step3_postprocess import Step3Postprocess
from pipeline.vram_manager import VRAMManager
from common.config import Config
from app.core.deps import verify_api_key
from fastapi import Depends

router = APIRouter(dependencies=[Depends(verify_api_key)])

# Temp directory for debug uploads
DEBUG_UPLOAD_DIR = Path("/tmp/adeasy_debug_uploads")
DEBUG_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Shared VRAM manager for debug
_vram_mgr = None

def get_vram_mgr():
    global _vram_mgr
    if _vram_mgr is None:
        _vram_mgr = VRAMManager()
    return _vram_mgr

@router.post("/step1/segmentation")
async def debug_step1_segmentation(
    files: List[UploadFile] = File(...),
    num_layers: int = Form(4),
    resolution: int = Form(640)
):
    """
    Debug Endpoint for Step 1: Segmentation
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    file = files[0]
    task_id = f"debug-{uuid.uuid4().hex[:8]}"
    ext = file.filename.split(".")[-1] if file.filename else "png"
    file_path = DEBUG_UPLOAD_DIR / f"{task_id}.{ext}"
    
    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        vram_mgr = get_vram_mgr()
        step1 = Step1Segmentation(vram_mgr)
        
        config = {
            "segmentation": {
                "num_layers": num_layers,
                "resolution": resolution
            }
        }
        
        result = step1.execute(
            task_id=task_id,
            image_paths=[str(file_path)],
            config=config
        )
        
        return {
            "status": "success",
            "task_id": task_id,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup input file
        if file_path.exists():
            os.remove(file_path)

@router.post("/step2/video_generation")
async def debug_step2_video_generation(
    main_product_layer: str = Form(...),
    prompt: str = Form(...),
    num_frames: int = Form(96)
):
    """
    Debug Endpoint for Step 2: Video Generation
    """
    task_id = f"debug-{uuid.uuid4().hex[:8]}"
    
    try:
        vram_mgr = get_vram_mgr()
        step2 = Step2VideoGeneration(vram_mgr)
        
        config = {
            "ltx2": {
                "num_frames": num_frames
            }
        }
        
        result = step2.execute(
            task_id=task_id,
            main_product_layer=main_product_layer,
            user_prompt=prompt,
            config=config
        )
        
        return {
            "status": "success",
            "task_id": task_id,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/step3/postprocess")
async def debug_step3_postprocess(
    raw_video_path: str = Form(...),
    rife_enabled: bool = Form(True),
    cugan_enabled: bool = Form(True)
):
    """
    Debug Endpoint for Step 3: Post-processing
    """
    task_id = f"debug-{uuid.uuid4().hex[:8]}"
    
    try:
        vram_mgr = get_vram_mgr()
        step3 = Step3Postprocess(vram_mgr)
        
        config = {
            "postprocess": {
                "rife": {"enabled": rife_enabled},
                "real_cugan": {"enabled": cugan_enabled}
            }
        }
        
        result = step3.execute(
            task_id=task_id,
            raw_video_path=raw_video_path,
            config=config
        )
        
        return {
            "status": "success",
            "task_id": task_id,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def debug_cleanup():
    """
    Unload all models from VRAM
    """
    try:
        vram_mgr = get_vram_mgr()
        vram_mgr.unload_all()
        return {"status": "success", "message": "All models unloaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
