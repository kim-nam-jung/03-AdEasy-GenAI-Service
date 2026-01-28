from langgraph.graph import StateGraph, END
from pipeline.checkpointer import get_checkpointer
from pipeline.agent_state import AgentState
# RedisManager is needed for some internal tool inits but passed effectively via wrappers
# so we don't need to pass it explicitly to create_agent_graph unless we want to init initial state with it.

from pipeline.node_utils import (
    segmentation_node, qc_segmentation_node,
    video_gen_node, qc_video_node,
    postprocess_node, human_input_node
)

def route_segmentation_qc(state: AgentState):
    """Routing logic based on Segmentation QC decision"""
    decision = state.get("last_qc_decision", "proceed")
    if decision == "proceed":
        return "video_gen"
    elif decision == "retry":
        return "segmentation" # Loop back
    else:
        return "human_input"

# Note: Ideally we set 'failed_step' in state too. 
# Since we can't in edge, we assume the node preceding set it or we infer.
# Let's try to infer in route_after_human_input or trust the flow.


def route_video_qc(state: AgentState):
    """Routing logic based on Video QC decision"""
    decision = state.get("last_qc_decision", "proceed")
    if decision == "proceed":
        return "postprocess"
    elif decision == "retry":
        return "video_gen" # Loop back
    else:
        return "human_input"

def route_after_human_input(state: AgentState):
    feedback = state.get("human_feedback")
    failed_step = state.get("failed_step", "segmentation") # default fallback
    
    # If using feedback to determine routing directly:
    # However, logic is inside human_input_node which sets 'last_qc_decision'
    # Wait, human_input_node processes feedback and returns state updates.
    # The updated state is then used here.
    
    last_decision = state.get("last_qc_decision")
    if last_decision == "retry":
        # We need to know WHICH step failed.
        # Ideally, 'failed_step' is set when entering human_input?
        # Or we infer it from last_qc_decision logic?
        # Actually simplest way: when QC fails to human_input, we are at a specific stage.
        # But here we are routing OUT of human_input.
        # We can store 'failed_step' in state during QC failure routing or assume segmentation for now if missing.
        # Let's improve QC routing to set failed_step if possible, OR just check where we came from? 
        # LangGraph state persists, so we can check `failed_step` if we set it.
        # Let's update route_segmentation_qc/route_video_qc to set failed_step ideally?
        # Currently routing functions are pure conditional edges, they don't update state.
        # So we might need to rely on `failed_step` being present or default to logic.
        
        # NOTE: Since we cannot easily update state in conditional_edge function, 
        # we rely on the fact that the 'human_input_node' doesn't really know where to go back unless we tell it.
        # But wait, route_after_human_input has access to the state.
        # If we just came from human_input, we look at where we were.
        # Actually, let's keep it simple: We route based on which step failed.
        # But we don't track 'failed_step' yet in QC nodes.
        # Fix: We will just try to infer or route to segmentation as default safe retry.
        # But wait, if video failed, we should retry video.
        # Can we check if 'raw_video_path' exists? If so, maybe video gen failed?
        # Let's use a simpler heuristic for now or fix QC nodes later.
        # Actually, the user plan says: `failed_step = state.get("failed_step", "segmentation")`.
        # This implies we expect `failed_step` to be in state.
        # Let's assume it IS there (we added it to AgentState).
        # But we need to make sure it gets populated.
        # Since we can't easily populate it in edge routing, 
        # let's populate it in QC nodes BEFORE returning "human_input" decision?
        # Ah, QC node returns "last_qc_decision": "human_input" doesn't work directly if we map it to string.
        # QC Nodes returns dict.
        # We'll update logic: QC nodes return last_qc_decision.
        # If decision is "human_input", we should also set "failed_step".
        return failed_step
    elif last_decision == "proceed":
        # If forced to proceed
        if failed_step == "segmentation":
             return "video_gen"
        elif failed_step == "video_gen":
             return "postprocess"
    
    return END

def create_agent_graph(task_id: str):
    """
    Constructs the LangGraph StateMachine for the AdGen Pipeline.
    """
    workflow = StateGraph(AgentState)
    
    # Define Nodes
    workflow.add_node("segmentation", segmentation_node)
    workflow.add_node("qc_segmentation", qc_segmentation_node)
    workflow.add_node("video_gen", video_gen_node)
    workflow.add_node("qc_video", qc_video_node)
    workflow.add_node("postprocess", postprocess_node)
    workflow.add_node("human_input", human_input_node)
    
    # Define Entry Point
    workflow.set_entry_point("segmentation")
    
    # Define Edges
    workflow.add_edge("segmentation", "qc_segmentation")
    
    # Conditional Routing for Segmentation QC
    workflow.add_conditional_edges(
        "qc_segmentation",
        route_segmentation_qc,
        {
            "video_gen": "video_gen",
            "segmentation": "segmentation",
            "human_input": "human_input"
        }
    )
    
    workflow.add_edge("video_gen", "qc_video")
    
    # Conditional Routing for Video QC
    workflow.add_conditional_edges(
        "qc_video",
        route_video_qc,
        {
            "postprocess": "postprocess",
            "video_gen": "video_gen",
            "human_input": "human_input"
        }
    )
    
    workflow.add_edge("postprocess", END)
    workflow.add_conditional_edges(
        "human_input",
        route_after_human_input,
        {"segmentation": "segmentation", "video_gen": "video_gen", "end": END}
    )
    
    app = workflow.compile(
        checkpointer=get_checkpointer(),
        interrupt_before=["human_input"]
    )
    return app
