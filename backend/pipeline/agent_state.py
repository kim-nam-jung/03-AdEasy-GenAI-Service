import operator
from typing import TypedDict, Annotated, List, Dict, Any, Union

class AgentState(TypedDict):
    # Task context
    task_id: str
    user_prompt: str
    image_paths: List[str]
    
    # Configuration (Dynamic)
    config: Dict[str, Any]
    
    # Execution State
    current_step: str
    next_step: str
    step_results: Dict[str, Any]  # Stores output of each step
    
    # Reflection / Error Handling
    error: Union[str, None]
    retry_count: Dict[str, int] # Track retries per step
    reflection_history: Annotated[List[str], operator.add] # Log of supervisor thoughts
    
    # Final Output
    final_output: Dict[str, Any]
