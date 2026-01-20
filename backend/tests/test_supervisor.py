import pytest
from unittest.mock import MagicMock, patch
from pipeline.supervisor import SupervisorAgent
from common.config import Config
from common.redis_manager import RedisManager

@pytest.fixture
def mock_redis():
    return MagicMock(spec=RedisManager)

@pytest.fixture
def mock_config():
    return MagicMock(spec=Config)

@pytest.fixture
def supervisor(mock_config, mock_redis):
    with patch("pipeline.supervisor.ChatOpenAI"):
        return SupervisorAgent(mock_config, "test_task", mock_redis)

def test_get_default_next(supervisor):
    assert supervisor._get_default_next("start") == "step1"
    assert supervisor._get_default_next("step1") == "step2"
    assert supervisor._get_default_next("step2") == "step3"
    assert supervisor._get_default_next("step3") == "end"
    assert supervisor._get_default_next("end") == "end"
    assert supervisor._get_default_next("unknown") == "end"

@patch("pipeline.supervisor.ChatPromptTemplate")
@patch("pipeline.supervisor.JsonOutputParser")
def test_reflect_and_route_success(mock_parser, mock_template, supervisor):
    # Mock LLM chain
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {
        "reflection": "High quality result",
        "decision": "proceed",
        "next_step": "step2"
    }
    
    # In supervisor.py, chain is (prompt | llm | parser)
    # This is tricky to patch directly because of the | operator.
    # Instead, let's patch the whole chain invoke.
    with patch("langchain_core.runnables.base.RunnableBinding.invoke", return_value={
                "reflection": "High quality result",
                "decision": "proceed",
                "next_step": "step2"
            }) as mock_invoke: # This is still hard.
        pass

    # Alternative: Mock the chain attribute if we can find where it's assigned.
    # But it's defined inside reflect_and_route.
    # Let's mock ChatOpenAI.invoke or similar? No, the chain is what's called.
    
    # Actually, SupervisorAgent.llm is what we need to control.
    supervisor.llm.invoke = MagicMock(return_value=MagicMock(content='{"decision": "proceed", "next_step": "step2"}'))
    
    state = {
        "current_step": "step1",
        "step_results": {"step1": {"status": "success"}},
        "retry_count": {}
    }
    
    # Let's just mock the whole chain creation and invocation
    with patch("pipeline.supervisor.ChatPromptTemplate.from_messages") as mock_prompt_fm:
        mock_chain = MagicMock()
        mock_prompt_fm.return_value.__or__.return_value.__or__.return_value = mock_chain
        mock_chain.invoke.return_value = {
            "reflection": "Ok",
            "decision": "proceed",
            "next_step": "step2"
        }
        
        result = supervisor.reflect_and_route(state)
        assert result["decision"] == "proceed"
        assert result["next_step"] == "step2"

def test_reflect_and_route_error_fallback(supervisor):
    # Simulate exception during LLM invoke
    with patch.object(supervisor.llm, "invoke", side_effect=Exception("LLM Fail")):
        result = supervisor.reflect_and_route({"current_step": "step1"})
        assert result["decision"] == "proceed"
        assert result["next_step"] == "step2"
        assert "Supervisor error" in result["reflection"]
