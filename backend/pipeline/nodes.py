from typing import Dict, Any
from pipeline.agent_state import AgentState
from common.config import Config
from common.logger import get_logger
from common.paths import TaskPaths
from common.redis_manager import RedisManager

# Use the adapter functions defined/verified previously
from pipeline.step0_preprocessing import step0_preprocessing
from pipeline.step1_understanding import step1_understanding
from pipeline.step1_5_prompt_expansion import step1_5_prompt_expansion
from pipeline.step2_planning import step2_planning
from pipeline.step3_control import step3_control
from pipeline.step4_generation import step4_generation
from pipeline.step5_video import step5_video
from pipeline.step6_postprocess import step6_postprocess
from pipeline.step7_8_assembly import step7_8_assembly
from pipeline.step9_validation import step9_validation

logger = get_logger("NodeWrapper")

def get_node(step_func, step_name):
    """
    Factory to create a graph node from a step function.
    Matches the signature expected by LangGraph (state -> state).
    """
    def node(state: AgentState) -> Dict[str, Any]:
        task_id = state["task_id"]
        # Reconstruct dependencies
        # In a real app, these might be singletons or passed differently.
        # Here we create lightweight instances or assume state has what's needed.
        
        # Config is in state
        cfg_dict = state.get("config", {})
        # Reconstruct Config object (assuming it can take dict, or we patch it)
        # Ideally we passed Config object in state, but TypedDict doesn't validate types at runtime.
        # Let's assume state['config'] is a Dict, but step functions expect Config object.
        # We need a quick adapter or ensure state['config'] IS the object.
        # For this implementation, let's assume Config is compatible or we mock it.
        
        # Actually, Config is a class in common/config.py. Let's try to use it.
        # cfg = Config(None)  <-- Removed
        # Manually inject dict into cfg if possible, or just pass the dict 
        # if we modify steps to accept dict.
        # Our previous refactors kept 'cfg: Config' type hint.
        # Python duck typing might save us if we just pass a class-like wrapper.
        
        class ConfigWrapper:
            def __init__(self, data): self.data = data
            def get(self, key, default=None): return self.data.get(key, default)
            def __getitem__(self, key): return self.data[key]
            
        cfg_wrapper = ConfigWrapper(cfg_dict)
        
        # Paths
        paths = TaskPaths.from_repo(task_id) # Todo: verify output dir
        
        # Redis (Optional mostly for logging status, but Supervisor handles stream)
        # We don't necessarily need Redis inside the nodes if Supervisor handles flow.
        # But existing steps use it to log status? 
        # Orchestrator used to update status. Nodes just do work.
        # Existing steps usually take 'logger', 'paths', 'cfg'.
        
        # Previous results
        results = state.get("step_results", {})
        
        # Merge all previous results into kwargs for the step
        # This matches how orchestrator passed `**result`
        step_kwargs = {}
        for k, v in results.items():
            if isinstance(v, dict):
                step_kwargs.update(v)
        
        # Special inputs
        image_paths = state.get("image_paths", [])
        prompt = state.get("user_prompt", "")
        
        logger.info(f"Executing Node: {step_name}")
        
        try:
            # Execute Step
            output = step_func(
                task_id=task_id,
                paths=paths,
                logger=logger,
                cfg=cfg_wrapper,
                image_paths=image_paths,
                prompt=prompt,
                **step_kwargs # Pass accumulated results
            )
            
            # Update State
            new_results = state["step_results"].copy()
            new_results[step_name] = output # Store per-step output
            
            # Also merge into a flat structure if needed, or just keep per-step.
            # Our supervisor looks at 'step_results[current_step]'
            
            return {
                "step_results": new_results,
                "current_step": step_name,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Node {step_name} Failed: {e}")
            return {
                "error": str(e),
                "current_step": step_name
            }

    return node

# Create Nodes
node_step0 = get_node(step0_preprocessing, "step0")
node_step1 = get_node(step1_understanding, "step1")
node_step1_5 = get_node(step1_5_prompt_expansion, "step1_5")
node_step2 = get_node(step2_planning, "step2")
node_step3 = get_node(step3_control, "step3")
node_step4 = get_node(step4_generation, "step4")
node_step5 = get_node(step5_video, "step5")
node_step6 = get_node(step6_postprocess, "step6")
node_step7_8 = get_node(step7_8_assembly, "step7_8")
node_step9 = get_node(step9_validation, "step9")
