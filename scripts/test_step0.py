# scripts/test_step0.py
"""
Step 0 단독 테스트
"""

from pathlib import Path
from pipeline.step0_preprocessing import run_step0

DATA_DIR = Path("data")
TEST_TASK_ID = "test_step0_shirt"
TEST_IMAGE = DATA_DIR / "inputs" / "shirt_front_test.jpg"

def main():
    print("=" * 60)
    print("🧪 Step 0 테스트: FastSAM 배경 제거")
    print("=" * 60)
    
    if not TEST_IMAGE.exists():
        print(f"❌ 테스트 이미지 없음: {TEST_IMAGE}")
        return
    
    print(f"📸 입력: {TEST_IMAGE}")
    
    result = run_step0(
        task_id=TEST_TASK_ID,
        image_paths=[str(TEST_IMAGE)],
        data_dir=DATA_DIR
    )
    
    print("\n📊 결과:")
    print(f"  - 메인 이미지: {result['main_image']}")
    print(f"  - 마스크: {result['mask']}")
    print(f"  - 소요 시간: {result['time_sec']}초")
    
    main_path = Path(result['main_image'])
    mask_path = Path(result['mask'])
    
    if main_path.exists() and mask_path.exists():
        print("\n✅ Step 0 테스트 성공!")
        print(f"\n📁 결과 위치:")
        print(f"   {main_path}")
        print(f"   {mask_path}")
    else:
        print("\n❌ 출력 파일 생성 실패")

if __name__ == "__main__":
    main()
