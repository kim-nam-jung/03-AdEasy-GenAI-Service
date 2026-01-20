# scripts/test_step5_video.py
"""
Step 5 독립 테스트 (LTX-Video I2V)

Step 3-4 결과물(keyframe_1/2/3.png)을 입력으로 받아
Step 5를 독립적으로 테스트합니다.

Usage:
    python scripts/test_step5_video.py --product 0
    python scripts/test_step5_video.py --product 0 --steps 20  # 빠른 테스트
    python scripts/test_step5_video.py --product 0 --duration 3  # 짧은 영상
"""

import sys
import argparse
import time
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.logger import TaskLogger
from common.paths import TaskPaths
from common.config import Config
from common.schema import AdPlan
from pipeline.step5_video import step5_video


def load_step3_4_results(product_index: int, base_dir: Path):
    """
    Step 3-4 결과 로드
    
    Returns:
        (adplan, keyframes)
    """
    # Step 3-4 출력 디렉토리
    test_dir = base_dir / "data" / "temp" / f"test_step3_4_product{product_index}"
    
    if not test_dir.exists():
        raise FileNotFoundError(
            f"Step 3-4 results not found: {test_dir}\n"
            f"Please run: python scripts/test_step3_4.py --product {product_index}"
        )
    
    # AdPlan 로드
    adplan_path = base_dir / "data" / "temp" / "test_step2" / "adplan.json"
    if not adplan_path.exists():
        raise FileNotFoundError(
            f"adplan.json not found: {adplan_path}\n"
            f"Please run Step 2 first: python scripts/test_step2_planning.py --product {product_index}"
        )
    
    import json
    with open(adplan_path, 'r', encoding='utf-8') as f:
        adplan_data = json.load(f)
    
    adplan = AdPlan(**adplan_data)
    
    print(f"✅ AdPlan loaded: {len(adplan.scenes)} scenes")
    for scene in adplan.scenes:
        print(f"   Scene {scene.scene_id}: {scene.duration}s - {scene.keyframe_prompt_video[:50]}...")
    print()
    
    # 키프레임 로드
    keyframes = []
    for scene in adplan.scenes:
        keyframe_path = test_dir / f"keyframe_{scene.scene_id}.png"
        
        if not keyframe_path.exists():
            raise FileNotFoundError(
                f"Keyframe not found: {keyframe_path}\n"
                f"Please run: python scripts/test_step3_4.py --product {product_index}"
            )
        
        keyframes.append(keyframe_path)
    
    print(f"✅ Keyframes loaded: {len(keyframes)} images")
    for kf in keyframes:
        print(f"   - {kf.name}")
    print()
    
    return adplan, keyframes


def main():
    parser = argparse.ArgumentParser(description="Step 5 Video Generation Test")
    parser.add_argument('--product', type=int, default=0, help='Product index (0-based)')
    parser.add_argument('--steps', type=int, default=30, help='Inference steps (default: 30)')
    parser.add_argument('--guidance', type=float, default=7.5, help='Guidance scale (default: 7.5)')
    parser.add_argument('--duration', type=float, default=None, help='Override duration for all scenes (for testing)')
    parser.add_argument('--no-8bit', action='store_true', help='Disable 8bit quantization')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Step 5 Video Generation Test (LTX-Video I2V)")
    print("=" * 80)
    print(f"Product: {args.product}")
    print(f"Inference Steps: {args.steps}")
    print(f"Guidance Scale: {args.guidance}")
    print(f"8bit Quantization: {not args.no_8bit}")
    if args.duration:
        print(f"Override Duration: {args.duration}s (all scenes)")
    print("=" * 80)
    print()
    
    # 경로 설정
    project_root_path = Path(__file__).parent.parent
    
    # Step 3-4 결과 로드
    print("Loading Step 3-4 results...")
    try:
        adplan, keyframes = load_step3_4_results(args.product, project_root_path)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1
    
    # Duration 오버라이드 (테스트용)
    if args.duration:
        print(f"⚠️  Overriding all scene durations to {args.duration}s")
        for scene in adplan.scenes:
            scene.duration = args.duration
        print()
    
    # 환경 설정
    task_id = f"test_step5_product{args.product}"
    
    # Logger 초기화
    log_file = project_root_path / "data" / "temp" / f"test_step5_product{args.product}" / "test.log"
    logger = TaskLogger(task_id=task_id, log_file=log_file)
    
    # Paths 초기화
    paths = TaskPaths.from_repo(
        task_id=task_id,
        root=project_root_path
    )
    
    # Config 초기화 + 오버라이드
    cfg = Config.load()
    cfg._data['video'] = {
        'fps': 24,
        'use_8bit': not args.no_8bit,
        'num_inference_steps': args.steps,
        'guidance_scale': args.guidance
    }
    
    # Step 5 실행
    print("Starting Step 5...")
    print()
    
    start_time = time.time()
    
    try:
        result = step5_video(
            task_id=task_id,
            paths=paths,
            logger=logger,
            cfg=cfg,
            adplan=adplan,
            keyframes=keyframes
        )
        
        total_time = time.time() - start_time
        
        print()
        print("=" * 80)
        print("✅ Step 5 Completed Successfully!")
        print("=" * 80)
        print(f"Total Time: {total_time:.1f}s")
        print(f"Videos: {len(result['scene_videos'])}")
        print()
        print("Output Files:")
        for video in result['scene_videos']:
            print(f"  {video}")
        print()
        print("=" * 80)
        print("Next Steps:")
        print("  1. Check video quality:")
        print(f"     open {result['scene_videos'][0].parent}/*.mp4")
        print("  2. Run Step 6 (Post-processing):")
        print(f"     python scripts/test_step6_postprocess.py --product {args.product}")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ Step 5 Failed: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
