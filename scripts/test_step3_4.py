"""
Step 3-4 실제 테스트 (Step 2 결과물 사용)

Step 2의 결과물(adplan.json, segmented 이미지)을 입력으로 받아
Step 3-4를 독립적으로 테스트합니다.

Usage:
    python scripts/test_step3_4.py --product 0
    python scripts/test_step3_4.py --product 0 --controlnet canny
    python scripts/test_step3_4.py --product 0 --controlnet depth
    python scripts/test_step3_4.py --product 0 --steps 20  # 빠른 테스트
"""

import sys
import argparse
from pathlib import Path
import json
import time

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.logger import TaskLogger
from common.paths import TaskPaths
from common.schema import AdPlan
from pipeline.step3_control import step3_control
from pipeline.step4_generation import step4_generation_batch


def load_step2_results(product_index: int, base_dir: Path):
    """
    Step 2의 결과물 로딩
    
    Args:
        product_index: 제품 인덱스 (0-based)
        base_dir: 프로젝트 루트 디렉토리
    
    Returns:
        (adplan, segmented_paths)
    """
    print(f"\n📦 Loading Step 2 results for product {product_index}...")
    
    # Step 2 결과물 경로
    temp_dir = base_dir / "data" / "temp" / "test_step2"
    
    # 1. adplan.json 로딩
    adplan_path = temp_dir / "adplan.json"
    if not adplan_path.exists():
        raise FileNotFoundError(
            f"❌ adplan.json not found: {adplan_path}\n"
            f"   Run Step 2 first:\n"
            f"   python scripts/test_step2_planning.py --product {product_index}"
        )
    
    with open(adplan_path, 'r', encoding='utf-8') as f:
        adplan_data = json.load(f)
    
    adplan = AdPlan(**adplan_data)
    
    print(f"   ✅ AdPlan loaded: {len(adplan.scenes)} scenes")
    for scene in adplan.scenes:
        print(f"      Scene {scene.scene_id}: {scene.keyframe_prompt_image[:50]}...")
    
    # 2. segmented 이미지 로딩 (실제 경로 사용)
    # 제품별 실제 Step 0 결과 경로 매핑
    step0_mapping = {
        0: "test_step0_shirt_front_test",
        1: "test_step0_HOOD_PULLOVER_front",
        2: "test_step0_setup"
    }
    
    segmented_paths = []
    
    # 먼저 매핑된 경로 시도
    if product_index in step0_mapping:
        step0_dir = base_dir / "data" / "temp" / step0_mapping[product_index]
        segmented_paths = sorted(step0_dir.glob("seg_*.png"))
    
    # 매핑 없으면 기본 경로들 시도
    if not segmented_paths:
        # 시도 1: step0_segmented (표준 경로)
        step0_dir = base_dir / "data" / "temp" / "step0_segmented"
        segmented_paths = sorted(step0_dir.glob(f"product_{product_index}_*.png"))
    
    if not segmented_paths:
        # 시도 2: test_step0_product{N} (자동 경로)
        step0_dir = base_dir / "data" / "temp" / f"test_step0_product{product_index}"
        segmented_paths = sorted(step0_dir.glob("seg_*.png"))
    
    if not segmented_paths:
        raise FileNotFoundError(
            f"❌ Segmented images not found!\n"
            f"   Tried paths:\n"
            f"   - {base_dir}/data/temp/{step0_mapping.get(product_index, 'N/A')}\n"
            f"   - {base_dir}/data/temp/step0_segmented\n"
            f"   - {base_dir}/data/temp/test_step0_product{product_index}\n"
            f"\n"
            f"   Run Step 0 first:\n"
            f"   python scripts/test_step0_multi.py --product {product_index}"
        )
    
    print(f"   ✅ Segmented images: {len(segmented_paths)}")
    for path in segmented_paths:
        print(f"      - {path.name}")
    
    return adplan, segmented_paths


def main():
    parser = argparse.ArgumentParser(description="Step 3-4 독립 테스트")
    parser.add_argument(
        "--product",
        type=int,
        default=0,
        help="제품 인덱스 (0-based)"
    )
    parser.add_argument(
        "--controlnet",
        choices=["canny", "depth", "both"],
        default="canny",
        help="ControlNet 방법 (기본: canny)"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=30,
        help="SDXL inference steps (기본: 30, 빠른 테스트: 20)"
    )
    parser.add_argument(
        "--guidance",
        type=float,
        default=7.5,
        help="SDXL guidance scale (기본: 7.5)"
    )
    parser.add_argument(
        "--controlnet-scale",
        type=float,
        default=0.8,
        help="ControlNet conditioning scale (기본: 0.8)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="랜덤 시드 (재현성)"
    )
    parser.add_argument(
        "--no-8bit",
        action="store_true",
        help="8bit 양자화 비활성화 (더 많은 VRAM 사용)"
    )
    
    args = parser.parse_args()
    
    # 프로젝트 루트
    project_root = Path(__file__).parent.parent
    
    print("=" * 70)
    print("🧪 Step 3-4 독립 테스트")
    print("=" * 70)
    print(f"   Product: {args.product}")
    print(f"   ControlNet: {args.controlnet}")
    print(f"   Inference steps: {args.steps}")
    print(f"   Guidance scale: {args.guidance}")
    print(f"   ControlNet scale: {args.controlnet_scale}")
    print(f"   8bit quantization: {not args.no_8bit}")
    if args.seed:
        print(f"   Seed: {args.seed}")
    
    # 1. Step 2 결과물 로딩
    try:
        adplan, segmented_paths = load_step2_results(args.product, project_root)
    except FileNotFoundError as e:
        print(f"\n{e}")
        sys.exit(1)
    
    # 2. 환경 설정
    task_id = f"test_step3_4_product{args.product}"
    
    # Logger 초기화 (task_id와 log_file 전달)
    log_file = project_root / "data" / "temp" / f"test_step3_4_product{args.product}" / "test.log"
    logger = TaskLogger(task_id=task_id, log_file=log_file)
    
    # TaskPaths 초기화 (from_repo 사용)
    paths = TaskPaths.from_repo(
        task_id=task_id,
        root=project_root
    )
    
    # Config를 일반 딕셔너리로 변경
    cfg = {
        'controlnet': {
            'canny_low': 100,
            'canny_high': 200
        },
        'keyframe': {
            'size': [704, 1280]
        },
        'negative_prompt': (
            'blurry, low quality, distorted, watermark, text, '
            'ugly, deformed, bad anatomy, extra limbs'
        )
    }
    
    logger.info(f"Task ID: {task_id}")
    logger.info(f"Output directory: {paths.temp_task_dir}")
    
    # 3. Step 3: 제어맵 생성
    print("\n" + "=" * 70)
    print("Step 3: Control Map Generation")
    print("=" * 70)
    
    start_time = time.time()
    
    try:
        step3_result = step3_control(
            task_id=task_id,
            paths=paths,
            logger=logger,
            cfg=cfg,
            segmented_paths=segmented_paths,
            adplan=adplan,
            controlnet_method=args.controlnet,
            use_8bit=not args.no_8bit
        )
    except Exception as e:
        logger.error(f"Step 3 failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    step3_time = time.time() - start_time
    
    print(f"\n⏱️  Step 3 completed in {step3_time:.1f}s")
    print(f"   Control maps: {len(step3_result['control_maps'])}")
    
    # 4. Step 4: 키프레임 생성
    print("\n" + "=" * 70)
    print("Step 4: Keyframe Generation")
    print("=" * 70)
    
    start_time = time.time()
    
    # ControlNet 타입 결정
    if args.controlnet == "both":
        controlnet_type = "canny"  # both인 경우 Canny 사용
    else:
        controlnet_type = args.controlnet
    
    try:
        step4_result = step4_generation_batch(
            task_id=task_id,
            paths=paths,
            logger=logger,
            cfg=cfg,
            adplan=adplan,
            control_maps=step3_result['control_maps'],
            reference_images=step3_result['reference_images'],
            controlnet_type=controlnet_type,
            use_8bit=not args.no_8bit,
            num_inference_steps=args.steps,
            guidance_scale=args.guidance,
            controlnet_scale=args.controlnet_scale,
            seed=args.seed
        )
    except Exception as e:
        logger.error(f"Step 4 failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    step4_time = time.time() - start_time
    
    print(f"\n⏱️  Step 4 completed in {step4_time:.1f}s")
    print(f"   Keyframes: {len(step4_result['keyframes'])}")
    
    # 5. 결과 요약
    print("\n" + "=" * 70)
    print("✅ Step 3-4 Test Completed!")
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
    
    print(f"\n   Directory: {paths.temp_task_dir}")
    
    # 6. Next steps
    print(f"\n🚀 Next Steps:")
    print(f"   1. View keyframes:")
    print(f"      open {paths.temp_task_dir}/keyframe_scene*.png")
    print(f"")
    print(f"   2. Test with different controlnet:")
    print(f"      python scripts/test_step3_4.py --product {args.product} --controlnet depth")
    print(f"")
    print(f"   3. Fast test (fewer steps):")
    print(f"      python scripts/test_step3_4.py --product {args.product} --steps 20")
    print(f"")
    print(f"   4. Run Step 5 (Video Generation):")
    print(f"      python scripts/test_step5_video.py --product {args.product}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
