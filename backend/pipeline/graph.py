from langgraph.graph import StateGraph, END
from pipeline.agent_state import AgentState
from pipeline.agent import AdGenAgent
from common.config import Config
from common.redis_manager import RedisManager
import logging
import json

logger = logging.getLogger(__name__)

def create_agent_graph(task_id: str, redis_mgr: RedisManager):
    """
    Create LangGraph workflow for Autonomous Agent.
    
    Graph structure:
        Start → Agent Node (Executor) → End
        
    The Agent Node runs a ReAct loop internally using LangChain's AgentExecutor.
    """
    
    # helper to extract tool outputs from agent execution
    def _parse_agent_output(agent_result: dict, state: AgentState) -> dict:
        updates = {}
        # Simple heuristic: Look at the intermediate steps to find key filenames
        # or rely on the agent to return a JSON in final answer (hard to guarantee).
        # Better: Rely on the fact that tools generate files in predictable paths.
        # We can scan the "intermediate_steps" to update state keys.
        
        steps = agent_result.get("intermediate_steps", [])
        for action, observation in steps:
            tool_name = action.tool
            try:
                # Observations are strings (JSON strings from our tools)
                if isinstance(observation, str) and observation.startswith("{"):
                    data = json.loads(observation)
                    
                    if tool_name == "vision_parsing_tool":
                        updates["vision_analysis"] = data
                    elif tool_name == "segmentation_tool":
                        updates["segmented_layers"] = data.get("segmented_layers")
                        updates["main_product_layer"] = data.get("main_product_layer")
                    elif tool_name == "video_generation_tool":
                        updates["raw_video_path"] = data.get("raw_video_path")
                    elif tool_name == "postprocess_tool":
                        updates["final_video_path"] = data.get("final_video_path")
                        updates["thumbnail_path"] = data.get("thumbnail_path")
                        updates["final_output"] = {
                            "video_path": data.get("final_video_path"),
                            "thumbnail_path": data.get("thumbnail_path"),
                            "metadata": data.get("metadata")
                        }
            except Exception:
                pass
                
        return updates

    def agent_node(state: AgentState):
        """
        Single Node: run the autonomous agent.
        """
        logger.info(f"[Graph] Executing Autonomous Agent Node")
        
        user_prompt = state.get("user_prompt", "")
        # Construct input for the agent
        agent_input = {
            "input": f"Create a video for task {state['task_id']}. " + 
                     (f"User Request: {user_prompt}" if user_prompt else ""),
            "chat_history": [] # TODO: Add memory if needed
        }
        
        agent = AdGenAgent(state["task_id"], redis_mgr)
        executor = agent.create_executor()
        
        try:
            # Run the agent (this runs the whole ReAct loop)
            result = executor.invoke(agent_input)
            
            # Parse results back into state
            updates = _parse_agent_output(result, state)
            updates["current_step"] = "completed"
            
            return updates
            
        except Exception as e:
            logger.error(f"[Graph] Agent failed: {e}")
            return {"error": str(e)}

    # Build graph
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", agent_node)
    workflow.set_entry_point("agent")
    workflow.add_edge("agent", END)
    
    app = workflow.compile()
    return app
