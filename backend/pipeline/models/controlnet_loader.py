"""
ControlNet 제어맵 생성기 (Step 3용)

✨ 핵심 기능:
- Canny Edge Detection (OpenCV)
- Depth Map 생성 (MiDaS v3.1 DPT-Large)
- 멀티 제어맵 지원
- 메모리 최적화 (8bit 양자화)
- GPU 캐시 관리
"""

import cv2
import numpy as np
import torch
from PIL import Image
from pathlib import Path
from typing import Literal, Optional, Tuple
import time

class ControlNetProcessor:
    """
    ControlNet 제어맵 생성 프로세서
    
    지원 방법:
    - canny: Edge detection
    - depth: Depth map (MiDaS)
    """
    
    def __init__(
        self,
        device: str = "cuda",
        use_8bit: bool = True
    ):
        """
        Args:
            device: 'cuda' or 'cpu'
            use_8bit: 8bit 양자화 사용 여부
        """
        self.device = device
        self.use_8bit = use_8bit
        self.depth_model = None
        self.depth_transform = None
        
        print(f"🎨 ControlNetProcessor initialized")
        print(f"   Device: {device}")
        print(f"   8bit quantization: {use_8bit}")
    
    def load_depth_model(self):
        """MiDaS Depth 모델 로딩 (필요시)"""
        if self.depth_model is not None:
            return
        
        print("📦 Loading MiDaS Depth model...")
        start_time = time.time()
        
        try:
            # MiDaS v3.1 DPT-Large 모델
            model_type = "DPT_Large"
            self.depth_model = torch.hub.load(
                "intel-isl/MiDaS",
                model_type,
                trust_repo=True
            )
            
            # 8bit 양자화
            if self.use_8bit and self.device == "cuda":
                self.depth_model = self.depth_model.half()
            
            self.depth_model.to(self.device)
            self.depth_model.eval()
            
            # Transform 로딩
            midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
            self.depth_transform = midas_transforms.dpt_transform
            
            elapsed = time.time() - start_time
            print(f"✅ MiDaS model loaded in {elapsed:.1f}s")
            
            if self.device == "cuda":
                memory_gb = torch.cuda.memory_allocated() / 1024**3
                print(f"   GPU Memory: {memory_gb:.2f} GB")
        
        except Exception as e:
            print(f"❌ Failed to load MiDaS: {e}")
            raise
    
    def generate_canny(
        self,
        image: Image.Image,
        low_threshold: int = 100,
        high_threshold: int = 200
    ) -> Image.Image:
        """
        Canny Edge Detection
        
        Args:
            image: 입력 이미지
            low_threshold: Canny low threshold
            high_threshold: Canny high threshold
        
        Returns:
            Canny edge map (PIL Image)
        """
        # PIL → NumPy
        img_np = np.array(image)
        
        # RGB → Grayscale
        if len(img_np.shape) == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np
        
        # Canny Edge Detection
        edges = cv2.Canny(gray, low_threshold, high_threshold)
        
        # 3채널 변환 (ControlNet 입력 형식)
        edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        
        return Image.fromarray(edges_rgb)
    
    def generate_depth(
        self,
        image: Image.Image
    ) -> Image.Image:
        """
        Depth Map 생성 (MiDaS)
        
        Args:
            image: 입력 이미지
        
        Returns:
            Depth map (PIL Image, 0-255 범위)
        """
        # 모델 로딩 (lazy loading)
        self.load_depth_model()
        
        # PIL → NumPy
        img_np = np.array(image)
        
        # Transform 적용
        input_batch = self.depth_transform(img_np).to(self.device)
        
        if self.use_8bit and self.device == "cuda":
            input_batch = input_batch.half()
        
        # Depth 예측
        with torch.no_grad():
            prediction = self.depth_model(input_batch)
            
            # 원본 해상도로 리샘플링
            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=img_np.shape[:2],
                mode="bicubic",
                align_corners=False,
            ).squeeze()
        
        # Tensor → NumPy
        depth_map = prediction.cpu().numpy()
        
        # 정규화 (0-255)
        depth_map = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min())
        depth_map = (depth_map * 255).astype(np.uint8)
        
        # 3채널 변환
        depth_rgb = cv2.cvtColor(depth_map, cv2.COLOR_GRAY2RGB)
        
        return Image.fromarray(depth_rgb)
    
    def generate_control_map(
        self,
        image_path: Path,
        method: Literal["canny", "depth"] = "canny",
        output_path: Optional[Path] = None,
        **kwargs
    ) -> Image.Image:
        """
        제어맵 생성 (통합 인터페이스)
        
        Args:
            image_path: 입력 이미지 경로
            method: 'canny' or 'depth'
            output_path: 저장 경로 (optional)
            **kwargs: 추가 파라미터 (low_threshold, high_threshold 등)
        
        Returns:
            제어맵 이미지
        """
        # 이미지 로딩
        image = Image.open(image_path).convert('RGB')
        
        print(f"🎨 Generating {method.upper()} control map...")
        print(f"   Input: {image_path.name} ({image.size[0]}x{image.size[1]})")
        
        start_time = time.time()
        
        # 제어맵 생성
        if method == "canny":
            control_map = self.generate_canny(
                image,
                low_threshold=kwargs.get('low_threshold', 100),
                high_threshold=kwargs.get('high_threshold', 200)
            )
        elif method == "depth":
            control_map = self.generate_depth(image)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        elapsed = time.time() - start_time
        print(f"✅ Control map generated in {elapsed:.1f}s")
        
        # 저장
        if output_path:
            control_map.save(output_path)
            print(f"   Saved: {output_path.name}")
        
        return control_map
    
    def unload(self):
        """메모리 해제"""
        if self.depth_model is not None:
            del self.depth_model
            self.depth_model = None
            self.depth_transform = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        print("🗑️  ControlNet processor unloaded")


# ==================== 사용 예시 ====================
if __name__ == "__main__":
    import sys
    
    # 테스트용
    processor = ControlNetProcessor(device="cuda", use_8bit=True)
    
    # 테스트 이미지 생성
    test_img = Image.new('RGB', (512, 512), (255, 255, 255))
    # 중앙에 사각형 그리기
    import numpy as np
    arr = np.array(test_img)
    arr[150:350, 150:350] = [0, 0, 255]
    test_img = Image.fromarray(arr)
    test_img.save("/tmp/test_input.png")
    
    # Canny 테스트
    print("\n=== Canny Edge Test ===")
    canny_map = processor.generate_control_map(
        Path("/tmp/test_input.png"),
        method="canny",
        output_path=Path("/tmp/test_canny.png")
    )
    
    # Depth 테스트
    print("\n=== Depth Map Test ===")
    depth_map = processor.generate_control_map(
        Path("/tmp/test_input.png"),
        method="depth",
        output_path=Path("/tmp/test_depth.png")
    )
    
    processor.unload()
    
    print("\n✅ All tests completed!")
    print(f"   Canny: /tmp/test_canny.png")
    print(f"   Depth: /tmp/test_depth.png")