"""
Step 3-4 통합 테스트 스크립트

✨ 테스트 시나리오:
1. Step 3: 제어맵 생성 (Canny/Depth)
2. Step 4: SDXL 키프레임 생성
3. 전체 파이프라인 검증
"""

from pathlib import Path
import sys
import time
from PIL import Image
import numpy as np

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

# Step 3-4 import
from step3_control import step3_control
from step4_generation import step4_generation, step4_generation_batch


# ==================== 더미 클래스 ====================
class TaskLogger:
    def info(self, msg):
        print(f"[INFO] {msg}")
    
    def error(self, msg):
        print(f"[ERROR] {msg}")


class TaskPaths:
    def __init__(self, temp_dir="/tmp/step3_4_test"):
        self.temp_task_dir = Path(temp_dir)
        self.temp_task_dir.mkdir(exist_ok=True, parents=True)
    
    def keyframe_png(self, scene_id):
        return self.temp_task_dir / f"keyframe_scene{scene_id}.png"


class Config(dict):
    pass


class ScenePlan:
    def __init__(self, scene_id, prompt):
        self.scene_id = scene_id
        self.keyframe_prompt_image = prompt


class AdPlan:
    def __init__(self):
        self.scenes = [
            ScenePlan(0, "A modern smartphone with sleek design, professional product photography, studio lighting, white background"),
            ScenePlan(1, "Close-up of smartphone screen showing vibrant display, high resolution, colorful interface, modern UI"),
            ScenePlan(2, "Smartphone in hand, lifestyle photography, natural lighting, outdoor setting, happy person")
        ]


# ==================== 테스트 데이터 생성 ====================
def create_test_images(output_dir: Path, num_images: int = 3):
    """테스트용 제품 이미지 생성"""
    print(f"\n📦 Creating {num_images} test images...")
    
    segmented_paths = []
    
    for i in range(num_images):
        img_path = output_dir / f"segmented_product_{i}.png"
        
        # 간단한 제품 시뮬레이션 (사각형)
        img = Image.new('RGB', (512, 768), (255, 255, 255))
        arr = np.array(img)
        
        # 제품 영역 (Scene별 다른 색상)
        colors = [
            [100, 149, 237],  # Cornflower Blue
            [60, 179, 113],   # Medium Sea Green
            [255, 140, 0]     # Dark Orange
        ]
        
        # 중앙에 제품 사각형
        arr[200:500, 150:350] = colors[i]
        
        # 약간의 디테일 (테두리)
        arr[200:210, 150:350] = [50, 50, 50]
        arr[490:500, 150:350] = [50, 50, 50]
        arr[200:500, 150:160] = [50, 50, 50]
        arr[200:500, 340:350] = [50, 50, 50]
        
        img = Image.fromarray(arr)
        img.save(img_path)
        segmented_paths.append(img_path)
        
        print(f"   ✅ Created: {img_path.name}")
    
    return segmented_paths


# ==================== 메인 테스트 ====================
def main():
    print("=" * 70)
    print("🧪 Step 3-4 Integration Test")
    print("=" * 70)
    
    # 환경 설정
    logger = TaskLogger()
    paths = TaskPaths(temp_dir="/tmp/step3_4_integration_test")
    cfg = Config({
        'controlnet': {
            'canny_low': 100,
            'canny_high': 200
        },
        'keyframe': {
            'size': [704, 1280]
        },
        'negative_prompt': 'blurry, low quality, distorted, watermark, text, ugly, deformed, bad anatomy'
    })
    adplan = AdPlan()
    
    logger.info(f"Test directory: {paths.temp_task_dir}")
    
    # 1. 테스트 이미지 생성
    print("\n" + "=" * 70)
    print("Step 0: Creating test images...")
    print("=" * 70)
    
    segmented_paths = create_test_images(paths.temp_task_dir, num_images=3)
    
    # 2. Step 3: 제어맵 생성
    print("\n" + "=" * 70)
    print("Step 3: Control Map Generation")
    print("=" * 70)
    
    start_time = time.time()
    
    step3_result = step3_control(
        task_id="test_integration_001",
        paths=paths,
        logger=logger,
        cfg=cfg,
        segmented_paths=segmented_paths,
        adplan=adplan,
        controlnet_method="canny",  # 또는 "both"
        use_8bit=True
    )
    
    step3_time = time.time() - start_time
    
    print(f"\n⏱️  Step 3 completed in {step3_time:.1f}s")
    
    # 3. Step 4: 키프레임 생성
    print("\n" + "=" * 70)
    print("Step 4: Keyframe Generation")
    print("=" * 70)
    
    start_time = time.time()
    
    # 방법 1: 개별 생성
    # step4_result = step4_generation(
    #     task_id="test_integration_001",
    #     paths=paths,
    #     logger=logger,
    #     cfg=cfg,
    #     adplan=adplan,
    #     control_maps=step3_result['control_maps'],
    #     reference_images=step3_result['reference_images'],
    #     controlnet_type="canny",
    #     use_8bit=True,
    #     num_inference_steps=25,
    #     guidance_scale=7.5,
    #     controlnet_scale=0.8,
    #     seed=42
    # )
    
    # 방법 2: 배치 생성 (권장)
    step4_result = step4_generation_batch(
        task_id="test_integration_001",
        paths=paths,
        logger=logger,
        cfg=cfg,
        adplan=adplan,
        control_maps=step3_result['control_maps'],
        reference_images=step3_result['reference_images'],
        controlnet_type="canny",
        use_8bit=True,
        num_inference_steps=25,
        guidance_scale=7.5,
        controlnet_scale=0.8,
        seed=42
    )
    
    step4_time = time.time() - start_time
    
    print(f"\n⏱️  Step 4 completed in {step4_time:.1f}s")
    
    # 4. 결과 요약
    print("\n" + "=" * 70)
    print("✅ Integration Test Completed!")
    print("=" * 70)
    
    print(f"\n📊 Performance Summary:")
    print(f"   Step 3 (Control Maps): {step3_time:.1f}s")
    print(f"   Step 4 (Keyframes):    {step4_time:.1f}s")
    print(f"   Total:                 {step3_time + step4_time:.1f}s")
    
    print(f"\n📁 Output Files:")
    print(f"\n   Control Maps ({len(step3_result['control_maps'])}):")
    for path in step3_result['control_maps']:
        print(f"   - {path}")
    
    if 'control_maps_depth' in step3_result:
        print(f"\n   Depth Maps ({len(step3_result['control_maps_depth'])}):")
        for path in step3_result['control_maps_depth']:
            print(f"   - {path}")
    
    print(f"\n   Keyframes ({len(step4_result['keyframes'])}):")
    for path in step4_result['keyframes']:
        print(f"   - {path}")
    
    print(f"\n   All files saved to: {paths.temp_task_dir}")
    
    print("\n" + "=" * 70)
    print("🎉 Test successful! Ready for integration.")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()