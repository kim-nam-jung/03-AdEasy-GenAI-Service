"""
Step 2 테스트 - Step 1.5 통합 버전 (최종)
"""

import sys
import json
import argparse
import time
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from pipeline.step1_5_prompt_expansion import step1_5_prompt_expansion
from pipeline.step2_planning import step2_planning


class SimpleLogger:
    def info(self, msg):
        print(msg)
    def warning(self, msg):
        print(f"⚠️  {msg}")
    def error(self, msg):
        print(f"❌ {msg}")


class SimplePaths:
    def __init__(self, temp_dir):
        self.temp_task_dir = temp_dir
        self.temp_task_dir.mkdir(parents=True, exist_ok=True)


class SimpleConfig:
    def __init__(self, use_llm=True, fast_mode=False):
        self.data = {
            "step2_use_llm": use_llm,
            "step2_fast_mode": fast_mode,
            "video": {"scene_durations": [5.5, 5.0, 5.0]}
        }
    
    def get(self, key, default=None):
        keys = key.split('.')
        value = self.data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value


def main():
    parser = argparse.ArgumentParser(description="Step 1.5 + Step 2 Test (Optimized)")
    parser.add_argument("--product", type=int, default=0,
                       help="Product index (0=first, 1=second, etc.)")
    parser.add_argument("--prompt", type=str, default="Create an engaging summer product showcase",
                       help="User prompt (e.g., '여름 시원한 느낌으로')")
    parser.add_argument("--fast", action="store_true",
                       help="Use fast mode (1-2 min)")
    parser.add_argument("--template", action="store_true",
                       help="Use template mode (instant, no LLM)")
    parser.add_argument("--skip-expansion", action="store_true",
                       help="Skip Step 1.5 (use original prompt directly)")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🧪 Step 1.5 + Step 2 Test (8bit Optimized)")
    print("=" * 60)
    print()
    
    # 모드 표시
    if args.template:
        print("🚀 Mode: Template-based (instant)")
    elif args.fast:
        print("🚀 Mode: LLM Fast (1-2 min)")
    else:
        print("🎨 Mode: LLM Creative (2-3 min)")
    
    if args.skip_expansion and not args.template:
        print("⚠️  Skipping Step 1.5 (using original prompt)")
    print()
    
    # Step 1 결과 로드
    step1_dir = project_root / "data" / "temp" / "test_step1"
    if not step1_dir.exists():
        print("❌ Step 1 결과 없음!")
        print("   먼저 실행: python scripts/test_step1_understanding.py")
        return
    
    understanding_files = sorted(step1_dir.glob("understanding_*.json"))
    if not understanding_files:
        print("❌ understanding_*.json 없음!")
        return
    
    print(f"📦 Loading {len(understanding_files)} Step 1 results...")
    
    descriptions = []
    categories = []
    colors = []
    styles = []
    keywords = []
    
    for idx, json_file in enumerate(understanding_files):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            descriptions.append(data.get("description", ""))
            categories.append(data.get("category", "product"))
            colors.append(data.get("colors", ["unknown"])[0])
            styles.append(data.get("style", "modern"))
            keywords.append(data.get("keywords", []))
        
        marker = "👉" if idx == args.product else "  "
        print(f"   {marker} [{idx}] {data.get('category')} - {data.get('colors', ['unknown'])[0]}")
    
    print()
    
    if args.product >= len(understanding_files):
        print(f"❌ Invalid product index: {args.product} (max: {len(understanding_files)-1})")
        return
    
    print(f"🎯 Using product #{args.product}: {categories[args.product]} ({colors[args.product]})")
    print(f"💬 User prompt: '{args.prompt}'")
    print()
    
    # 설정
    task_id = "test_step2"
    temp_dir = project_root / "data" / "temp" / "test_step2"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    logger = SimpleLogger()
    paths = SimplePaths(temp_dir)
    cfg = SimpleConfig(use_llm=not args.template, fast_mode=args.fast)
    
    # 전체 시작 시간
    total_start = time.time()
    
    try:
        # ✨ Step 1.5: 프롬프트 증강
        expanded_prompt = None
        
        if not args.template and not args.skip_expansion:
            print("=" * 60)
            print("🎨 Step 1.5: Prompt Expansion")
            print("=" * 60)
            print()
            
            step1_5_start = time.time()
            
            step1_5_result = step1_5_prompt_expansion(
                task_id=task_id,
                paths=paths,
                logger=logger,
                cfg=cfg,
                user_prompt=args.prompt,
                description=descriptions[args.product],
                category=categories[args.product],
                color=colors[args.product],
                style=styles[args.product],
                keywords=keywords[args.product]
            )
            
            step1_5_elapsed = time.time() - step1_5_start
            
            expanded_prompt = step1_5_result["expanded_prompt"]
            
            print()
            print("📊 Expanded Prompt:")
            print(f"   Original: {expanded_prompt['original']}")
            print(f"   Expanded: {expanded_prompt['expanded'][:100]}...")
            print(f"   Keywords: {', '.join(expanded_prompt['keywords'][:5])}")
            print(f"   Tone: {expanded_prompt['tone']}")
            print(f"   Target: {expanded_prompt['target_audience']}")
            print(f"   ⏱️  Step 1.5 time: {step1_5_elapsed:.1f}s")
            print()
        
        # Step 2: AdPlan 생성
        print("=" * 60)
        print("🎬 Step 2: AdPlan Generation")
        print("=" * 60)
        print()
        
        step2_start = time.time()
        
        result = step2_planning(
            task_id=task_id,
            paths=paths,
            logger=logger,
            cfg=cfg,
            prompt=args.prompt,
            descriptions=descriptions,
            categories=categories,
            colors=colors,
            styles=styles,
            keywords=keywords,
            product_index=args.product,
            expanded_prompt=expanded_prompt
        )
        
        step2_elapsed = time.time() - step2_start
        
        adplan = result["adplan"]
        
        # 전체 소요 시간
        total_elapsed = time.time() - total_start
        
        print()
        print("=" * 60)
        print("📊 Generated AdPlan")
        print("=" * 60)
        print()
        print(f"🎯 Concept: {adplan.concept}")
        print(f"👥 Target: {adplan.target_audience}")
        print(f"⏱️  Total Duration: {adplan.total_duration}s")
        print(f"🎨 Style: {adplan.style}")
        print(f"💫 Mood: {adplan.mood}")
        print()
        
        # Scene 상세
        for scene in adplan.scenes:
            print(f"🎬 Scene {scene.scene_id} ({scene.duration}s)")
            print(f"   📸 Image: {scene.keyframe_prompt_image[:70]}...")
            print(f"   🎥 Video: {scene.keyframe_prompt_video[:70]}...")
            print(f"   📹 Camera: {scene.control_constraints.camera_movement if scene.control_constraints else 'N/A'}")
            print()
        
        # 저장
        adplan_path = temp_dir / "adplan.json"
        adplan_dict = {
            "task_id": adplan.task_id,
            "concept": adplan.concept,
            "target_audience": adplan.target_audience,
            "total_duration": adplan.total_duration,
            "style": adplan.style,
            "mood": adplan.mood,
            "scenes": [
                {
                    "scene_id": s.scene_id,
                    "duration": s.duration,
                    "image_prompt": s.keyframe_prompt_image,
                    "video_prompt": s.keyframe_prompt_video,
                    "camera_movement": s.control_constraints.camera_movement if s.control_constraints else "static"
                }
                for s in adplan.scenes
            ]
        }
        
        with open(adplan_path, 'w', encoding='utf-8') as f:
            json.dump(adplan_dict, f, indent=2, ensure_ascii=False)
        
        print("=" * 60)
        print("✅ Test completed successfully!")
        print()
        print("⏱️  Performance:")
        if not args.template and not args.skip_expansion:
            print(f"   Step 1.5: {step1_5_elapsed:.1f}s")
        print(f"   Step 2: {step2_elapsed:.1f}s")
        print(f"   Total: {total_elapsed:.1f}s (~{total_elapsed/60:.1f} min)")
        print()
        print(f"💾 Output files: {temp_dir}")
        print(f"   📄 adplan.json")
        if expanded_prompt:
            print(f"   📄 expanded_prompt.json")
        if not args.template:
            print(f"   📄 step2_llm_output.json")
        print()
        print("🎉 Ready for Step 5 (Video Generation)!")
        print()
        print("💡 Next steps:")
        print("   - Compare with --skip-expansion for speed test")
        print("   - Try --template for instant generation")
        print("   - Test with --product 1 for hoodie")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        print()
        print("💡 Troubleshooting:")
        print("   1. Check if bitsandbytes is installed: pip install bitsandbytes")
        print("   2. Clear GPU cache: python -c 'import torch; torch.cuda.empty_cache()'")
        print("   3. Try --template mode to test without LLM")


if __name__ == "__main__":
    main()
