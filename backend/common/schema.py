# common/schema.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class ControlConstraints(BaseModel):
    model_config = ConfigDict(extra="allow")
    preserve_shape: bool = True
    preserve_color: bool = True
    preserve_text: List[str] = Field(default_factory=list)
    controlnet_scale: float = 0.8



class SceneConfig(BaseModel):
    """Scene 구성 정보 (간단 버전)"""
    model_config = ConfigDict(extra="allow")
    scene_id: int
    duration: float = Field(gt=0)
    prompt: str
    camera_movement: str = Field(default="static")
    transition: str = Field(default="dissolve")


class ScenePlan(BaseModel):
    model_config = ConfigDict(extra="allow")
    scene_id: int
    duration: float = Field(gt=0)
    keyframe_prompt_image: str
    keyframe_prompt_video: str
    control_constraints: ControlConstraints = Field(default_factory=ControlConstraints)


class SubtitlePlan(BaseModel):
    model_config = ConfigDict(extra="allow")
    text: str
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    position: str
    font: str = "Noto Sans KR"
    font_size: int = 48
    color: str = "white"
    outline_color: str = "black"
    outline_width: int = 2
    animation: Optional[str] = None


class BGMPlan(BaseModel):
    model_config = ConfigDict(extra="allow")
    mood: str
    volume: float = Field(ge=0, le=1)
    fade_in: float = Field(ge=0)
    fade_out: float = Field(ge=0)
    source: Optional[str] = None


class AdPlan(BaseModel):
    model_config = ConfigDict(extra="allow")
    concept: str
    target_audience: str
    mood: str
    global_constraints: Dict[str, Any] = Field(default_factory=dict)
    negative_prompt_image: str = ""
    negative_prompt_video: str = ""
    scenes: List[ScenePlan]
    subtitles: List[SubtitlePlan] = Field(default_factory=list)
    bgm: Optional[BGMPlan] = None


# run.json (최소형)
class RunPerformance(BaseModel):
    model_config = ConfigDict(extra="allow")
    total_time_seconds: float
    vram_peak_gb: Optional[float] = None
    wan_output_fps: Optional[int] = None
    rife_applied: Optional[bool] = None
    step_times: Dict[str, float] = Field(default_factory=dict)


class RunQuality(BaseModel):
    model_config = ConfigDict(extra="allow")
    identity_score: float
    status: Literal["passed", "failed"]
    sampled_frames: Optional[int] = None
    top_50_percent_frames: Optional[int] = None


class RunOutputs(BaseModel):
    model_config = ConfigDict(extra="allow")
    video_path: str
    thumbnail_path: Optional[str] = None
    duration_seconds: float
    resolution: str
    fps: int


class RunMeta(BaseModel):
    model_config = ConfigDict(extra="allow")
    task_id: str
    timestamp: str
    version: str = "v2.3"
    performance: RunPerformance
    quality: RunQuality
    outputs: RunOutputs
