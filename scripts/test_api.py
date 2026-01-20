# scripts/test_api.py
"""
Flask API 테스트 스크립트

개선 사항:
- 여러 이미지 파일 업로드 테스트
- 파일 크기 검증 테스트
- 에러 케이스 테스트
"""

import requests
import time
from pathlib import Path
from io import BytesIO
from PIL import Image

API_BASE = "http://localhost:5000/api"


def create_test_image(width=800, height=600, color=(255, 0, 0)) -> BytesIO:
    """테스트용 이미지 생성 (메모리)"""
    img = Image.new('RGB', (width, height), color)
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=85)
    buf.seek(0)
    return buf


def test_health():
    """Health check 테스트"""
    print("=== 1. Health Check ===")
    try:
        resp = requests.get(f"{API_BASE}/health")
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        print()
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_generate_single():
    """단일 이미지 업로드 테스트"""
    print("=== 2. Generate Video (Single Image) ===")
    
    try:
        # 테스트 이미지 생성
        img1 = create_test_image(800, 600, (255, 100, 100))
        
        files = [
            ("images", ("test_product_1.jpg", img1, "image/jpeg"))
        ]
        data = {
            'prompt': '여름 시원한 느낌으로'
        }
        
        resp = requests.post(f"{API_BASE}/generate", files=files, data=data)
        print(f"Status: {resp.status_code}")
        result = resp.json()
        print(f"Response: {result}")
        print()
        
        return result.get('task_id') if resp.status_code == 202 else None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_generate_multiple():
    """여러 이미지 업로드 테스트"""
    print("=== 3. Generate Video (Multiple Images) ===")
    
    try:
        # 4개 이미지 생성 (다른 색상)
        img1 = create_test_image(800, 600, (255, 100, 100))  # 빨강
        img2 = create_test_image(800, 600, (100, 255, 100))  # 초록
        img3 = create_test_image(800, 600, (100, 100, 255))  # 파랑
        img4 = create_test_image(800, 600, (255, 255, 100))  # 노랑
        
        files = [
            ("images", ("product_1.jpg", img1, "image/jpeg")),
            ("images", ("product_2.jpg", img2, "image/jpeg")),
            ("images", ("product_3.jpg", img3, "image/jpeg")),
            ("images", ("product_4.jpg", img4, "image/jpeg")),
        ]
        data = {
            'prompt': '봄맞이 신상품 특가'
        }
        
        resp = requests.post(f"{API_BASE}/generate", files=files, data=data)
        print(f"Status: {resp.status_code}")
        result = resp.json()
        print(f"Response: {result}")
        print()
        
        return result.get('task_id') if resp.status_code == 202 else None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_status(task_id, polls=5):
    """상태 조회 테스트"""
    if not task_id:
        print("⚠️  task_id 없음, 상태 조회 스킵")
        return
    
    print(f"=== 4. Status Check (task_id: {task_id}) ===")
    
    for i in range(polls):
        try:
            resp = requests.get(f"{API_BASE}/status/{task_id}")
            status_data = resp.json()
            print(f"[{i+1}/{polls}] {status_data}")
            
            # completed면 중단
            if status_data.get('status') == 'completed':
                print("✅ Task completed!")
                break
            
            time.sleep(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            break
    print()


def test_download(task_id):
    """다운로드 테스트"""
    if not task_id:
        print("⚠️  task_id 없음, 다운로드 스킵")
        return
    
    print(f"=== 5. Download Video (task_id: {task_id}) ===")
    
    try:
        resp = requests.get(f"{API_BASE}/download/{task_id}")
        
        if resp.status_code == 200:
            save_path = f"/tmp/{task_id}_test.mp4"
            with open(save_path, 'wb') as f:
                f.write(resp.content)
            
            size_mb = len(resp.content) / (1024 * 1024)
            print(f"✅ Downloaded to {save_path}")
            print(f"   Size: {size_mb:.2f} MB")
        else:
            print(f"❌ Download failed: {resp.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()


def test_error_cases():
    """에러 케이스 테스트"""
    print("=== 6. Error Cases ===")
    
    # 6-1. 이미지 없이 요청
    print("[6-1] No images:")
    resp = requests.post(f"{API_BASE}/generate", data={'prompt': 'test'})
    print(f"  Status: {resp.status_code}, Response: {resp.json()}")
    
    # 6-2. 5개 이미지 (초과)
    print("[6-2] Too many images (5 > 4):")
    files = [
        ("images", (f"img{i}.jpg", create_test_image(), "image/jpeg"))
        for i in range(5)
    ]
    resp = requests.post(f"{API_BASE}/generate", files=files)
    print(f"  Status: {resp.status_code}, Response: {resp.json()}")
    
    # 6-3. 잘못된 확장자
    print("[6-3] Invalid file type:")
    files = [("images", ("test.txt", BytesIO(b"text"), "text/plain"))]
    resp = requests.post(f"{API_BASE}/generate", files=files)
    print(f"  Status: {resp.status_code}, Response: {resp.json()}")
    
    # 6-4. 프롬프트 너무 길게
    print("[6-4] Prompt too long:")
    long_prompt = "A" * 201
    img = create_test_image()
    files = [("images", ("img.jpg", img, "image/jpeg"))]
    resp = requests.post(f"{API_BASE}/generate", files=files, data={'prompt': long_prompt})
    print(f"  Status: {resp.status_code}, Response: {resp.json()}")
    
    # 6-5. 존재하지 않는 task_id 조회
    print("[6-5] Non-existent task_id:")
    resp = requests.get(f"{API_BASE}/status/nonexistent")
    print(f"  Status: {resp.status_code}, Response: {resp.json()}")
    
    print()


if __name__ == '__main__':
    print("🧪 ADEASY_SHORTS API Test Suite")
    print("=" * 50)
    print()
    
    # 1. Health check
    if not test_health():
        print("❌ Health check failed. Is the server running?")
        exit(1)
    
    # 2. 단일 이미지 테스트
    task_id_1 = test_generate_single()
    
    # 3. 여러 이미지 테스트
    task_id_2 = test_generate_multiple()
    
    # 4. 상태 조회 (첫 번째 작업)
    if task_id_1:
        test_status(task_id_1, polls=5)
    
    # 5. 다운로드 시도 (아직 완료 안 됐을 것)
    if task_id_1:
        test_download(task_id_1)
    
    # 6. 에러 케이스 테스트
    test_error_cases()
    
    print("=" * 50)
    print("✅ All tests completed!")
    print()
    print("📝 Generated task IDs:")
    if task_id_1:
        print(f"  - Single image: {task_id_1}")
    if task_id_2:
        print(f"  - Multiple images: {task_id_2}")
