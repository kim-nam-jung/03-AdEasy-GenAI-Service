# scripts/test_step0_agentic.py
import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 추가 (모듈 import를 위해)
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from pipeline.step0_agentic import Step0_Agentic_Preprocessing
from common.logger import get_logger

# 테스트 설정
TEST_IMAGE_PATH = "data/inputs/test_pipeline_full/shirt_front_test.jpg"  # 테스트할 이미지 경로 확인 필요!
TASK_ID = "test_agentic_001"

def main():
    logger = get_logger("Test_Script")
    
    # 1. 이미지 존재 확인
    if not os.path.exists(TEST_IMAGE_PATH):
        logger.error(f"❌ Test image not found at: {TEST_IMAGE_PATH}")
        logger.info("Please change 'TEST_IMAGE_PATH' in the script to a valid file.")
        return

    logger.info(f"🚀 Starting Agentic Step 0 Test for: {TEST_IMAGE_PATH}")
    
    # 2. Agentic 전처리기 초기화
    # 주의: OPENAI_API_KEY 환경변수가 설정되어 있어야 함
    try:
        processor = Step0_Agentic_Preprocessing()
        
        # 3. 실행
        output_path = processor.run(
            task_id=TASK_ID,
            input_path=TEST_IMAGE_PATH,
            output_dir="data/outputs/test_agentic"
        )
        
        logger.info(f"✨ Success! Final Output saved at: {output_path}")
        logger.info("Check the folder 'data/outputs/test_agentic' to see the result.")
        
    except Exception as e:
        logger.error(f"❌ Failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()