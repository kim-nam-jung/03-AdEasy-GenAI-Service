from typing import Literal, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from common.config import Config
from pipeline.agent_state import AgentState
from common.callback import RedisStreamingCallback
from common.redis_manager import RedisManager

class SupervisorAgent:
    """
    Decides the next step in the pipeline based on the current state.
    Reflects on results and can modify configuration for retries.
    """
    def __init__(self, cfg: Config, task_id: str, redis_mgr: RedisManager):
        self.cfg = cfg
        self.task_id = task_id
        # Initialize LLM with streaming callback
        api_key = cfg.get("api_key", "adeasy-secret-key") # Or from os env
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
        Analyzes the last step's result and decides:
        - next_node: Name of the next node to run
        - action: 'proceed', 'retry', 'error'
        - new_config: (Optional) Updated config for retry
        - reflection: Logic behind the decision
        """
        current_step = state.get("current_step", "start")
        last_result = state.get("step_results", {}).get(current_step)
        
        # System Prompt
        system_prompt = """
        You are the Supervisor of an AI Video Generation Pipeline.
        Your goal is to ensure high-quality output by monitoring each step.
        
        Current Step: {current_step}
        Last Result Summary: {result_summary}
        Current Config: {config}
        Retry Count for this step: {retry_count}
        
        Pipeline Steps Order: step0 -> step1 -> step1_5 -> step2 -> step3 -> step4 -> step5 -> step6 -> step7_8 -> step9
        
        Analyze the result.
        1. If success and quality is good -> Proceed to next step.
        2. If failure or low quality (e.g. Identity Score < 0.9) ->
           - If retry_count < 2: Suggest RE-RUN with adjusted parameters (e.g. lower threshold, different prompt).
           - If retry_count >= 2: Proceed anyway (accept lower quality) OR Fail if critical.
        
        Return JSON:
        {{
            "thought": "Your reflection here...",
            "decision": "proceed" | "retry" | "fail",
            "next_step": "name_of_next_step",
            "updated_config_patch": {{ ... }} (optional, only for retry)
        }}
        """
        
        # Prepare context (simplified for prompt)
        result_summary = "N/A"
        if last_result:
            # Extract key metrics if available
            if "identity_score" in last_result:
                result_summary = f"Identity Score: {last_result['identity_score']}"
            elif "error" in last_result:
                result_summary = f"Error: {last_result['error']}"
            else:
                result_summary = "Success"
        
        retry_count = state.get("retry_count", {}).get(current_step, 0)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Analyze and decide.")
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
            # Fallback in case of LLM error
            return {
                "thought": f"Supervisor crashed: {e}. Proceeding blindly.",
                "decision": "proceed",
                "next_step": self._get_default_next(current_step)
            }

    def _get_default_next(self, current_step):
        steps = ["start", "step0", "step1", "step1_5", "step2", "step3", "step4", "step5", "step6", "step7_8", "step9", "end"]
        try:
            idx = steps.index(current_step)
            return steps[idx + 1] if idx + 1 < len(steps) else "end"
        except:
            return "end"
