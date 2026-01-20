import pytest
from unittest.mock import MagicMock, patch
from pipeline.graph import create_agent_graph
from pipeline.agent_state import AgentState
from common.redis_manager import RedisManager

@pytest.fixture
def mock_redis():
    mock = MagicMock(spec=RedisManager)
    mock.client = MagicMock()
    return mock

@pytest.fixture
def mock_steps():
    # Mock the NODE functions imported in pipeline.graph
    with patch("pipeline.graph.node_step0") as s0, \
         patch("pipeline.graph.node_step1") as s1, \
         patch("pipeline.graph.node_step1_5") as s1_5, \
         patch("pipeline.graph.node_step2") as s2, \
         patch("pipeline.graph.node_step3") as s3, \
         patch("pipeline.graph.node_step4") as s4, \
         patch("pipeline.graph.node_step5") as s5, \
         patch("pipeline.graph.node_step6") as s6, \
         patch("pipeline.graph.node_step7_8") as s7_8, \
         patch("pipeline.graph.node_step9") as s9:
        
        # Nodes return a dict update for the state
        s0.return_value = {"current_step": "step0"}
        s1.return_value = {"current_step": "step1"}
        s1_5.return_value = {"current_step": "step1_5"}
        s2.return_value = {"current_step": "step2"}
        s3.return_value = {"current_step": "step3"}
        s4.return_value = {"current_step": "step4"}
        s5.return_value = {"current_step": "step5"}
        s6.return_value = {"current_step": "step6"}
        s7_8.return_value = {"current_step": "step7_8"}
        s9.return_value = {"current_step": "step9"}
        
        yield {
            "s0": s0, "s1": s1, "s1_5": s1_5, "s2": s2, "s3": s3, 
            "s4": s4, "s5": s5, "s6": s6, "s7_8": s7_8, "s9": s9
        }

@pytest.fixture
def mock_supervisor():
    with patch("pipeline.graph.SupervisorAgent") as mock:
        agent = mock.return_value
        # Default behavior: always proceed
        agent.reflect_and_route.return_value = {
            "thought": "Looks good",
            "decision": "proceed",
            "next_step": "next", # Will be ignored by default logic if we mock logic? 
            # Wait, supervisor_node logic uses this.
        }
        
        # We need to simulate dynamic next_step based on input
        # But for simple test, let's mock reflect_and_route side effect
        yield agent

def test_graph_execution_happy_path(mock_redis, mock_steps, mock_supervisor):
    # Setup Supervisor to guide flow
    # Since we use a real graph, we must ensure 'next_step' returned by reflect matches graph expectation
    # But our graph defines logic: steps -> supervisor -> conditional
    # The supervisor node logic calls reflect_and_route.
    # We need to ensure reflect_and_route returns the CORRECT next step name for each stage.
    
    # Let's mock side_effect to return correct next step based on state
    def side_effect(state):
        step = state.get("current_step")
        transitions = {
            "step0": "step1",
            "step1": "step1_5",
            "step1_5": "step2",
            "step2": "step3",
            "step3": "step4",
            "step4": "step5",
            "step5": "step6",
            "step6": "step7_8",
            "step7_8": "step9",
            "step9": "end"
        }
        next_s = transitions.get(step, "end")
        return {
            "thought": f"Finished {step}, going to {next_s}",
            "decision": "proceed",
            "next_step": next_s
        }
    
    mock_supervisor.reflect_and_route.side_effect = side_effect
    
    # Build Graph
    app = create_agent_graph("test_task", mock_redis)
    
    # Invoke
    initial_state = {
        "task_id": "test_task",
        "user_prompt": "test",
        "image_paths": ["img.png"],
        "config": {},
        "current_step": "start", # Logic might need tweak if entry point is step0
        "step_results": {}
    }
    
    # Run
    # app.invoke(initial_state) 
    # invoke runs until END
    
    final_state = app.invoke(initial_state)
    
    # Verify execution
    assert final_state["current_step"] == "step9" # Last recorded step
    assert "Finished step9" in final_state["reflection_history"][-1]
    
    # Verify all steps called
    for step_mock in mock_steps.values():
        step_mock.assert_called()

def test_graph_retry_logic(mock_redis, mock_steps, mock_supervisor):
    # Simulate partial failure and retry
    # step9 fails once, then succeeds
    
    # Mock Step 9 to fail first time
    # This is hard because steps are stateless mocks.
    # We can use side_effect on Step 9 to return low score first?
    # But reflect_and_route decides retry.
    
    mock_steps["s9"].return_value = {"identity_score": 0.5, "passed": False}
    
    # Mock Supervisor to Retry Step 9 once
    # We need a stateful side effect for supervisor
    
    call_counts = {"step9": 0}
    
    def supervisor_logic(state):
        step = state.get("current_step")
        if step == "step9":
            call_counts["step9"] += 1
            if call_counts["step9"] == 1:
                return {
                    "thought": "Score low, retrying...",
                    "decision": "retry",
                    "next_step": "retry",
                    "updated_config_patch": {"threshold": 0.5}
                }
            else:
                return {
                    "thought": "Retry done, proceeding",
                    "decision": "proceed",
                    "next_step": "end"
                }
        
        # Default flow
        transitions = {
            "step0": "step1", "step1": "step1_5", "step1_5": "step2",
            "step2": "step3", "step3": "step4", "step4": "step5",
            "step5": "step6", "step6": "step7_8", "step7_8": "step9"
        }
        return {
            "thought": "ok",
            "decision": "proceed",
            "next_step": transitions.get(step, "end")
        }

    mock_supervisor.reflect_and_route.side_effect = supervisor_logic
    
    # Build
    app = create_agent_graph("test_task_retry", mock_redis)
    
    initial_state = {
        "task_id": "test_task",
        "user_prompt": "test",
        "image_paths": ["img.png"],
        "config": {},
        "step_results": {}
    }
    
    final_state = app.invoke(initial_state)
    
    # Verify Retry
    assert final_state["retry_count"].get("step9") == 1
    assert final_state["config"].get("threshold") == 0.5 # Config patched
    assert "Score low, retrying..." in final_state["reflection_history"]
