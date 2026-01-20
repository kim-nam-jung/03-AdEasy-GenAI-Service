import pytest
from unittest.mock import MagicMock, patch
from pipeline.orchestrator import PipelineOrchestrator
from common.redis_manager import RedisManager

@pytest.fixture
def mock_redis():
    mock = MagicMock(spec=RedisManager)
    return mock

@pytest.fixture
def mock_vram():
    with patch("pipeline.orchestrator.VRAMManager") as mock:
        yield mock

@pytest.fixture
def mock_config():
    with patch("pipeline.orchestrator.Config") as mock:
        cfg = mock.return_value
        cfg.get.return_value = {} # Default
        cfg._data = {}
        yield mock

@pytest.fixture
def mock_graph_factory():
    # Patch where it is defined, because it is imported locally in run()
    with patch("pipeline.graph.create_agent_graph") as mock_factory:
        mock_app = MagicMock()
        mock_factory.return_value = mock_app
        
        # Simulate successful 3-step graph execution
        mock_app.invoke.return_value = {
            "task_id": "test_task",
            "current_step": "step3",
            "step_results": {
                "step1": {"status": "success"},
                "step2": {"raw_video_path": "outputs/test_task/raw.mp4"},
                "step3": {
                    "final_video_path": "outputs/test_task/final.mp4",
                    "thumbnail_path": "outputs/test_task/thumb.jpg"
                }
            },
            "final_video_path": "outputs/test_task/final.mp4",
            "thumbnail_path": "outputs/test_task/thumb.jpg",
            "reflection_history": ["Step 1 done", "Step 2 done", "Step 3 done"],
            "final_output": {
                "video_path": "outputs/test_task/final.mp4",
                "thumbnail_path": "outputs/test_task/thumb.jpg",
                "metadata": {}
            }
        }
        yield mock_factory

def test_pipeline_execution(mock_redis, mock_vram, mock_config, mock_graph_factory):
    # Init
    orchestrator = PipelineOrchestrator(
        task_id="test_task",
        image_paths=["img1.jpg"],
        prompt="test prompt",
        redis_mgr=mock_redis
    )
    
    # Run
    result = orchestrator.run()
    
    # Assert
    assert result["status"] == "success"
    assert result["task_id"] == "test_task"
    assert result["final_video"] == "outputs/test_task/final.mp4"
    assert "reflection_history" in result
    
    # Verify graph was compiled and invoked
    mock_graph_factory.assert_called_once()
    mock_graph_factory.return_value.invoke.assert_called_once()
