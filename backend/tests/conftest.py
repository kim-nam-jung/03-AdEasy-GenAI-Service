import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add backend to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from 'common' or 'backend.common' depending on how pytest is run
try:
    from common.redis_manager import RedisManager
except ImportError:
    # Fallback if running from outside backend
    from backend.common.redis_manager import RedisManager

@pytest.fixture
def mock_redis():
    with patch("redis.from_url") as mock:
        yield mock

@pytest.fixture
def mock_redis_manager(mock_redis):
    mgr = MagicMock(spec=RedisManager)
    mgr.client = mock_redis
    mgr.set_status = MagicMock(return_value={})
    mgr.get_status = MagicMock(return_value=None)
    mgr.publish = MagicMock(return_value=1)
    yield mgr

@pytest.fixture
def mock_config():
    with patch("common.config.Config.load") as mock:
        cfg = MagicMock()
        cfg.get.return_value = {}
        mock.return_value = cfg
        yield cfg

@pytest.fixture
def mock_agent_tools():
    """Mock the tools to avoid actual GPU/API calls."""
    with patch("pipeline.agent.vision_parsing_tool") as vision, \
         patch("pipeline.agent.segmentation_tool") as seg, \
         patch("pipeline.agent.video_generation_tool") as video, \
         patch("pipeline.agent.postprocess_tool") as post, \
         patch("pipeline.agent.reflection_tool") as reflect, \
         patch("pipeline.agent.ask_human_tool") as human:
        
        vision.invoke.return_value = '{"product_name": "shoe", "suggested_video_prompt": "rotating shoe"}'
        seg.invoke.return_value = '{"segmented_layers": ["layer0.png"], "main_product_layer": "layer0.png"}'
        video.invoke.return_value = '{"raw_video_path": "video.mp4"}'
        post.invoke.return_value = '{"final_video_path": "final_video.mp4", "thumbnail_path": "thumb.jpg", "metadata": {}}'
        reflect.invoke.return_value = '{"decision": "proceed", "reflection": "Good job"}'
        human.invoke.return_value = "Guidance requested"
        
        yield {
            "vision": vision,
            "seg": seg,
            "video": video,
            "post": post,
            "reflect": reflect,
            "human": human
        }
