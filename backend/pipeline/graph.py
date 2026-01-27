from langgraph.graph import StateGraph, END
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

def route_video_qc(state: AgentState):
    """Routing logic based on Video QC decision"""
    decision = state.get("last_qc_decision", "proceed")
    if decision == "proceed":
        return "postprocess"
    elif decision == "retry":
        return "video_gen" # Loop back
    else:
        return "human_input"

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
    workflow.add_edge("human_input", END)
    
    app = workflow.compile()
    return app
