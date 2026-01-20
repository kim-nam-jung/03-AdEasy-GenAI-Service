from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import shutil
import os
import json
import uuid
from pathlib import Path

from pipeline.step1_understanding import Step1_Understanding
from pipeline.step2_planning import Step2_Planning

router = APIRouter()

# Temp directory for debug uploads
DEBUG_UPLOAD_DIR = Path("/tmp/adeasy_debug_uploads")
DEBUG_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/step1/analyze")
async def debug_step1_analyze(
    files: list[UploadFile] = File(...),
    prompt: Optional[str] = Form("")
):
    """
    Debug Endpoint for Step 1: Image Analysis & Prompt Augmentation
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Use first file
    file = files[0]
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if file.filename else "png"
    file_path = DEBUG_UPLOAD_DIR / f"{file_id}.{ext}"
    
    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Run Step 1
        step1 = Step1_Understanding()
        result = step1.run(
            task_id=f"debug-{file_id}",
            image_path=str(file_path),
            user_prompt=prompt
        )
        
        return {
            "status": "success",
            "task_id": f"debug-{file_id}",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if file_path.exists():
            os.remove(file_path)

@router.post("/step2/plan")
async def debug_step2_plan(
    files: list[UploadFile] = File(...),
    analysis_data: str = Form(...), # JSON string
    prompt: Optional[str] = Form("")
):
    """
    Debug Endpoint for Step 2: Scenario Planning
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
        
    try:
        # Parse analysis data
        analysis_json = json.loads(analysis_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid analysis_data JSON")
    
    # Use first file
    file = files[0]
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if file.filename else "png"
    file_path = DEBUG_UPLOAD_DIR / f"{file_id}.{ext}"
    
    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Run Step 2
        step2 = Step2_Planning()
        result = step2.run(
            task_id=f"debug-{file_id}",
            image_path=str(file_path),
            analysis_data=analysis_json,
            user_prompt=prompt
        )
        
        return {
            "status": "success",
            "task_id": f"debug-{file_id}",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if file_path.exists():
            os.remove(file_path)
