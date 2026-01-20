from langgraph.graph import StateGraph, END
from pipeline.agent_state import AgentState
from pipeline.nodes import (
    node_step0, node_step1, node_step1_5, node_step2, node_step3, 
    node_step4, node_step5, node_step6, node_step7_8, node_step9
)
from pipeline.supervisor import SupervisorAgent
from common.config import Config
from common.redis_manager import RedisManager

def create_agent_graph(task_id: str, redis_mgr: RedisManager):
    config = Config() # Load default config
    supervisor = SupervisorAgent(config, task_id, redis_mgr)
    
    workflow = StateGraph(AgentState)
    
    # 1. Add Nodes (Workers)
    workflow.add_node("step0", node_step0)
    workflow.add_node("step1", node_step1)
    workflow.add_node("step1_5", node_step1_5)
    workflow.add_node("step2", node_step2)
    workflow.add_node("step3", node_step3)
    workflow.add_node("step4", node_step4)
    workflow.add_node("step5", node_step5)
    workflow.add_node("step6", node_step6)
    workflow.add_node("step7_8", node_step7_8)
    workflow.add_node("step9", node_step9)
    
    # 2. Add Supervisor Node
    # Supervisor is not a standard node that modifies state directly in this pattern used here,
    # but rather a 'conditional edge' logic provider.
    # HOWEVER, to capture 'reflection_history' in state, we should make Supervisor a node 
    # OR update state in the conditional edge function (not recommended).
    # Best pattern: Worker -> Supervisor Node (reflects) -> Conditional Edge (routes)
    
    def supervisor_node(state: AgentState):
        decision = supervisor.reflect_and_route(state)
        
        # Update State with reflection and decision
        new_history = state.get("reflection_history", []) + [decision["thought"]]
        new_config = state.get("config", {}).copy()
        
        if decision.get("updated_config_patch"):
            # Deep merge logic simplified
            patch = decision["updated_config_patch"]
            new_config.update(patch)
        
        # Update retry count
        retries = state.get("retry_count", {}).copy()
        current_step = state.get("current_step")
        if decision["decision"] == "retry":
            retries[current_step] = retries.get(current_step, 0) + 1
        
        return {
            "next_step": decision["next_step"], # Used by conditional edge
            "reflection_history": [decision["thought"]], # Add to history
            "config": new_config,
            "retry_count": retries
        }

    workflow.add_node("supervisor", supervisor_node)
    
    # 3. Define Edges
    # Start -> Step 0
    workflow.set_entry_point("step0")
    
    # After every step, go to Supervisor to decide next
    steps = ["step0", "step1", "step1_5", "step2", "step3", "step4", "step5", "step6", "step7_8", "step9"]
    for step in steps:
        workflow.add_edge(step, "supervisor")
        
    # Supervisor -> Next Step (Conditional)
    def route_next(state: AgentState):
        next_step = state.get("next_step")
        current_step = state.get("current_step")
        
        if next_step == "end":
            return "end"
        
        if next_step == "retry":
             return current_step # Go back to same step
             
        # Normal progression or jump
        return next_step

    # Conditional mapping
    # We must explicitly list all reachable nodes from supervisor
    mapping = {k: k for k in steps}
    mapping["end"] = END
    # Retry maps to current step, but 'route_next' returns the name, so mapping covers it if name is valid
    
    workflow.add_conditional_edges(
        "supervisor",
        route_next,
        mapping
    )
    
    # Compile
    app = workflow.compile()
    return app
