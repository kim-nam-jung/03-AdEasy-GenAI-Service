# pipeline/step1_understanding.py
"""
Step 1: 제품 이해 및 기획 초안 (Product Understanding & Prompt Augmentation)
- 입력: 누끼 이미지 + 사용자 요청(Raw Prompt)
- 모델: GPT-4o (Vision)
- 기능: 
  1. 사용자 프롬프트를 전문적인 비디오 생성용 영어 프롬프트로 증강 (Augmentation)
  2. 향후 일관성 유지를 위한 시각적 DNA(Visual Features) 추출
  3. 광고 분위기 및 키워드 분석
"""

import os
import base64
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from common.logger import get_logger
from common.paths import TaskPaths
from common.config import Config
from common.logger import TaskLogger

# 환경 변수 로드
load_dotenv()
logger = get_logger("Step1_Understanding")

class Step1_Understanding:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found.")
            raise ValueError("OPENAI_API_KEY is missing.")
        
        self.client = OpenAI(api_key=api_key)

    def _encode_image(self, image_path):
        """이미지를 Base64로 인코딩"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def run(self, task_id: str, image_path: str, user_prompt: str = "") -> dict:
        """
        GPT-4o Vision을 사용하여 이미지 분석 및 프롬프트 증강 수행
        """
        logger.info(f"🧐 [Step 1] Analyzing & Augmenting: {Path(image_path).name}")
        
        try:
            # 1. 이미지 인코딩
            base64_image = self._encode_image(image_path)
            
            # 2. 분석 프롬프트 구성 (Expert Video Director Persona)
            system_prompt = """
            You are an expert AI Video Director and Creative Strategist.
            Your task is to analyze the product image (transparent background) and the user's request to prepare for a high-quality video advertisement.

            **GOALS:**
            1. **Understand:** Identify the product and its visual details perfectly.
            2. **Augment:** Convert the user's simple request into a **Professional Video Generation Prompt** (English).
            3. **Consistency:** Extract "Visual DNA" to ensure the same product look in future generation steps.

            **OUTPUT FORMAT (JSON):**
            {
                "main_object": "Short name of the product",
                "visual_dna": "Detailed description of the product's physical appearance ONLY (colors, textures, shape, ingredients). This will be used to maintain consistency in image generation.",
                "mood_atmosphere": "The vibe of the video (e.g., Cinematic, Energetic, Fresh, Luxury)",
                "augmented_video_prompt": "A highly detailed, cinematic English prompt for video generation models (like Runway/Sora). Incorporate camera movement, lighting, style, and the user's intent. Start with 'Cinematic shot of...'",
                "ad_keywords": ["Keyword1", "Keyword2", "Keyword3", "Keyword4", "Keyword5"]
            }
            """

            user_content = f"User Request: {user_prompt}" if user_prompt else "Make a cool commercial for this product."

            # 3. GPT-4o 호출
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_content},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                        ],
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=800, # 상세한 프롬프트를 위해 토큰 수 증가
                temperature=0.7
            )

            # 4. 결과 파싱
            analysis_result = json.loads(response.choices[0].message.content)
            
            # 로그에 증강된 프롬프트 출력 (디버깅용)
            logger.info(f"✨ Augmented Prompt: {analysis_result.get('augmented_video_prompt')}")
            
            return analysis_result

        except Exception as e:
            logger.error(f"❌ Step 1 Analysis Failed: {e}")
            raise e

# ==================== Adapter Function ====================
def step1_understanding(
    task_id: str,
    paths: TaskPaths,
    logger: TaskLogger,
    cfg: Config,
    image_paths: list,
    prompt: str = "",
    **kwargs
) -> dict:
    """
    Step 1 Adapter
    First image is considered main product for analysis.
    """
    # Use the first image for understanding
    if not image_paths:
        raise ValueError("No image paths provided for Step 1")
    
    main_image_path = image_paths[0]
    
    step1 = Step1_Understanding()
    # Ensure correct user prompt is passed
    result = step1.run(task_id, main_image_path, user_prompt=prompt)
    
    return result