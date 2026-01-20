# pipeline/step0_agentic.py
"""
Step 0: Agentic Background Removal
- 모델: SAM 2 (Segment Anything Model 2)
- 로직: 생성 -> GPT-4o 평가 -> 파라미터 조정 및 재시도
- 출력: 투명 배경 PNG (RGBA)
"""

import os
import shutil
import base64
from pathlib import Path
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv

from common.logger import TaskLogger
# [변경] FastSAM 대신 SAM 2 로더 사용
from pipeline.models.sam2_loader import get_sam2_loader

# .env 파일 로드
load_dotenv()

class Step0_Agentic_Preprocessing:
    def __init__(self):
        # API Key 확인
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ WARNING: OPENAI_API_KEY not found. Agentic evaluation will fail.")
        
        self.client = OpenAI(api_key=api_key)
        
        # [변경] SAM 2 로더 초기화
        self.segmentor = get_sam2_loader()
        self.segmentor.load()

    def _encode_image(self, image_path):
        """이미지를 base64로 인코딩"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _evaluate_result(self, original_path, segmented_path, logger=None):
        """
        GPT-4o에게 누끼 품질 평가 요청
        """
        # 생성 실패 시 처리
        if segmented_path is None or not os.path.exists(segmented_path):
            return 0, "Segmentation failed. No output file generated."

        try:
            original_b64 = self._encode_image(original_path)
            seg_b64 = self._encode_image(segmented_path)

            # [업데이트] 평가 기준 강화 (감자튀김 등 배경 요소 감지)
            prompt = """
            You are an expert image editor QA. Compare the 'Original Product' and the 'Background Removed Result (Transparent PNG)'.

            CRITICAL Evaluation Criteria (Score 0-100):
            1. **Artifacts (High Penalty):** Are there background elements incorrectly included? (e.g., fries, plate edges, text, or objects not belonging to the main product). The result must ONLY be the main product (e.g., just the burger).
            2. **Completeness:** Are key parts of the main product cut off? (e.g., lettuce edges, bun top, straps).
            3. **Edges:** Are the edges clean?

            **Scoring Guide:**
            - If background artifacts (like fries) are present, the score MUST be below 80.
            - If parts of the main product are missing, the score MUST be below 80.
            - Perfect isolation: 95-100.
            
            Output JSON format:
            {
                "score": 85,
                "reason": "Good object detection but included some fries on the side."
            }
            """

            if logger:
                logger.info("🤖 Asking GPT-4o to evaluate segmentation quality...")
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url", 
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{original_b64}",
                                    "detail": "high"
                                }
                            },
                            {
                                "type": "image_url", 
                                "image_url": {
                                    "url": f"data:image/png;base64,{seg_b64}",
                                    "detail": "high"
                                }
                            }
                        ],
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=300,
                temperature=0.2
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result.get("score", 0), result.get("reason", "No reason provided")
            
        except Exception as e:
            if logger:
                logger.error(f"GPT-4o evaluation failed: {e}")
            return 0, f"Error: {str(e)}"

    def run(self, task_id: str, input_path: str, output_dir: str = None) -> str:
        """
        Agentic Workflow 실행: SAM 2 생성 -> 평가 -> (재시도)
        """
        # 로거 설정 (호출 방식에 따라 유연하게)
        try:
            from common.paths import TaskPaths
            paths = TaskPaths.from_repo(task_id)
            logger = TaskLogger(task_id, paths.run_log)
        except:
            from common.logger import get_logger
            logger = get_logger("Step0_Agentic")

        input_path = Path(input_path)
        if output_dir is None:
            output_dir = input_path.parent
        
        # 최종 결과물 경로
        final_output_path = Path(output_dir) / f"{input_path.stem}_processed.png"
        
        # [전략 수정] SAM 2 파라미터 전략
        # 1차: 엄격 (Conf 0.4) - 확실한 메인 객체만 잡기 위해
        # 2차: 표준 (Conf 0.25)
        # 3차: 관대 (Conf 0.1) - 객체를 못 잡았을 경우 대비
        retry_params = [
            {"conf": 0.4, "iou": 0.8},
            {"conf": 0.25, "iou": 0.7},
            {"conf": 0.1, "iou": 0.6}
        ]

        best_score = -1
        best_image_temp_path = None

        for attempt, params in enumerate(retry_params, 1):
            logger.info(f"🔄 [Agentic Step 0] Attempt {attempt}/{len(retry_params)} (SAM2, conf={params['conf']}, iou={params['iou']})")
            
            temp_seg_path = None
            try:
                # 1. SAM 2 실행
                res = self.segmentor.segment(
                    image_path=str(input_path),
                    output_dir=str(output_dir),
                    conf=params["conf"],
                    iou=params["iou"]
                )
                temp_seg_path = res["main_image"]
                
            except Exception as e:
                logger.warning(f"Segmentation failed on attempt {attempt}: {e}")
                continue

            # 2. 평가
            score, reason = self._evaluate_result(input_path, temp_seg_path, logger)
            logger.info(f"🧐 Evaluation: Score={score} | Reason: {reason}")

            # 최고 점수 갱신
            if temp_seg_path and os.path.exists(temp_seg_path):
                if score > best_score:
                    best_score = score
                    best_image_temp_path = temp_seg_path
            
            # 3. 목표 점수 도달 시 중단
            if score >= 90:
                logger.info("✅ Quality target met. Stopping retries.")
                break
        
        # 최종 결과 처리
        if best_image_temp_path and os.path.exists(best_image_temp_path):
            logger.info(f"🏆 Finalizing best result (Score: {best_score})")
            
            # 임시 파일을 최종 경로로 이동
            if Path(best_image_temp_path) != final_output_path:
                shutil.move(best_image_temp_path, final_output_path)
            
            # [수정] 흰색 배경 채우기(RGB Flattening) 제거됨!
            # 순수 투명 PNG(RGBA) 상태 유지 확인
            try:
                with Image.open(final_output_path) as img:
                    if img.mode != 'RGBA':
                        logger.warning("Output is not RGBA, converting to ensure transparency.")
                        img.convert("RGBA").save(final_output_path)
            except Exception as e:
                logger.warning(f"Image check failed: {e}")

            return str(final_output_path)
        else:
            error_msg = f"Agentic Step 0 Failed. Best Score: {best_score}. Please check logs."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
