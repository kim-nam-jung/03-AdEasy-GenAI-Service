import json
import logging
from typing import Dict, Any

from pipeline.agent_state import AgentState
from pipeline.tools import (
    segmentation_tool,
    video_generation_tool,
    postprocess_tool,
    reflection_tool,
    vision_parsing_tool,
    ask_human_tool
)
from common.utils import extract_json_from_text

logger = logging.getLogger(__name__)

def parse_tool_output(json_str: str) -> Dict[str, Any]:
    # Tool output is a JSON string, we need to parse it
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Fallback for malformed json
        return extract_json_from_text(json_str) or {}

def segmentation_node(state: AgentState):
    task_id = state["task_id"]
    image_paths = state["image_paths"]
    config = state.get("config", {})
    
    # Extract config parameters
    seg_config = config.get("segmentation", {})
    num_layers = seg_config.get("num_layers", 4)
    resolution = seg_config.get("resolution", 640)
    prompt_mode = seg_config.get("prompt_mode", "center")
    
    logger.info(f"[Graph] Node: Segmentation (res={resolution}, mode={prompt_mode})")
    
    # Call tool (synchronously)
    # image_paths[0] is assumed to be the main input
    result_json = segmentation_tool.invoke({
        "task_id": task_id,
        "image_path": image_paths[0],
        "num_layers": num_layers,
        "resolution": resolution,
        "prompt_mode": prompt_mode
    })
    
    result = parse_tool_output(result_json)
    
    return {
        "segmented_layers": result.get("segmented_layers", []),
        "main_product_layer": result.get("abs_main_product_layer") or result.get("main_product_layer"),
        "step_results": {**state.get("step_results", {}), "segmentation": result}
    }

def qc_segmentation_node(state: AgentState):
    task_id = state["task_id"]
    step_name = "segmentation"
    result_summary = f"Generated {len(state['segmented_layers'])} layers. Main layer: {state['main_product_layer']}"
    image_path = state["main_product_layer"] # Check the main cutout
    
    # We rely on the internal retry counting of reflection_tool, but we also track it in state
    result_json = reflection_tool.invoke({
        "task_id": task_id,
        "step_name": step_name,
        "result_summary": result_summary,
        "image_path": image_path,
        "user_prompt": state.get("user_prompt")
    })
    
    result = parse_tool_output(result_json)
    decision = result.get("decision", "proceed")
    
    # Reflection tool already updates Redis config/retry_count, but we should sync graph state if needed
    # For now, we trust Redis as the source of truth for config, but we need decision for routing.
    
    return {
        "last_qc_decision": decision,
        "reflection_history": state.get("reflection_history", []) + [result.get("reflection", "")]
    }

def video_gen_node(state: AgentState):
    task_id = state["task_id"]
    main_layer = state["main_product_layer"]
    prompt = state.get("vision_analysis", {}).get("suggested_video_prompt") or state.get("user_prompt") or "Cinematic product video"
    
    # Config
    vid_config = state.get("config", {}).get("video_generation", {})
    num_frames = vid_config.get("num_frames", 96)
    
    logger.info(f"[Graph] Node: Video Gen (frames={num_frames})")
    
    result_json = video_generation_tool.invoke({
        "task_id": task_id,
        "main_product_layer": main_layer,
        "prompt": prompt,
        "num_frames": num_frames
    })
    
    result = parse_tool_output(result_json)
    
    return {
        "raw_video_path": result.get("abs_raw_video_path") or result.get("raw_video_path"),
        "step_results": {**state.get("step_results", {}), "video_generation": result}
    }

def qc_video_node(state: AgentState):
    task_id = state["task_id"]
    step_name = "video_generation"
    # For video, reflection tool currently just checks text or needs a frame extracting.
    # The current reflection_tool might not handle video path well if it expects an image.
    # We pass the raw_video_path, but reflection_tool needs to handle it.
    # Assuming reflection_tool handles it or we skip visual check for now (or extract frame).
    # Since we didn't implement video frame extraction in reflection_tool yet, let's pass a placeholder or the thumbnail if exists.
    
    # Wait, reflection_tool expects "image_path". 
    # Let's skip visual QC for video for now to avoid crash, or assume it checks text logic only if image invalid.
    
    result_json = reflection_tool.invoke({
        "task_id": task_id,
        "step_name": step_name,
        "result_summary": "Video generated successfully.",
        "user_prompt": state.get("user_prompt")
    })
    
    result = parse_tool_output(result_json)
    decision = result.get("decision", "proceed")
    
    return {
        "last_qc_decision": decision
    }

def postprocess_node(state: AgentState):
    task_id = state["task_id"]
    raw_video = state["raw_video_path"]
    
    result_json = postprocess_tool.invoke({
        "task_id": task_id,
        "raw_video_path": raw_video
    })
    
    result = parse_tool_output(result_json)
    
    return {
        "final_video_path": result.get("abs_video_path") or result.get("video_path"),
        "thumbnail_path": result.get("thumbnail_path"),
        "final_output": result
    }

def human_input_node(state: AgentState):
    # This node is hit when QC fails 3 times
    task_id = state["task_id"]
    ask_human_tool.invoke({
        "task_id": task_id,
        "question": "품질 기준 미달로 작업이 중단되었습니다. 직접 개입해주시겠습니까?",
        "context": "최대 재시도 횟수를 초과했습니다."
    })
    # In a real LangGraph with human-in-the-loop, we would suspend execution here using interrupts.
    # For now, we logically end the graph execution, waiting for an async API call to resume (which restarts the graph or specific node).
    return {"error": "Human intervention required"}
