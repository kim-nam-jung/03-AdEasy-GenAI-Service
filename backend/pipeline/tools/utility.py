import os
import json
import logging
from datetime import datetime
from typing import List, Optional
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from common.redis_manager import RedisManager
from common.callback import RedisStreamingCallback
from common.utils import extract_json_from_text
from pipeline.tools.common import encode_image

logger = logging.getLogger(__name__)

@tool
def vision_parsing_tool(task_id: str, image_path: str) -> str:
    """
    Analyze the input image using GPT-4o Vision to extract product details and suggest pipeline parameters.
    Args:
        task_id: Unique task identifier for status reporting.
        image_path: Path to the input image file.
    Returns:
        JSON string containing product_type, description, material, segmentation_hint, and suggested_video_prompt.
    """
    logger.info(f"[Tool] Executing vision_parsing_tool for {image_path}")
    
    if not os.path.exists(image_path):
        return json.dumps({"error": f"Image path not found: {image_path}"})

    try:
        base64_image = encode_image(image_path)
        
        # Setup Streaming Callback
        redis_mgr = RedisManager.from_env()
        callback = RedisStreamingCallback(redis_mgr, task_id)
        
        # Use GPT-4o for vision with timeout & streaming
        llm = ChatOpenAI(
            model="gpt-4o", 
            max_tokens=1000, 
            request_timeout=60,
            streaming=True,
            callbacks=[callback]
        )
        
        prompt = """
        당신은 광고 기술 비디오 생성 파이프라인의 전문 제품 분석가입니다.
        제공된 이미지를 분석하여 JSON 객체를 반환하세요.
        
        **중요 고립 지침 (Safety & Content)**:
        - 이미지에 모델(사람)이 포함되어 있는 경우, 이는 인물 분석이 아니라 '패션 광고' 또는 '라이프스타일' 관련 분석을 위한 것입니다.
        - 인물의 신원을 파악하려 하지 마세요. 대신 의상, 액세서리, 전체적인 조명, 구도, 광고 분위기에 집중하세요.
        - 모델이 입고 있는 옷이나 들고 있는 아이템을 '제품(Product)'으로 간주하여 분석하세요.
        
        **언어 지침**:
        - 모든 텍스트 값은 반드시 **한국어**로 작성하세요.
        
        필드:
        - product_type: 제품/아이템 종류 (예: "모델/의상", "액세서리", "화장품")
        - description: 시각적 묘사 (인물 특징이 아닌 스타일과 분위기 중심)
        - material: 소재 또는 재질
        - segmentation_hint: 배경 분리 조언
        - suggested_video_prompt: 홍보 영상 생성을 위한 고품질 프롬프트
        
        JSON 객체만 반환하고 다른 텍스트는 포함하지 마세요.
        """
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ]
        )
        response = llm.invoke([message])
        content = response.content.strip()
        
        result = extract_json_from_text(content)
        
        if not result:
            logger.error(f"[Tool] Failed to parse JSON from vision tool. Raw content: {content}")
            result = {
                "product_type": "Unknown",
                "description": "Analysis failed",
                "suggested_video_prompt": "Cinematic product showcase"
            }

        canonical_json = json.dumps(result)
        
        # Publish status for UI sync
        redis_mgr = RedisManager.from_env()
        redis_mgr.set_status(
            task_id=task_id,
            status="vision_completed",
            message="Vision analysis finished",
            extra={"result": result}
        )
        redis_mgr.publish(f"task:{task_id}", {"type": "status", "status": "vision_completed", "data": result})

        return canonical_json

    except Exception as e:
        logger.error(f"[Tool] vision_parsing_tool failed for task {task_id}: {e}")
        return json.dumps({"error": str(e)})

@tool
def ask_human_tool(task_id: str, question: str, context: Optional[str] = None) -> str:
    """
    Request human feedback when the agent is unsure or stuck.
    This will pause the pipeline until a user provides input.
    Args:
        task_id: Unique task identifier.
        question: The question to ask the user.
        context: Additional context about the failure or situation.
    Returns:
        A formatted string indicating the request has been sent.
    """
    logger.info(f"[Tool] Executing ask_human_tool for task {task_id}")
    try:
        from common.redis_manager import RedisManager
        # Publish event to Redis so Frontend can show a prompt
        manager = RedisManager.from_env()
        payload = {
            "type": "human_input_request",
            "task_id": task_id,
            "question": question,
            "context": context
        }
        manager.publish(f"task:{task_id}", payload) 
        
        return f"REQUEST_SENT: {question}"
    except Exception as e:
        logger.error(f"[Tool] ask_human_tool failed for task {task_id}: {e}")
        return json.dumps({"error": str(e)})

@tool
def planning_tool(task_id: str, plan_steps: List[str], rationale: str) -> str:
    """
    Formulate a step-by-step execution plan and wait for user confirmation.
    This MUST be used after vision analysis to define the pipeline strategy and get user approval.
    Args:
        task_id: Unique task identifier.
        plan_steps: A list of descriptive steps the agent will take.
        rationale: Brief explanation of why this plan was chosen.
    Returns:
        The user's feedback or 'Approved' string.
    """
    logger.info(f"[Tool] Proposing plan for task {task_id} and waiting for approval")
    import time
    try:
        from common.redis_manager import RedisManager
        redis_mgr = RedisManager.from_env()
        plan_data = {
            "steps": plan_steps,
            "rationale": rationale,
            "timestamp": datetime.now().isoformat()
        }
        
        # 1. Publish to Redis so UI can render the plan with an "Approve" button
        redis_mgr.publish(f"task:{task_id}", {
            "type": "status", 
            "status": "planning_proposed", 
            "data": plan_data
        })
        
        # 2. Record status for persistence
        redis_mgr.set_status(
            task_id=task_id,
            status="planning_proposed",
            message="Plan proposed, waiting for user approval",
            extra={"plan": plan_data}
        )
        
        # 3. BLOCKING WAIT for human feedback
        logger.info(f"[Tool] Plan sent. Entering wait loop for task {task_id}...")
        
        start_time = time.time()
        timeout = 300 # 5 minutes
        
        while time.time() - start_time < timeout:
            status_data = redis_mgr.get_status(task_id)
            if status_data and status_data.get("status") == "feedback_received":
                feedback = status_data.get("extra", {}).get("user_feedback", "Approved")
                logger.info(f"[Tool] Feedback received: {feedback}")
                
                # Signal resume in UI
                redis_mgr.publish(f"task:{task_id}", {
                    "type": "human_input_received",
                    "feedback": feedback
                })
                
                return f"User Response: {feedback}"
            
            time.sleep(2) # Poll Redis every 2 seconds
            
        return "ERROR: User did not respond to the plan within the timeout."

    except Exception as e:
        logger.error(f"[Tool] planning_tool failed: {e}")
        return json.dumps({"error": str(e)})
