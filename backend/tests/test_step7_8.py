import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from pipeline.step7_8_assembly import step7_8_assembly
from common.paths import TaskPaths
from common.logger import TaskLogger
from common.config import Config
from common.schema import AdPlan, ScenePlan

@pytest.fixture
def mock_components():
    task_id = "test_task"
    paths = MagicMock(spec=TaskPaths)
    paths.final_mp4 = Path("/tmp/final.mp4")
    paths.thumb_jpg = Path("/tmp/thumb.jpg")
    
    logger = MagicMock(spec=TaskLogger)
    cfg = MagicMock(spec=Config)
    cfg.get.return_value = {} # default video cfg
    
    adplan = MagicMock(spec=AdPlan)
    adplan.scenes = [MagicMock(spec=ScenePlan), MagicMock(spec=ScenePlan), MagicMock(spec=ScenePlan)]
    
    return task_id, paths, logger, cfg, adplan

@patch("subprocess.run")
def test_step7_8_assembly_success(mock_subprocess, mock_components):
    task_id, paths, logger, cfg, adplan = mock_components
    
    processed_videos = [Path("v1.mp4"), Path("v2.mp4"), Path("v3.mp4")]
    
    result = step7_8_assembly(
        task_id=task_id,
        paths=paths,
        logger=logger,
        cfg=cfg,
        adplan=adplan,
        processed_videos=processed_videos
    )
    
    # Verify FFmpeg call
    assert mock_subprocess.call_count == 2 # 1 for basic concat, 1 for thumb
    
    # Check return
    assert result["final_video"] == paths.final_mp4
    assert result["thumbnail"] == paths.thumb_jpg
