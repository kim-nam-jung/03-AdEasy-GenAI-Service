import pytest
from unittest.mock import MagicMock, patch
from pipeline.agent import AdGenAgent
from langgraph.graph import StateGraph

# Mock LangChain components since we don't want real OpenAI calls
@pytest.fixture
def mock_agent_executor():
    with patch("pipeline.agent.ChatOpenAI") as mock_llm_cls, \
         patch("pipeline.agent.create_openai_tools_agent") as mock_agent_factory, \
         patch("pipeline.agent.AgentExecutor") as mock_executor_cls:

        mock_llm_cls.return_value = MagicMock()
        mock_executor = MagicMock()
        mock_executor_cls.return_value = mock_executor

        # Simulate a successful run returning intermediate steps
        mock_executor.invoke.return_value = {
            "output": "Finished video generation",
            "intermediate_steps": [
                (MagicMock(tool="vision_parsing_tool"), '{"product": "shoe"}'),
                (MagicMock(tool="segmentation_tool"), '{"segmented_layers": ["layer.png"]}'),
                (MagicMock(tool="postprocess_tool"), '{"final_video_path": "vid.mp4"}')
            ]
        }

        yield mock_executor

def test_agent_initialization(mock_redis_manager):
    """Test that agent initializes correctly."""
    agent = AdGenAgent("task-123", mock_redis_manager)
    assert agent.task_id == "task-123"
    assert agent.redis_mgr == mock_redis_manager

def test_agent_execution_flow(mock_redis_manager, mock_agent_executor, mock_agent_tools):
    """
    Test the full agent execution flow.
    Using mock_agent_executor to simulate LLM deciding to call tools.
    """
    agent = AdGenAgent("task-123", mock_redis_manager)
    executor = agent.create_executor()
    
    # Run
    result = executor.invoke({"input": "Make a video"})
    
    # Assertions
    assert result["output"] == "Finished video generation"
    assert len(result["intermediate_steps"]) == 3
    # Verify we mocked the tools passed to executor
    # (In reality, AgentExecutor calls the tools, but here we mock the executor itself,
    # so we are just testing that create_executor sets things up and invoke returns what we expect)

def test_graph_integration(mock_redis_manager, mock_agent_executor):
    """
    Test that graph.py correctly wraps the agent.
    This requires importing create_agent_graph and mocking AdGenAgent inside it.
    """
    from pipeline.graph import create_agent_graph
    
    with patch("pipeline.graph.AdGenAgent") as MockAgentCls:
        mock_agent_instance = MockAgentCls.return_value
        mock_agent_instance.create_executor.return_value = mock_agent_executor
        
        app = create_agent_graph("task-123", mock_redis_manager)
        
        # Invoke the graph
        initial_state = {"task_id": "task-123", "image_paths": ["img.jpg"]}
        final_state = app.invoke(initial_state)
        
        # Check if state was updated from intermediate steps
        assert final_state["current_step"] == "completed"
        # Since our mock executor returned "postprocess_tool" step with "final_video_path",
        # the _parse_agent_output logic in graph.py should pick it up.
        assert final_state["final_video_path"] == "vid.mp4"
