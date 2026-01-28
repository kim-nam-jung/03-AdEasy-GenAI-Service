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
)
from common.utils import extract_json_from_text
from common.redis_manager import RedisManager

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
    reflection = result.get("reflection", "")
    
    # Publish reflection to Redis for Frontend
    try:
        redis_mgr = RedisManager.from_env()
        redis_mgr.publish_event(task_id, {
            "type": "thought",
            "message": f"[QC Segment] Decision: {decision}\nReflection: {reflection}",
            "is_complete": True
        })
    except Exception as e:
        logger.error(f"Failed to publish QC reflection: {e}")

    # Reflection tool already updates Redis config/retry_count, but we should sync graph state if needed
    # For now, we trust Redis as the source of truth for config, but we need decision for routing.
    
    return {
        "last_qc_decision": decision,
        "failed_step": "segmentation" if decision not in ["proceed", "retry"] else None, # Actually if retry also failed eventually... 
        # But wait, logic is: QC returns decision. graph routes.
        # If it returns "human_input" (which means max retries exceeded or manual intervention needed), 
        # we should mark failed_step.
        # But wait, local variable 'decision' is just "proceed" or "retry" usually unless tool says "human_input"?
        # Actually reflection tool returns "proceed" or "retry".
        # If retry count > max, tool might return "human_input" or graph logic handles it?
        # The logic for "human_input" is triggered by...?
        # Ah, route_segmentation_qc handles routing.
        # But route_* functions READ state.
        # So we must set 'failed_step' HERE if decision implies failure.
        # Reflection tool returns decision. If it's "human_input", we set it.
        # If it's "retry" but we eventually route to human_input?
        # Graph routing logic in graph.py says:
        # if decision == "proceed" -> video_gen
        # elif decision == "retry" -> segmentation
        # else -> human_input.
        # So if decision is anything else (e.g. "human_input" or "fail"), we go to human_input.
        # So we should set failed_step = "segmentation"
        "failed_step": "segmentation", # Set current step as context
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
    
    # Check for errors in tool output
    if result.get("error"):
        logger.error(f"Video Generation Failed: {result['error']}")
        return {
            "raw_video_path": None,
            "step_results": {**state.get("step_results", {}), "video_generation": result},
            "error": result["error"] # Persist error to state
        }

    return {
        "raw_video_path": result.get("abs_raw_video_path") or result.get("raw_video_path"),
        "step_results": {**state.get("step_results", {}), "video_generation": result},
        "error": None
    }

def qc_video_node(state: AgentState):
    task_id = state["task_id"]
    step_name = "video_generation"
    
    # Check if previous step failed
    if state.get("error") or not state.get("raw_video_path"):
        logger.warning(f"Skipping QC because Video Gen failed: {state.get('error')}")
        
        # Publish error thought
        try:
             redis_mgr = RedisManager.from_env()
             redis_mgr.publish_event(task_id, {
                "type": "thought",
                "message": f"⚠️ 영상 생성 실패 (오류: {state.get('error') or 'Unknown'}).\n재시도하거나 사용자 지침을 요청합니다.",
                "is_complete": True
            })
        except: pass

        return {
            "last_qc_decision": "retry", # Retry or human input?
            # If we just return retry, it loops back to video_gen. 
            # If video_gen fails consistently, we need max retry logic.
            # reflection_tool handles retry counting. Since we SKIP reflection tool here, we must handle it or invoke reflection tool with "FAILURE" summary.
            # Let's invoke reflection tool with failure summary so it counts retries.
            "failed_step": "video_gen"
        }
        
    # Valid video path
    raw_video = state["raw_video_path"]
    
    result_json = reflection_tool.invoke({
        "task_id": task_id,
        "step_name": step_name,
        "result_summary": f"Video generated at {raw_video}. Please verify.",
        "user_prompt": state.get("user_prompt")
    })
    
    result = parse_tool_output(result_json)
    decision = result.get("decision", "proceed")
    
    # Publish reflection to Redis for Frontend
    try:
        redis_mgr = RedisManager.from_env()
        redis_mgr.publish_event(task_id, {
            "type": "thought",
            "message": f"[QC Video] Decision: {decision}",
            "is_complete": True
        })
    except Exception as e:
        logger.error(f"Failed to publish QC reflection: {e}")
    
    return {
        "last_qc_decision": decision,
        "failed_step": "video_gen" if decision != "proceed" else None
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
    # Check if we have feedback (Resume case)
    feedback = state.get("human_feedback", {})
    if feedback:
        action = feedback.get("action", "cancel")
        if action == "retry":
            return {
                "human_feedback": None, # Clean up
                "last_qc_decision": "retry",
                "user_guidance": feedback.get("message", "")
            }
        elif action == "proceed":
             return {
                "human_feedback": None,
                "last_qc_decision": "proceed"
            }
        # If cancel or unknown
        return {"error": "User cancelled or unknown action"}

    # This node is hit when QC fails 3 times
    task_id = state["task_id"]
    ask_human_tool.invoke({
        "task_id": task_id,
        "question": "품질 기준 미달로 작업이 중단되었습니다. 어떻게 하시겠습니까?",
        "context": "최대 재시도 횟수를 초과했습니다."
    })
    # This return value is essentially ignored because the graph interrupts AFTER this node
    return {"error": "Human intervention required"}
