# common/paths.py
"""
TaskPaths: task_id별 경로 관리
- outputs/{task_id}/: 최종 산출물
- data/temp/{task_id}/: 중간 파일
- data/inputs/{task_id}/: 입력 이미지 (🆕 추가)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


_TASK_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{2,63}$")


def validate_task_id(task_id: str) -> str:
    if not _TASK_ID_RE.match(task_id):
        raise ValueError(
            f"Invalid task_id='{task_id}'. "
            "Use 3~64 chars: alnum + '_' + '-', starting with alnum."
        )
    return task_id


@dataclass(frozen=True)
class TaskPaths:
    """Centralized path rules for a given task_id."""
    root: Path
    task_id: str

    @classmethod
    def from_repo(cls, task_id: str, root: Path | None = None) -> "TaskPaths":
        task_id = validate_task_id(task_id)
        if root is None:
            # common/paths.py -> common -> repo root
            root = Path(__file__).resolve().parents[1]
        return cls(root=root, task_id=task_id)

    # ==================== base dirs ====================
    @property
    def outputs_task_dir(self) -> Path:
        """outputs/{task_id}/ - 최종 산출물"""
        return self.root / "outputs" / self.task_id

    @property
    def temp_task_dir(self) -> Path:
        """data/temp/{task_id}/ - 중간 파일"""
        return self.root / "data" / "temp" / self.task_id

    @property
    def inputs_task_dir(self) -> Path:
        """🆕 data/inputs/{task_id}/ - 업로드된 원본 이미지"""
        return self.root / "data" / "inputs" / self.task_id

    @property
    def inputs_dir(self) -> Path:
        """data/inputs/ - 모든 입력 루트 (호환성 유지)"""
        return self.root / "data" / "inputs"

    @property
    def bgm_dir(self) -> Path:
        """data/bgm/ - BGM 라이브러리"""
        return self.root / "data" / "bgm"

    # ==================== output artifacts ====================
    @property
    def final_mp4(self) -> Path:
        """outputs/{task_id}/final.mp4"""
        return self.outputs_task_dir / "final.mp4"

    @property
    def thumb_jpg(self) -> Path:
        """outputs/{task_id}/thumb.jpg"""
        return self.outputs_task_dir / "thumb.jpg"

    @property
    def run_json(self) -> Path:
        """outputs/{task_id}/run.json"""
        return self.outputs_task_dir / "run.json"

    @property
    def run_log(self) -> Path:
        """outputs/{task_id}/run.log"""
        return self.outputs_task_dir / "run.log"

    # ==================== input files (🆕 추가) ====================
    def input_image(self, idx: int, ext: str = "jpg") -> Path:
        """
        🆕 data/inputs/{task_id}/image_{idx}.{ext}
        
        Args:
            idx: 이미지 번호 (1부터 시작)
            ext: 확장자 (jpg, png, webp 등)
        
        Example:
            paths.input_image(1, "jpg")  # data/inputs/abc123/image_1.jpg
        """
        return self.inputs_task_dir / f"image_{idx}.{ext}"

    # ==================== intermediate files ====================
    def scene_raw_mp4(self, scene_id: int) -> Path:
        """data/temp/{task_id}/scene{scene_id}_raw.mp4"""
        return self.temp_task_dir / f"scene{scene_id}_raw.mp4"

    def scene_esrgan_mp4(self, scene_id: int) -> Path:
        """data/temp/{task_id}/scene{scene_id}_esrgan.mp4"""
        return self.temp_task_dir / f"scene{scene_id}_esrgan.mp4"

    def scene_final_mp4(self, scene_id: int) -> Path:
        """data/temp/{task_id}/scene{scene_id}_final.mp4"""
        return self.temp_task_dir / f"scene{scene_id}_final.mp4"

    def keyframe_png(self, scene_id: int) -> Path:
        """data/temp/{task_id}/keyframe_{scene_id}.png"""
        return self.temp_task_dir / f"keyframe_{scene_id}.png"

    # ==================== ensure dirs ====================
    def ensure_dirs(self) -> None:
        """필요한 모든 디렉토리 생성 (🆕 inputs_task_dir 추가)"""
        self.outputs_task_dir.mkdir(parents=True, exist_ok=True)
        self.temp_task_dir.mkdir(parents=True, exist_ok=True)
        self.inputs_task_dir.mkdir(parents=True, exist_ok=True)  # 🆕
        self.inputs_dir.mkdir(parents=True, exist_ok=True)
        self.bgm_dir.mkdir(parents=True, exist_ok=True)
