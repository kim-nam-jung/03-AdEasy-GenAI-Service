# scripts/download_models.py
"""
Phase 5: AI 모델 다운로드 스크립트 (수정 버전)
- 실제 존재하는 공개 repo 사용
"""

import os
from pathlib import Path
from huggingface_hub import snapshot_download, hf_hub_download

# 모델 저장 경로
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

def download_fastsam():
    """FastSAM 모델 다운로드 (~100MB)"""
    print("📥 Downloading FastSAM...")
    model_path = MODELS_DIR / "FastSAM"
    model_path.mkdir(exist_ok=True)
    
    # FastSAM-x.pt 파일만 다운로드
    try:
        hf_hub_download(
            repo_id="IDEA-Research/grounding-dino-base",
            filename="groundingdino_swint_ogc.pth",
            local_dir=str(model_path)
        )
        print("✅ FastSAM downloaded")
    except Exception as e:
        print(f"⚠️ FastSAM download failed: {e}")
        print("   FastSAM will use ultralytics package instead")

def download_qwen_vl():
    """Qwen2-VL-7B 모델 다운로드 (~8GB)"""
    print("📥 Downloading Qwen2-VL-7B...")
    model_path = MODELS_DIR / "Qwen2-VL-7B"
    if model_path.exists() and len(list(model_path.glob("*"))) > 0:
        print("✅ Qwen2-VL-7B already downloaded")
        return
    
    try:
        snapshot_download(
            repo_id="Qwen/Qwen2-VL-7B-Instruct",
            local_dir=str(model_path),
            local_dir_use_symlinks=False,
            ignore_patterns=["*.bin"]  # safetensors만 다운로드
        )
        print("✅ Qwen2-VL-7B downloaded")
    except Exception as e:
        print(f"❌ Qwen2-VL-7B download failed: {e}")

def download_qwen_14b():
    """Qwen2.5-14B 모델 다운로드 (~15GB)"""
    print("📥 Downloading Qwen2.5-14B...")
    model_path = MODELS_DIR / "Qwen2.5-14B"
    if model_path.exists() and len(list(model_path.glob("*"))) > 0:
        print("✅ Qwen2.5-14B already downloaded")
        return
    
    try:
        snapshot_download(
            repo_id="Qwen/Qwen2.5-14B-Instruct",
            local_dir=str(model_path),
            local_dir_use_symlinks=False,
            ignore_patterns=["*.bin"]  # safetensors만 다운로드
        )
        print("✅ Qwen2.5-14B downloaded")
    except Exception as e:
        print(f"❌ Qwen2.5-14B download failed: {e}")

def download_sdxl():
    """SDXL 1.0 모델 다운로드 (~7GB)"""
    print("📥 Downloading SDXL 1.0...")
    model_path = MODELS_DIR / "SDXL-1.0"
    if model_path.exists() and len(list(model_path.glob("*"))) > 0:
        print("✅ SDXL 1.0 already downloaded")
        return
    
    try:
        snapshot_download(
            repo_id="stabilityai/stable-diffusion-xl-base-1.0",
            local_dir=str(model_path),
            local_dir_use_symlinks=False,
            ignore_patterns=["*.bin", "*.ckpt"]  # safetensors만
        )
        print("✅ SDXL 1.0 downloaded")
    except Exception as e:
        print(f"❌ SDXL download failed: {e}")

def download_controlnet():
    """ControlNet SDXL Canny 모델 다운로드 (~2.5GB)"""
    print("📥 Downloading ControlNet SDXL...")
    model_path = MODELS_DIR / "ControlNet-SDXL-Canny"
    if model_path.exists() and len(list(model_path.glob("*"))) > 0:
        print("✅ ControlNet already downloaded")
        return
    
    try:
        snapshot_download(
            repo_id="diffusers/controlnet-canny-sdxl-1.0",
            local_dir=str(model_path),
            local_dir_use_symlinks=False
        )
        print("✅ ControlNet downloaded")
    except Exception as e:
        print(f"❌ ControlNet download failed: {e}")

def download_video_model():
    """Video I2V 모델 다운로드 (~5GB)"""
    print("📥 Downloading Video I2V Model...")
    model_path = MODELS_DIR / "LTX-Video"
    if model_path.exists() and len(list(model_path.glob("*"))) > 0:
        print("✅ Video model already downloaded")
        return
    
    try:
        snapshot_download(
            repo_id="Lightricks/LTX-Video",
            local_dir=str(model_path),
            local_dir_use_symlinks=False
        )
        print("✅ Video model downloaded")
    except Exception as e:
        print(f"❌ Video model download failed: {e}")

def main():
    print("🚀 Starting model downloads...")
    print(f"📁 Models directory: {MODELS_DIR.absolute()}")
    print()
    
    try:
        # 순차 다운로드 (실패해도 계속 진행)
        download_fastsam()      # ~100MB
        print()
        
        download_qwen_vl()      # ~8GB
        print()
        
        download_qwen_14b()     # ~15GB
        print()
        
        download_sdxl()         # ~7GB
        print()
        
        download_controlnet()   # ~2.5GB
        print()
        
        download_video_model()  # ~5GB
        print()
        
        print("✅ Model download process completed!")
        print(f"📁 Total size: ~35-40GB")
        print(f"📁 Location: {MODELS_DIR.absolute()}")
        print()
        print("📊 Check downloaded models:")
        print(f"   ls -lh {MODELS_DIR.absolute()}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Download interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
