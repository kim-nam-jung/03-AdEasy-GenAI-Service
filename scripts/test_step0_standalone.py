# scripts/test_step0_standalone.py
"""
Step 0 단독 테스트 (기존 인프라 활용)
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.logger import TaskLogger
from common.paths import TaskPaths
from common.config import Config
from pipeline.step0_preprocessing import step0_preprocessing

def main():
    # 설정
    task_id = "test_step0_shirt"
    
    # ✅ root를 프로젝트 루트로 설정 (data가 아님!)
    project_root = Path(__file__).parent.parent
    
    # 테스트 이미지
    test_image = project_root / "data" / "inputs" / "shirt_front_test.jpg"
    
    if not test_image.exists():
        print(f"❌ 테스트 이미지 없음: {test_image}")
        return
    
    # ✅ TaskPaths에 프로젝트 루트 전달 (data 디렉토리가 아님!)
    paths = TaskPaths(root=project_root, task_id=task_id)
    log_path = paths.outputs_task_dir / "test.log"
    logger = TaskLogger(task_id=task_id, log_file=log_path)
    cfg = Config()
    
    print("=" * 60)
    print("🧪 Step 0 단독 테스트")
    print("=" * 60)
    print(f"�� 입력: {test_image}")
    print(f"🗂️  temp_task_dir: {paths.temp_task_dir}")
    
    # Step 0 실행
    result = step0_preprocessing(
        task_id=task_id,
        paths=paths,
        logger=logger,
        cfg=cfg,
        image_paths=[str(test_image)]
    )
    
    # 결과 출력
    print("\n📊 결과:")
    for idx, (seg, mask) in enumerate(zip(
        result["segmented_paths"],
        result["mask_paths"]
    ), 1):
        print(f"\n  Image {idx}:")
        print(f"    - Segmented: {seg}")
        print(f"    - Mask: {mask}")
        print(f"    - Exists: seg={seg.exists()}, mask={mask.exists()}")
    
    if all(p.exists() for p in result["segmented_paths"] + result["mask_paths"]):
        print("\n✅ Step 0 테스트 성공!")
        print(f"\n📁 결과 위치:")
        print(f"   {result['segmented_paths'][0].parent}")
    else:
        print("\n❌ 일부 파일 생성 실패")

if __name__ == "__main__":
    main()
