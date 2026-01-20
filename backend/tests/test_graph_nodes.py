import pytest
from unittest.mock import MagicMock, patch
from pipeline.graph import create_agent_graph
from pipeline.agent_state import AgentState

@pytest.fixture
def mock_redis():
    return MagicMock()

def test_graph_step1_node_coverage(mock_redis):
    # This test hits the node_step1 code by invoking the graph and checking for step1 result
    with patch("pipeline.graph.SupervisorAgent") as mock_sup, \
         patch("common.logger.TaskLogger") as mock_logger, \
         patch("pipeline.step1_segmentation.Step1Segmentation") as mock_s1, \
         patch("pipeline.step2_video_generation.Step2VideoGeneration") as mock_s2, \
         patch("pipeline.step3_postprocess.Step3Postprocess") as mock_s3:
        
        mock_s1.return_value.execute.return_value = {"segmented_layers": ["L1"]}
        mock_sup.return_value.reflect_and_route.return_value = {
            "decision": "proceed",
            "next_step": "end"
        }
        
        app = create_agent_graph("test_task", mock_redis)
        
        initial_state = {
            "task_id": "test",
            "image_paths": ["img.jpg"],
            "step_results": {}
        }
        
        final_state = app.invoke(initial_state)
        assert "step1" in final_state["step_results"]
        assert final_state["segmented_layers"] == ["L1"]

def test_graph_step2_node_coverage(mock_redis):
    with patch("pipeline.graph.SupervisorAgent") as mock_sup, \
         patch("common.logger.TaskLogger") as mock_logger, \
         patch("pipeline.step1_segmentation.Step1Segmentation") as mock_s1, \
         patch("pipeline.step2_video_generation.Step2VideoGeneration") as mock_s2, \
         patch("pipeline.step3_postprocess.Step3Postprocess") as mock_s3:
        
        mock_s1.return_value.execute.return_value = {"segmented_layers": ["L1"]}
        mock_s2.return_value.execute.return_value = {"raw_video_path": "raw.mp4"}
        
        # Route: step1 -> supervisor -> step2 -> supervisor -> end
        side_effects = [
            {"decision": "proceed", "next_step": "step2"},
            {"decision": "proceed", "next_step": "end"}
        ]
        mock_sup.return_value.reflect_and_route.side_effect = side_effects
        
        app = create_agent_graph("test", mock_redis)
        final_state = app.invoke({"task_id": "t", "image_paths": ["i"], "step_results": {}})
        
        assert "step2" in final_state["step_results"]
        assert final_state["raw_video_path"] == "raw.mp4"

def test_graph_step3_node_coverage(mock_redis):
    with patch("pipeline.graph.SupervisorAgent") as mock_sup, \
         patch("common.logger.TaskLogger") as mock_logger, \
         patch("pipeline.step1_segmentation.Step1Segmentation") as mock_s1, \
         patch("pipeline.step2_video_generation.Step2VideoGeneration") as mock_s2, \
         patch("pipeline.step3_postprocess.Step3Postprocess") as mock_s3:
        
        mock_s1.return_value.execute.return_value = {"status": "ok"}
        mock_s2.return_value.execute.return_value = {"raw_video_path": "raw.mp4"}
        mock_s3.return_value.execute.return_value = {
            "final_video_path": "final.mp4",
            "thumbnail_path": "th.jpg"
        }
        
        side_effects = [
            {"decision": "proceed", "next_step": "step2"},
            {"decision": "proceed", "next_step": "step3"},
            {"decision": "proceed", "next_step": "end"}
        ]
        mock_sup.return_value.reflect_and_route.side_effect = side_effects
        
        app = create_agent_graph("test", mock_redis)
        final_state = app.invoke({"task_id": "t", "image_paths": ["i"], "step_results": {}})
        assert "step3" in final_state["step_results"]
        assert final_state["final_video_path"] == "final.mp4"

