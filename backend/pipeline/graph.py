from langgraph.graph import StateGraph, END
from pipeline.agent_state import AgentState
from pipeline.supervisor import SupervisorAgent
from common.config import Config
from common.redis_manager import RedisManager
import logging

logger = logging.getLogger(__name__)

def create_agent_graph(task_id: str, redis_mgr: RedisManager):
    """
    Create LangGraph workflow for 3-step pipeline.
    
    Graph structure:
        step1 (Segmentation) → supervisor → step2 (Video Gen) → supervisor → step3 (Post-process) → supervisor → END
    
    Supervisor can:
        - Proceed to next step
        - Retry current step (with config patch)
        - Fail (abort pipeline)
    """
    config = Config.load()
    supervisor = SupervisorAgent(config, task_id, redis_mgr)
    
    # Import step classes
    from pipeline.step1_segmentation import Step1Segmentation
    from pipeline.step2_video_generation import Step2VideoGeneration
    from pipeline.step3_postprocess import Step3Postprocess
    from pipeline.vram_manager import VRAMManager
    from common.logger import TaskLogger
    
    # Initialize components
    task_logger = TaskLogger(task_id, redis_mgr)
    vram_mgr = VRAMManager(logger=task_logger, cfg=config)
    
    step1_executor = Step1Segmentation(vram_mgr)
    step2_executor = Step2VideoGeneration(vram_mgr)
    step3_executor = Step3Postprocess(vram_mgr)
    
    # Define node functions
    def node_step1(state: AgentState):
        """Execute Step 1: Segmentation"""
        logger.info(f"[Graph] Executing Step 1 - Segmentation")
        
        try:
            result = step1_executor.execute(
                task_id=state["task_id"],
                image_paths=state["image_paths"],
                config=state.get("config", {})
            )
            
            # Update state
            step_results = state.get("step_results", {})
            step_results["step1"] = result
            
            return {
                "current_step": "step1",
                "step_results": step_results,
                "segmented_layers": result.get("segmented_layers", []),
                "main_product_layer": result.get("main_product_layer", ""),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"[Graph] Step 1 failed: {e}")
            step_results = state.get("step_results", {})
            step_results["step1"] = {"error": str(e)}
            
            return {
                "current_step": "step1",
                "step_results": step_results,
                "error": str(e)
            }
    
    def node_step2(state: AgentState):
        """Execute Step 2: Video Generation"""
        logger.info(f"[Graph] Executing Step 2 - Video Generation")
        
        try:
            result = step2_executor.execute(
                task_id=state["task_id"],
                main_product_layer=state.get("main_product_layer", ""),
                user_prompt=state.get("user_prompt", ""),
                config=state.get("config", {})
            )
            
            # Update state
            step_results = state.get("step_results", {})
            step_results["step2"] = result
            
            return {
                "current_step": "step2",
                "step_results": step_results,
                "raw_video_path": result.get("raw_video_path", ""),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"[Graph] Step 2 failed: {e}")
            step_results = state.get("step_results", {})
            step_results["step2"] = {"error": str(e)}
            
            return {
                "current_step": "step2",
                "step_results": step_results,
                "error": str(e)
            }
    
    def node_step3(state: AgentState):
        """Execute Step 3: Post-processing"""
        logger.info(f"[Graph] Executing Step 3 - Post-processing")
        
        try:
            result = step3_executor.execute(
                task_id=state["task_id"],
                raw_video_path=state.get("raw_video_path", ""),
                config=state.get("config", {})
            )
            
            # Update state
            step_results = state.get("step_results", {})
            step_results["step3"] = result
            
            return {
                "current_step": "step3",
                "step_results": step_results,
                "final_video_path": result.get("final_video_path", ""),
                "thumbnail_path": result.get("thumbnail_path", ""),
                "final_output": {
                    "video_path": result.get("final_video_path", ""),
                    "thumbnail_path": result.get("thumbnail_path", ""),
                    "metadata": result.get("metadata", {})
                },
                "error": None
            }
            
        except Exception as e:
            logger.error(f"[Graph] Step 3 failed: {e}")
            step_results = state.get("step_results", {})
            step_results["step3"] = {"error": str(e)}
            
            return {
                "current_step": "step3",
                "step_results": step_results,
                "error": str(e)
            }
    
    def supervisor_node(state: AgentState):
        """
        Supervisor node: Reflects on step result and routes to next step.
        """
        logger.info(f"[Graph] Executing Supervisor")
        
        decision = supervisor.reflect_and_route(state)
        
        # Extract decision fields
        thought = decision.get("reflection", decision.get("thought", ""))
        next_step = decision.get("next_step", "end")
        config_patch = decision.get("config_patch", decision.get("updated_config_patch", {}))
        
        # Update config if patch provided
        new_config = state.get("config", {}).copy()
        if config_patch:
            # Deep merge (simplified)
            for key, value in config_patch.items():
                if isinstance(value, dict) and key in new_config:
                    new_config[key].update(value)
                else:
                    new_config[key] = value
        
        # Update retry count if retrying
        retries = state.get("retry_count", {}).copy()
        current_step = state.get("current_step", "")
        if decision.get("decision") == "retry":
            retries[current_step] = retries.get(current_step, 0) + 1
        
        return {
            "next_step": next_step,
            "reflection_history": [thought],
            "config": new_config,
            "retry_count": retries
        }
    
    # Build graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("step1", node_step1)
    workflow.add_node("step2", node_step2)
    workflow.add_node("step3", node_step3)
    workflow.add_node("supervisor", supervisor_node)
    
    # Set entry point
    workflow.set_entry_point("step1")
    
    # Add edges: each step goes to supervisor
    workflow.add_edge("step1", "supervisor")
    workflow.add_edge("step2", "supervisor")
    workflow.add_edge("step3", "supervisor")
    
    # Conditional routing from supervisor
    def route_next(state: AgentState):
        next_step = state.get("next_step", "end")
        
        if next_step == "end":
            return "end"
        
        # Valid next steps
        if next_step in ["step1", "step2", "step3"]:
            return next_step
        
        # Default to end if invalid
        logger.warning(f"[Graph] Invalid next_step: {next_step}, defaulting to END")
        return "end"
    
    workflow.add_conditional_edges(
        "supervisor",
        route_next,
        {
            "step1": "step1",
            "step2": "step2",
            "step3": "step3",
            "end": END
        }
    )
    
    # Compile graph
    app = workflow.compile()
    return app
