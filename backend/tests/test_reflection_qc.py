import pytest
from unittest.mock import MagicMock, patch
import json
from pipeline.tools import reflection_tool
from common.redis_manager import RedisManager

# Mock response chunks for streaming simulation
MOCK_STREAMING_CHUNKS = [
    MagicMock(content="흠"), 
    MagicMock(content=","), 
    MagicMock(content=" "), 
    MagicMock(content="햄"), 
    MagicMock(content="버"), 
    MagicMock(content="거"), 
    MagicMock(content=" "), 
    MagicMock(content="윗"), 
    MagicMock(content="부"), 
    MagicMock(content="분"), 
    MagicMock(content="이"), 
    MagicMock(content=" "), 
    MagicMock(content="잘"), 
    MagicMock(content="렸"), 
    MagicMock(content="습"), 
    MagicMock(content="니"), 
    MagicMock(content="다"), 
    MagicMock(content="."),
    MagicMock(content='```json\n{"decision": "retry", "reflection": "잘림 발생", "config_patch": {"segmentation": {"resolution": 1280}}}\n```')
]

@pytest.fixture
def mock_redis():
    with patch("pipeline.tools.RedisManager.from_env") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_llm():
    with patch("pipeline.tools.ChatOpenAI") as mock_cls:
        mock_instance = MagicMock()
        # Mocking the stream method
        mock_instance.stream.return_value = MOCK_STREAMING_CHUNKS
        # Mocking the invoke method (fallback)
        mock_instance.invoke.return_value = MagicMock(content=MOCK_STREAMING_CHUNKS[-1].content)
        
        mock_cls.return_value = mock_instance
        yield mock_instance

def test_reflection_tool_streaming_and_qc(mock_redis, mock_llm):
    """
    Test that reflection_tool:
    1. Streams thoughts to Redis line-by-line (or chunk-by-chunk).
    2. Correctly parses the JSON decision from the accumulated content.
    3. Handles the 'retry' decision logic.
    """
    task_id = "test-task-123"
    step_name = "segmentation_tool"
    result_summary = "Image segmented."
    
    # Execute the tool using KEYWORD arguments to avoid BaseTool positional arg issues
    result_json = reflection_tool(
        task_id=task_id, 
        step_name=step_name, 
        result_summary=result_summary
    )
    
    # 1. Verify Streaming to Redis
    # We expect multiple publish calls, one for each "thought" chunk
    assert mock_redis.publish.call_count >= len(MOCK_STREAMING_CHUNKS)
    
    # Check if the correct message structure was sent
    # We check one of the middle calls
    call_args = mock_redis.publish.call_args_list[3] # Index 3 is '햄'
    channel, message = call_args[0]
    
    assert channel == f"task:{task_id}"
    assert message["type"] == "thought_stream"
    assert message["content"] == "햄"
    
    # 2. Verify Return Value (QC Decision)
    result = json.loads(result_json)
    assert result["decision"] == "retry"
    assert result["config_patch"]["segmentation"]["resolution"] == 1280
    
    print("\n✅ Reflection Tool Streaming & QC Test Passed!")
