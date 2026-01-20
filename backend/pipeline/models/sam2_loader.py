# pipeline/models/sam2_loader.py
"""
SAM 2 모델 로더 (Box Prompt 방식 적용)
- 전략: 점(Point) 대신 중앙 영역 박스(Box)를 프롬프트로 사용
- 해결: '토마토'만 따는 문제 해결 -> 박스 내부의 '전체 객체' 인식 유도
- 효과: 주변부(감자튀김, 접시 끝) 배제 및 메인 객체(햄버거) 전체 포착
"""

from ultralytics import SAM
from pathlib import Path
import torch
import cv2
import numpy as np
from PIL import Image

class SAM2Loader:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SAM2Loader, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.device = "cuda" if torch.cuda.is_available() else "cpu"
            cls._instance.model_path = "sam2.1_l.pt" 
        return cls._instance

    def load(self):
        if self.model is None:
            print(f"🔄 Loading SAM 2 (Large) from {self.model_path}...")
            try:
                self.model = SAM(self.model_path)
            except Exception as e:
                print(f"⚠️ Error loading SAM 2: {e}")
                raise
            self.model.to(self.device)
            print(f"✅ SAM 2 loaded on {self.device}")
        return self.model
    
    def unload(self):
        if self.model is not None:
            del self.model
            self.model = None
            torch.cuda.empty_cache()
            print("🗑️ SAM 2 unloaded")
    
    def segment(self, image_path: str, output_dir: str, conf: float = None, iou: float = None):
        """
        SAM 2 박스 프롬프트 세그멘테이션
        """
        model = self.load()
        
        # 1. 이미지 정보 읽기
        original = cv2.imread(image_path)
        if original is None:
             raise FileNotFoundError(f"Image not found: {image_path}")
             
        orig_h, orig_w = original.shape[:2]
        
        # ✨ 전략 수정: 중앙 "박스(Box)" 프롬프트 생성
        # 이미지의 중앙 50% 정도를 커버하는 박스를 만듭니다.
        # 너무 작으면 토마토만 잡고, 너무 크면 감자튀김까지 잡으므로 0.25~0.75 구간(50%)이 적당합니다.
        
        margin_x = int(orig_w * 0.20) # 좌우 20%씩 여백 (중앙 60% 사용)
        margin_y = int(orig_h * 0.20) # 상하 20%씩 여백
        
        x1 = margin_x
        y1 = margin_y
        x2 = orig_w - margin_x
        y2 = orig_h - margin_y
        
        box_prompt = [x1, y1, x2, y2] # [x1, y1, x2, y2]
        
        print(f"🎯 SAM 2 Box Prompting: {box_prompt} (Center Focused)")

        # 2. 추론 실행 (박스 프롬프트)
        # bboxes 인자를 사용합니다.
        results = model(
            image_path,
            bboxes=[box_prompt],
            device=self.device,
            retina_masks=True,
            verbose=False
        )
        
        if not results or not results[0].masks:
            print("⚠️ SAM 2 found no objects in the box.")
            return {"main_image": image_path, "mask": None}

        # SAM 2는 보통 3개의 마스크 후보를 줍니다 (Small, Medium, Large 느낌)
        # 우리는 이 중에서 "박스 크기와 가장 비슷한" 놈을 골라야 합니다.
        # 보통 마지막(index 2)이나 중간(index 1)이 전체 객체일 확률이 높습니다.
        
        masks = results[0].masks.data # (3, H, W) usually
        best_mask = None
        best_score = -float('inf')

        # 박스 면적 계산
        box_area = (x2 - x1) * (y2 - y1)

        for i, mask_tensor in enumerate(masks):
            mask_np = mask_tensor.cpu().numpy()
            mask_resized = cv2.resize(mask_np.astype(np.float32), (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
            
            mask_area = mask_resized.sum()
            
            # 점수 산정 로직:
            # 1. 박스 면적과 마스크 면적이 비슷할수록 좋음 (너무 작으면 토마토, 너무 크면 배경)
            # 2. 화면 전체를 덮으면 안됨 (> 90%)
            
            img_area = orig_w * orig_h
            coverage = mask_area / img_area
            
            # 너무 큰 배경(90% 이상)은 제외
            if coverage > 0.90:
                continue
                
            # 너무 작은 파편(5% 미만)은 제외
            if coverage < 0.05:
                continue

            # 박스 면적 대비 비율 (1.0에 가까울수록 박스를 꽉 채운 것)
            fill_ratio = mask_area / box_area
            
            # 점수 = fill_ratio (단, 1.2배 이상 넘어가면 감점 - 박스 밖으로 많이 나갔다는 뜻)
            if fill_ratio > 1.5:
                score = 1.0 / fill_ratio # 패널티
            else:
                score = fill_ratio
            
            # SAM 자체 confidence score가 있다면 활용 (results[0].box.conf 같은 것이 있을 수 있음)
            # 여기서는 면적 기반 휴리스틱 사용
            
            print(f"  Candidate {i}: Coverage={coverage:.2f}, BoxFill={fill_ratio:.2f} -> Score={score:.2f}")

            if score > best_score:
                best_score = score
                best_mask = mask_resized

        # 만약 적절한 후보를 못 찾았다면, 가장 큰 마스크 선택 (Fallback)
        if best_mask is None:
             best_mask = masks[0].cpu().numpy()
             best_mask = cv2.resize(best_mask.astype(np.float32), (orig_w, orig_h))

        # ✨ 후처리: Connected Components (마스크 파편 제거)
        mask_uint8 = (best_mask > 0.5).astype(np.uint8)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_uint8, connectivity=8)
        
        if num_labels > 2: 
            # 중앙점(혹은 박스 중심)을 포함하는 덩어리 찾기
            center_x, center_y = orig_w // 2, orig_h // 2
            center_label = labels[center_y, center_x]
            
            if center_label != 0:
                product_mask = (labels == center_label).astype(np.float32)
            else:
                # 중심이 비었으면 가장 큰 덩어리 선택
                largest_comp_idx = stats[1:, cv2.CC_STAT_AREA].argmax() + 1
                product_mask = (labels == largest_comp_idx).astype(np.float32)
        else:
            product_mask = best_mask.astype(np.float32)

        # --- 저장 ---
        original_rgb = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
        mask_binary = (product_mask > 0.5).astype(np.float32)
        
        mask_3ch = np.stack([mask_binary]*3, axis=-1)
        main_image_rgb = (original_rgb.astype(np.float32) * mask_3ch).astype(np.uint8)
        
        mask_255 = (mask_binary * 255).astype(np.uint8)
        rgba = np.dstack([main_image_rgb, mask_255])
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = Path(image_path).stem
        
        save_path = output_dir / f"{filename}_seg.png"
        mask_save_path = output_dir / f"{filename}_mask.png"
        
        Image.fromarray(rgba, mode='RGBA').save(save_path)
        Image.fromarray(mask_255, mode='L').save(mask_save_path)
        
        return {"main_image": str(save_path), "mask": str(mask_save_path)}

def get_sam2_loader():
    return SAM2Loader()