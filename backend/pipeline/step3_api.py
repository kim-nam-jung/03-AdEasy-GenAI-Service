import os
import replicate
from common.logger import get_logger
import requests
from PIL import Image
from io import BytesIO
import json

logger = get_logger("Step3_API")

class ControlMapGeneratorAPI:
    def __init__(self):
        """
        Step 3: Replicate API를 이용한 제어맵 생성
        - 목표: VRAM 0 사용, 고품질 제어맵 확보
        - 출력: SoftEdge(형태), Depth(공간), Mask(영역), BBox(위치)
        """
        self.api_token = os.getenv("REPLICATE_API_TOKEN")
        if not self.api_token:
            logger.error("❌ REPLICATE_API_TOKEN이 없습니다.")
            raise ValueError("API Token Missing")
        
        # ===== [UPDATED] 모델 버전 관리 =====
        self.models = {
            # fofr/controlnet-preprocessors: 최신 버전 (f6584ef...)
            "preprocessor": "fofr/controlnet-preprocessors:f6584ef76cf07a2014ffe1e9bdb1a5cfa714f031883ab43f8d4b05506625988e"
        }
        
        # [NEW] 출력 맵 인덱스 매핑
        # API가 processor 파라미터를 무시하고 13개 맵을 모두 생성하므로
        # 원하는 맵을 인덱스로 선택
        self.map_indices = {
            "softedge": 7,  # [7] pidi.png
            "depth": 4      # [4] midas.png
        }

    def _download_image(self, url, save_path):
        """URL에서 이미지 다운로드"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            img.save(save_path)
            logger.info(f"✅ 다운로드: {os.path.basename(save_path)}")
            return True
        except Exception as e:
            logger.error(f"❌ 다운로드 실패: {url}, 에러: {e}")
            return False

    def get_bbox(self, mask_path):
        """마스크 이미지에서 Bounding Box 추출"""
        try:
            mask = Image.open(mask_path).convert("L")
            bbox = mask.getbbox()  # (left, upper, right, lower)
            if bbox:
                return {
                    "x": bbox[0],
                    "y": bbox[1],
                    "w": bbox[2] - bbox[0],
                    "h": bbox[3] - bbox[1]
                }
            logger.warning("⚠️ BBox 없음 (마스크가 비어있음)")
            return None
        except Exception as e:
            logger.error(f"❌ BBox 추출 실패: {e}")
            return None

    def run(self, input_path: str, output_dir: str):
        """
        제어맵 생성 실행
        
        Args:
            input_path: Step 0 누끼 이미지 경로
            output_dir: 출력 디렉토리
        
        Returns:
            dict: {
                "mask_path": "...",
                "bbox_path": "...",
                "softedge_path": "...",
                "depth_path": "..."
            }
        """
        filename = os.path.basename(input_path).split('.')[0]
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"🚀 Step 3 시작: {filename}")
        results = {}

        # ===== 1. Mask + BBox (로컬) =====
        try:
            img = Image.open(input_path).convert("RGBA")
            mask = img.split()[-1]  # Alpha 채널
            mask_path = os.path.join(output_dir, f"{filename}_mask.png")
            mask.save(mask_path)
            results["mask_path"] = mask_path
            logger.info("✅ Mask 생성 완료")
            
            # BBox 추출 및 저장
            bbox = self.get_bbox(mask_path)
            if bbox:
                bbox_path = os.path.join(output_dir, f"{filename}_bbox.json")
                with open(bbox_path, "w") as f:
                    json.dump(bbox, f, indent=2)
                results["bbox_path"] = bbox_path
                logger.info(f"✅ BBox 추출 완료: {bbox}")
        except Exception as e:
            logger.error(f"❌ Mask/BBox 실패: {e}")

        # ===== 2. SoftEdge + Depth (API - 한 번에 호출) =====
        try:
            logger.info("⏳ 제어맵 생성 중 (SoftEdge + Depth)...")
            with open(input_path, "rb") as f:
                output = replicate.run(
                    self.models["preprocessor"],
                    input={
                        "image": f
                        # [수정] processor 파라미터 제거 (무시되므로)
                        # API가 모든 프로세서를 실행하고 13개 맵을 반환
                    }
                )
            
            # [디버깅] 출력 확인
            logger.info(f"🔍 출력 타입: {type(output)}")
            if isinstance(output, list):
                logger.info(f"🔍 리스트 길이: {len(output)}개")
                
                # [수정] 인덱스로 SoftEdge와 Depth 선택
                if len(output) >= 13:
                    # SoftEdge: [7] pidi.png
                    softedge_idx = self.map_indices["softedge"]
                    softedge_url = str(output[softedge_idx])
                    logger.info(f"🎨 SoftEdge [{softedge_idx}]: {softedge_url[:60]}...")
                    
                    if softedge_url.startswith("http"):
                        softedge_path = os.path.join(output_dir, f"{filename}_softedge.png")
                        if self._download_image(softedge_url, softedge_path):
                            results["softedge_path"] = softedge_path
                    
                    # Depth: [4] midas.png
                    depth_idx = self.map_indices["depth"]
                    depth_url = str(output[depth_idx])
                    logger.info(f"🌊 Depth [{depth_idx}]: {depth_url[:60]}...")
                    
                    if depth_url.startswith("http"):
                        depth_path = os.path.join(output_dir, f"{filename}_depth.png")
                        if self._download_image(depth_url, depth_path):
                            results["depth_path"] = depth_path
                else:
                    logger.error(f"❌ 출력 길이 부족: {len(output)}개 (13개 필요)")
            else:
                logger.error(f"❌ 예상치 못한 출력 형식: {type(output)}")
                
        except Exception as e:
            logger.error(f"❌ API 호출 실패: {e}")

        # ===== 결과 요약 =====
        success_count = len(results)
        total_count = 4  # mask, bbox, softedge, depth
        logger.info(f"✅ Step 3 완료: {success_count}/{total_count} 성공")
        
        if success_count < 3:  # 최소 3개는 있어야 함
            logger.warning(f"⚠️ 일부 제어맵 생성 실패 ({success_count}/4)")
        
        return results


if __name__ == "__main__":
    # ===== 테스트 코드 =====
    import sys
    
    if len(sys.argv) < 2:
        print("사용법: python -m pipeline.step3_api <input_image_path>")
        print("예시: python -m pipeline.step3_api data/temp/test_task/product_processed.png")
        sys.exit(1)
    
    test_input = sys.argv[1]
    test_output = "data/temp/test_step3"
    
    if not os.path.exists(test_input):
        print(f"❌ 파일 없음: {test_input}")
        sys.exit(1)
    
    generator = ControlMapGeneratorAPI()
    results = generator.run(test_input, test_output)
    
    print("\n📊 생성 결과:")
    for key, path in results.items():
        print(f"  ✅ {key}: {path}")
