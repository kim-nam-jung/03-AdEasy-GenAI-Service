# scripts/test_pipeline.py
"""
파이프라인 단독 테스트
"""

import sys
from pathlib import Path

# PYTHONPATH 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.orchestrator import PipelineOrchestrator
from PIL import Image
import os


def test_pipeline():
    """
    파이프라인 전체 테스트
    """
    print("🧪 Testing Full Pipeline (Step 0~9)")
    print("=" * 60)
    
    # 테스트 데이터
    task_id = "test_pipeline_full"
    image_dir = f"data/inputs/{task_id}"
    image_paths = [
        f"{image_dir}/image_1.jpg",
        f"{image_dir}/image_2.jpg"
    ]
    prompt = "여름 시원한 느낌의 광고 영상"
    
    # 더미 이미지 생성
    os.makedirs(image_dir, exist_ok=True)
    Image.new('RGB', (512, 512), (255, 100, 100)).save(image_paths[0])
    Image.new('RGB', (512, 512), (100, 255, 100)).save(image_paths[1])
    
    print(f"📷 Created test images:")
    print(f"   - {image_paths[0]}")
    print(f"   - {image_paths[1]}")
    print()
    
    # Orchestrator 실행
    try:
        orchestrator = PipelineOrchestrator(
            task_id=task_id,
            image_paths=image_paths,
            prompt=prompt
        )
        
        result = orchestrator.run()
        
        print()
        print("=" * 60)
        print("✅ Test completed!")
        print(f"   Status: {result['status']}")
        print(f"   Task ID: {result['task_id']}")
        print(f"   Final video: {result['final_video']}")
        print(f"   Thumbnail: {result['thumbnail']}")
        print(f"   Identity Score: {result['identity_score']:.4f}")
        print(f"   Validation: {'PASSED' if result['passed'] else 'FAILED'}")
        print("=" * 60)
        
        # 로그 확인
        print()
        print("📝 Check logs:")
        print(f"   tail -50 outputs/{task_id}/run.log")
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_pipeline()
