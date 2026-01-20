import operator
from typing import TypedDict, Annotated, List, Dict, Any, Union

class AgentState(TypedDict):
    # Task context
    task_id: str
    user_prompt: str
    image_paths: List[str]
    
    # Configuration (Dynamic - can be patched by Supervisor)
    config: Dict[str, Any]
    
    # Execution State
    current_step: str  # "step1", "step2", "step3"
    next_step: str
    step_results: Dict[str, Any]  # Stores output of each step
    
    # Step 1 Outputs (Segmentation)
    segmented_layers: List[str]  # Paths to layer images
    main_product_layer: str  # Path to main product layer
    
    # Step 2 Outputs (Video Generation)
    raw_video_path: str  # Path to raw generated video
    
    # Step 3 Outputs (Post-processing)
    final_video_path: str  # Path to final processed video
    thumbnail_path: str  # Path to video thumbnail
    
    # Reflection / Error Handling
    vision_analysis: Dict[str, Any]  # Output of vision_parsing_tool
    error: Union[str, None]
    retry_count: Dict[str, int]  # Track retries per step
    reflection_history: Annotated[List[str], operator.add]  # Log of supervisor thoughts
    
    # Final Output
    final_output: Dict[str, Any]

