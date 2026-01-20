from pydantic import BaseModel, Field
from typing import List, Optional

class TaskCreate(BaseModel):
    images: List[str] = Field(..., description="List of image paths (local path on server currently, or URL)")
    prompt: Optional[str] = Field("", description="Optional text prompt")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "images": ["/app/data/inputs/image1.jpg", "https://example.com/image2.jpg"],
                    "prompt": "Cinematic shot of a perfume bottle, 4k, slow motion"
                }
            ]
        }
    }

class TaskResponse(BaseModel):
    task_id: str = Field(..., description="Unique Task ID (UUID)")
    status: str = Field(..., description="Task status (queued, processing, completed, failed)")
    message: Optional[str] = Field(None, description="Progress message or error details")
    progress: int = Field(0, description="Progress percentage (0-100)")
    current_step: int = Field(0, description="Current pipeline step index (0-9)")
    output_path: Optional[str] = Field(None, description="Path to generated video (if completed)")
    thumbnail_path: Optional[str] = Field(None, description="Path to thumbnail image (if completed)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_id": "550e8400-e29b-41d4-a716-446655440000",
                    "status": "processing",
                    "message": "Step 5: Video generation...",
                    "progress": 60,
                    "current_step": 5,
                    "output_path": None,
                    "thumbnail_path": None
                },
                {
                    "task_id": "550e8400-e29b-41d4-a716-446655440000",
                    "status": "completed",
                    "message": "Pipeline completed",
                    "progress": 100,
                    "current_step": 9,
                    "output_path": "outputs/550e8400-e29b-41d4-a716-446655440000/final.mp4",
                    "thumbnail_path": "outputs/550e8400-e29b-41d4-a716-446655440000/thumb.jpg"
                }
            ]
        }
    }
