# pipeline/step4_generation.py
"""
Step 4: Keyframe Generation Pipeline
SDXL + ControlNet + IP-Adapter를 사용한 Scene별 키프레임 생성

✨ 핵심 기능:
- SDXL 1.0 Base + Multi-ControlNet (SoftEdge + Depth)
- Scene별 Start/End Frame 생성 (3 Scene × 2 = 6장)
- 704×1280 해상도 (세로형)
- IP-Adapter: 제품 일관성 유지
- 완전 로컬 실행 (L4 24GB GPU)

[FIXED] 주요 수정사항:
1. generate_with_ip_adapter 호출 시 파라미터 이름 수정 (ip_adapter_image)
2. control_images를 PIL Image 리스트로 전달
3. controlnet_conditioning_scale을 리스트로 전달
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image
import torch

# ===== 올바른 import =====
from pipeline.models.sdxl_loader import get_sdxl_loader
from common.paths import TaskPaths
from common.config import Config
from common.logger import TaskLogger

logger = logging.getLogger("Step4_KeyframeGenerator")
logger.setLevel(logging.INFO)


class Step4_KeyframeGenerator:
    """
    Step 4: 키프레임 생성기
    
    입력:
    - product_image: Step 0의 누끼 이미지 (IP-Adapter용)
    - visual_dna: Step 1의 제품 특징 (프롬프트 증강용)
    - scenario: Step 2의 시나리오 (3개 Scene)
    - control_maps: Step 3의 제어맵 (softedge, depth, mask, bbox)
    
    출력:
    - 6개 키프레임 (Scene별 Start/End Frame)
    """
    
    def __init__(self):
        self.loader = None  # SDXL Loader는 첫 실행 시 로드
        logger.info("✅ Step4_KeyframeGenerator 초기화 완료")
    
    def _load_model(self):
        """SDXL 모델 로딩 (최초 1회만)"""
        if self.loader is None:
            logger.info("📦 SDXL 모델 로딩 중... (최초 1회 30초 소요)")
            
            self.loader = get_sdxl_loader()
            
            # [FIXED] enable_cpu_offload 제거
            success = self.loader.load(enable_controlnet=True)
            
            if not success:
                raise RuntimeError("❌ SDXL 모델 로딩 실패!")
            
            logger.info("✅ SDXL 모델 로딩 완료")
    
    def generate_keyframes(
        self,
        product_image: str,
        visual_dna: str,
        scenario: Dict,
        control_maps: Dict,
        output_dir: str,
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        controlnet_scale: List[float] = [0.5, 0.8],
        seed: Optional[int] = None
    ) -> Dict[str, str]:
        """
        키프레임 생성 메인 함수
        """
        try:
            logger.info("🎬 [Step 4] 키프레임 생성 시작...")
            logger.info(f"   - 입력 이미지: {Path(product_image).name}")
            logger.info(f"   - Scene 수: {len(scenario.get('scenes', []))}")
            logger.info(f"   - Inference Steps: {num_inference_steps}")
            logger.info(f"   - Guidance Scale: {guidance_scale}")
            logger.info(f"   - ControlNet Scale: {controlnet_scale}")
            
            # 1) 모델 로딩
            self._load_model()
            
            # 2) 제어맵 로드 [FIXED] PIL Image 리스트로 준비
            softedge_path = control_maps.get('softedge_path')
            depth_path = control_maps.get('depth_path')
            
            control_images = None  # [FIXED] 기본값 None
            
            if not softedge_path or not depth_path:
                logger.warning("⚠️ SoftEdge 또는 Depth Map이 없습니다. ControlNet 없이 진행합니다.")
            else:
                logger.info(f"   - SoftEdge: {Path(softedge_path).name}")
                logger.info(f"   - Depth: {Path(depth_path).name}")
                
                # [FIXED] PIL Image 리스트로 로드
                softedge_img = Image.open(softedge_path).convert('RGB')
                depth_img = Image.open(depth_path).convert('RGB')
                control_images = [softedge_img, depth_img]
            
            # 3) 출력 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)
            
            # 4) Scene별 키프레임 생성
            keyframes = {}
            scenes = scenario.get('scenes', [])
            
            for scene in scenes:
                scene_id = scene['scene_id']
                logger.info(f"\\n{'='*60}")
                logger.info(f"🎨 Scene {scene_id} 키프레임 생성 중...")
                logger.info(f"{'='*60}")
                
                # ===== Start Frame 생성 =====
                logger.info(f"🎬 Scene {scene_id} - Start Frame")
                
                start_prompt = self._build_prompt(
                    scene, 
                    visual_dna, 
                    frame_type='start'
                )
                logger.info(f"   Prompt: {start_prompt[:80]}...")
                
                # [FIXED] 파라미터 이름 수정: ip_adapter_image
                start_image = self.loader.generate_with_ip_adapter(
                    prompt=start_prompt,
                    ip_adapter_image=product_image,  # [FIXED] 이름 변경
                    ip_adapter_scale=0.6,
                    negative_prompt="low quality, blurry, distorted, watermark, text, deformed",
                    width=704,
                    height=1280,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    seed=seed + scene_id * 10 if seed else None,
                    control_images=control_images,  # [FIXED] PIL Image 리스트
                    controlnet_conditioning_scale=controlnet_scale  # [FIXED] 리스트 전달
                )
                
                if start_image:
                    start_path = os.path.join(output_dir, f"scene{scene_id}_start.png")
                    start_image.save(start_path)
                    keyframes[f"scene{scene_id}_start"] = start_path
                    logger.info(f"   ✅ Start Frame 저장: {Path(start_path).name}")
                else:
                    logger.error(f"   ❌ Start Frame 생성 실패")
                
                # ===== End Frame 생성 =====
                logger.info(f"🎬 Scene {scene_id} - End Frame")
                
                end_prompt = self._build_prompt(
                    scene, 
                    visual_dna, 
                    frame_type='end'
                )
                logger.info(f"   Prompt: {end_prompt[:80]}...")
                
                # [FIXED] 파라미터 이름 수정: ip_adapter_image
                end_image = self.loader.generate_with_ip_adapter(
                    prompt=end_prompt,
                    ip_adapter_image=product_image,  # [FIXED] 이름 변경
                    ip_adapter_scale=0.6,
                    negative_prompt="low quality, blurry, distorted, watermark, text, deformed",
                    width=704,
                    height=1280,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    seed=seed + scene_id * 10 + 5 if seed else None,
                    control_images=control_images,  # [FIXED] PIL Image 리스트
                    controlnet_conditioning_scale=controlnet_scale  # [FIXED] 리스트 전달
                )
                
                if end_image:
                    end_path = os.path.join(output_dir, f"scene{scene_id}_end.png")
                    end_image.save(end_path)
                    keyframes[f"scene{scene_id}_end"] = end_path
                    logger.info(f"   ✅ End Frame 저장: {Path(end_path).name}")
                else:
                    logger.error(f"   ❌ End Frame 생성 실패")
            
            logger.info(f"\\n{'='*60}")
            logger.info(f"✅ [Step 4] 완료: {len(keyframes)}/6 키프레임 생성")
            logger.info(f"{'='*60}")
            
            return keyframes
        
        except Exception as e:
            logger.error(f"❌ 키프레임 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _build_prompt(self, scene: Dict, visual_dna: str, frame_type: str) -> str:
        """
        Scene 정보를 바탕으로 프롬프트 생성
        """
        description = scene.get('description', '')
        camera = scene.get('camera_movement', '')
        
        if frame_type == 'start':
            frame_desc = scene.get('start_frame_description', '')
        else:
            frame_desc = scene.get('end_frame_description', '')
        
        # 프롬프트 조합
        prompt = f"{description}. {frame_desc}. Camera movement: {camera}. Product features: {visual_dna}. Professional advertising photography, cinematic lighting, 4K quality, high detail."
        
        return prompt
    
    def unload(self):
        """모델 언로드 (메모리 해제)"""
        if self.loader:
            logger.info("🗑️ SDXL 모델 언로드 중...")
            self.loader.unload()
            self.loader = None
            logger.info("✅ 모델 언로드 완료")


# ==================== 싱글톤 인스턴스 ====================
_step4_generator_instance = None

def get_step4_generator():
    """Step 4 Generator 싱글톤 가져오기"""
    global _step4_generator_instance
    if _step4_generator_instance is None:
        _step4_generator_instance = Step4_KeyframeGenerator()
    return _step4_generator_instance


# ==================== Adapter Function ====================
def step4_generation(
    task_id: str,
    paths: TaskPaths,
    logger: TaskLogger,
    cfg: Config,
    processed_images: list = None,
    visual_dna: str = "",
    scenario: dict = None,
    control_maps: dict = None, # Can be dict or list of dicts
    **kwargs
) -> dict:
    """
    Step 4 Adapter
    """
    # 1. Get main product image
    if not processed_images:
        raise ValueError("Step 4: No processed_images provided")
    product_image = processed_images[0]
    
    # Handle control_maps list
    c_maps = control_maps
    if isinstance(c_maps, list):
        if len(c_maps) > 0:
            c_maps = c_maps[0]
        else:
            c_maps = {}
    if c_maps is None:
        c_maps = {}

    # 3. Instantiate Generator
    generator = get_step4_generator() 
    
    output_dir = paths.data_dir / "step4_keyframes"
    
    # 4. Generate
    keyframes_map = generator.generate_keyframes(
        product_image=str(product_image),
        visual_dna=visual_dna,
        scenario=scenario,
        control_maps=c_maps,
        output_dir=str(output_dir)
        # Defaults for other params
    )
    
    # 5. Extract Start Frames for Step 5
    ordered_keyframes = []
    scenes = scenario.get('scenes', [])
    for scene in scenes:
        sid = scene['scene_id']
        key = f"scene{sid}_start" # Use Start frame for video gen
        if key in keyframes_map:
            ordered_keyframes.append(Path(keyframes_map[key]))
        else:
            logger.error(f"Missing keyframe for scene {sid}: {key}")
            
    return {
        "keyframes": ordered_keyframes,
    }
