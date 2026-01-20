"""
Step 1 이미지 이해 테스트 (독립형)
노스페이스 후드와 셔츠를 대상으로 이미지 이해 테스트
"""

import sys
from pathlib import Path
import json

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))


# 간단한 Logger 클래스
class SimpleLogger:
    def __init__(self, name):
        self.name = name
    
    def info(self, msg):
        print(msg)
    
    def warning(self, msg):
        print(f"⚠️ {msg}")
    
    def error(self, msg):
        print(f"❌ {msg}")


# 간단한 Paths 클래스
class SimplePaths:
    def __init__(self, temp_dir):
        self.temp_task_dir = Path(temp_dir)
        self.temp_task_dir.mkdir(parents=True, exist_ok=True)


# 간단한 Config 클래스
class SimpleConfig:
    def __init__(self):
        self.data = {}
    
    def get(self, key, default=None):
        return self.data.get(key, default)


def main():
    """Step 1 테스트 실행"""
    
    print("\n" + "="*60)
    print("🧪 Step 1 Understanding Test (Simple Version)")
    print("="*60)
    
    # 테스트 이미지 (Step 0 결과)
    test_images = [
        {
            "name": "shirt_front_test.jpg",
            "seg_path": "data/temp/test_step0_shirt_front_test/seg_1.png"
        },
        {
            "name": "HOOD PULLOVER_front.png",
            "seg_path": "data/temp/test_step0_HOOD_PULLOVER_front/seg_1.png"
        }
    ]
    
    print(f"\n📦 Testing {len(test_images)} images:")
    for img in test_images:
        print(f"   - {img['name']}")
    
    # 배경 제거된 이미지 경로 수집
    segmented_paths = []
    for img in test_images:
        seg_path = project_root / img['seg_path']
        
        if seg_path.exists():
            segmented_paths.append(seg_path)
            print(f"   ✅ Found: {seg_path.relative_to(project_root)}")
        else:
            print(f"   ⚠️ Not found: {seg_path.relative_to(project_root)}")
            print(f"      (Run Step 0 first: python scripts/test_step0_multi.py)")
    
    if not segmented_paths:
        print("\n❌ No valid images found. Please run Step 0 first!")
        return
    
    # Task 설정
    task_id = "test_step1"
    temp_dir = project_root / "data" / "temp" / "test_step1"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 간단한 Logger, Paths, Config 초기화
    logger = SimpleLogger(task_id)
    paths = SimplePaths(temp_dir)
    cfg = SimpleConfig()
    
    # 실제 모델 사용 여부 (False = 더미 데이터, True = Qwen2-VL)
    use_real_model = False  # ⚠️ True로 변경하면 Qwen2-VL 사용 (14GB 메모리 필요)
    cfg.data["step1_use_qwen2vl"] = use_real_model
    
    if use_real_model:
        print("\n🤖 Using Qwen2-VL model (this may take a while...)")
    else:
        print("\n🎭 Using dummy data (for quick testing)")
        print("   💡 Set use_real_model=True in script for real AI analysis")
    
    # Step 1 실행
    print("\n" + "="*60)
    
    try:
        from pipeline.step1_understanding import step1_understanding
        
        results = step1_understanding(
            task_id=task_id,
            paths=paths,
            logger=logger,
            cfg=cfg,
            segmented_paths=segmented_paths
        )
        
        # 결과 출력
        print("\n" + "="*60)
        print("📊 Test Results Summary")
        print("="*60)
        
        for idx, img in enumerate(test_images):
            if idx < len(results["descriptions"]):
                print(f"\n📸 {img['name']}")
                print(f"   Category: {results['categories'][idx]}")
                print(f"   Color: {results['colors'][idx]}")
                print(f"   Style: {results['styles'][idx]}")
                print(f"   Keywords: {', '.join(results['keywords'][idx][:3])}...")
                print(f"   Description: {results['descriptions'][idx][:80]}...")
                print(f"   ✅ SUCCESS")
            else:
                print(f"\n📸 {img['name']}")
                print(f"   ❌ FAILED")
        
        success_count = len(results["descriptions"])
        total_count = len(test_images)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        print(f"\n📈 Success Rate: {success_count}/{total_count} ({success_rate:.0f}%)")
        
        if success_count == total_count:
            print("\n🎉 All tests passed! Ready for Step 2!")
        elif success_count > 0:
            print(f"\n⚠️ Partial success: {success_count}/{total_count} images processed")
        else:
            print("\n❌ All tests failed. Check error messages above.")
        
        # JSON 파일 경로 출력
        print(f"\n💾 Output files in: {temp_dir.relative_to(project_root)}")
        json_files = sorted(temp_dir.glob("understanding_*.json"))
        for jf in json_files:
            print(f"   📄 {jf.name}")
            # JSON 내용 미리보기
            with open(jf, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"      Category: {data.get('category', 'N/A')}")
                print(f"      Colors: {', '.join(data.get('colors', [])[:2])}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()