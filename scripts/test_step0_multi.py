# scripts/test_step0_multi.py
"""
Step 0 다중 이미지 테스트
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.logger import TaskLogger
from common.paths import TaskPaths
from common.config import Config
from pipeline.step0_preprocessing import step0_preprocessing


def test_single_image(image_name: str):
    """단일 이미지 테스트"""
    # 파일명에서 공백/특수문자 제거하여 task_id 생성
    task_id_suffix = Path(image_name).stem.replace(" ", "_").replace(".", "_")
    task_id = f"test_step0_{task_id_suffix}"
    
    project_root = Path(__file__).parent.parent
    test_image = project_root / "data" / "inputs" / image_name
    
    if not test_image.exists():
        print(f"❌ 이미지 없음: {test_image}")
        return False
    
    paths = TaskPaths(root=project_root, task_id=task_id)
    log_path = paths.outputs_task_dir / "test.log"
    logger = TaskLogger(task_id=task_id, log_file=log_path)
    cfg = Config()
    
    print("\n" + "=" * 60)
    print(f"🧪 테스트: {image_name}")
    print("=" * 60)
    
    try:
        result = step0_preprocessing(
            task_id=task_id,
            paths=paths,
            logger=logger,
            cfg=cfg,
            image_paths=[str(test_image)]
        )
        
        seg_path = result["segmented_paths"][0]
        mask_path = result["mask_paths"][0]
        
        if seg_path.exists() and mask_path.exists():
            print(f"✅ 성공: {seg_path.parent}")
            return True
        else:
            print(f"❌ 실패: 파일 생성 안됨")
            return False
            
    except Exception as e:
        print(f"❌ 에러: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """여러 이미지 테스트"""
    test_images = [
        "shirt_front_test.jpg",
        "HOOD PULLOVER_front.png",  # ✅ 공백 포함
        "setup.jpg"                      # 🆕 의자 테스트
    ]
    
    print("=" * 60)
    print("🧪 Step 0 다중 이미지 테스트")
    print("=" * 60)
    
    results = {}
    for img in test_images:
        success = test_single_image(img)
        results[img] = success
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    for img, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status}: {img}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\n총 {total}개 중 {passed}개 성공 ({passed/total*100:.0f}%)")
    
    # 결과 파일 위치 안내
    if passed > 0:
        print("\n📁 결과 파일 위치:")
        for img, success in results.items():
            if success:
                task_id_suffix = Path(img).stem.replace(" ", "_").replace(".", "_")
                print(f"   data/temp/test_step0_{task_id_suffix}/seg_1.png")


if __name__ == "__main__":
    main()
