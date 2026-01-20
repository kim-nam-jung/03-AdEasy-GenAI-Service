from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from common.config import Config
from pipeline.agent_state import AgentState
from common.callback import RedisStreamingCallback
from common.redis_manager import RedisManager

class SupervisorAgent:
    """
    Supervisor for 3-step pipeline.
    Analyzes step results and decides: proceed, retry, or fail.
    Can patch configuration for retries.
    """
    def __init__(self, cfg: Config, task_id: str, redis_mgr: RedisManager):
        self.cfg = cfg
        self.task_id = task_id
        # Initialize GPT-4o for reflection
        import os
        openai_key = os.getenv("OPENAI_API_KEY")
        
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            openai_api_key=openai_key,
            streaming=True,
            callbacks=[RedisStreamingCallback(redis_mgr, task_id)]
        )
        
    def reflect_and_route(self, state: AgentState) -> Dict[str, Any]:
        """
        Analyze step result and decide next action.
        
        Returns:
            {
                "thought": str,
                "decision": "proceed" | "retry" | "fail",
                "next_step": "step1" | "step2" | "step3" | "end",
                "config_patch": {...}  # Optional config updates for retry
            }
        """
        current_step = state.get("current_step", "start")
        step_results = state.get("step_results", {})
        last_result = step_results.get(current_step, {})
        retry_count = state.get("retry_count", {}).get(current_step, 0)
        
        # System prompt for 3-step pipeline
        system_prompt = """
You are the Supervisor for a 3-step video generation pipeline:

**Pipeline**: Step 1 (Segmentation) → Step 2 (Video Generation) → Step 3 (Post-processing)

**Current Step**: {current_step}
**Result Summary**: {result_summary}
**Current Config**: {config}
**Retry Count**: {retry_count}

**Your Tasks**:
1. **Reflection**: Analyze the quality of the step result
2. **Decision**: Choose one of:
   - "proceed": Move to next step (good quality)
   - "retry": Re-run current step (low quality, retry_count < 2)
   - "fail": Abort pipeline (critical error or max retries)
3. **Routing**: Determine next_step
4. **Config Patch**: (Only for retry) Adjust parameters to improve quality

**Quality Criteria**:
- Step 1: Clean segmentation, no background noise
- Step 2: Smooth motion, product stays centered
- Step 3: No artifacts from interpolation/upscaling

**Adjustable Parameters**:
- Step 1: num_layers (3-8), resolution (512-1024)
- Step 2: num_frames (17-49), guidance_scale (5.0-10.0), num_inference_steps (20-40)
- Step 3: rife.target_fps (24-60), real_cugan.scale (2-4)

Return JSON:
{{
    "reflection": "Quality analysis...",
    "decision": "proceed" | "retry" | "fail",
    "next_step": "step1" | "step2" | "step3" | "end",
    "config_patch": {{...}}  // Only if decision="retry"
}}
"""
        
        # Prepare result summary
        result_summary = "N/A"
        if last_result:
            if "error" in last_result:
                result_summary = f"Error: {last_result['error']}"
            elif "metadata" in last_result:
                result_summary = f"Success - {last_result['metadata']}"
            else:
                result_summary = "Success"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Analyze and decide the next action.")
        ])
        
        chain = prompt | self.llm | JsonOutputParser()
        
        try:
            response = chain.invoke({
                "current_step": current_step,
                "result_summary": result_summary,
                "config": str(state.get("config", {})),
                "retry_count": retry_count
            })
            
            return response
            
        except Exception as e:
            # Fallback if LLM fails
            return {
                "reflection": f"Supervisor error: {e}. Proceeding to next step.",
                "decision": "proceed",
                "next_step": self._get_default_next(current_step),
                "config_patch": {}
            }

    def _get_default_next(self, current_step: str) -> str:
        """Get next step in sequence"""
        steps = ["start", "step1", "step2", "step3", "end"]
        try:
            idx = steps.index(current_step)
            return steps[idx + 1] if idx + 1 < len(steps) else "end"
        except:
            return "end"
