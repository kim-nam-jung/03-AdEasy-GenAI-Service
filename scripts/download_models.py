# scripts/download_models.py
"""
AdEasy Model Download Script (3-Step Pipeline Version)
- SAM 2 (Segmentation)
- LTX-Video-2-Pro-13B (I2V)
- RIFE v4.26 (Interpolation)
- Real-CUGAN (Upscaling)
"""

import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download, hf_hub_download, login

# HF Token from argument or environment
HF_TOKEN = os.environ.get("HF_TOKEN")
if len(sys.argv) > 1:
    HF_TOKEN = sys.argv[1]

if HF_TOKEN:
    print("🔑 Authenticating with Hugging Face...")
    login(token=HF_TOKEN)
else:
    print("⚠️ No HF_TOKEN provided. Some gated models may fail to download.")

# 모델 저장 경로
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

def download_sam2():
    """SAM 2 모델 다운로드 (~1GB)"""
    print("📥 Downloading SAM 2 (Hiera Large)...")
    model_path = MODELS_DIR / "sam2"
    if model_path.exists() and len(list(model_path.glob("*"))) > 0:
        print("✅ SAM 2 already downloaded")
        return
    
    try:
        snapshot_download(
            repo_id="facebook/sam2-hiera-large",
            local_dir=str(model_path),
            local_dir_use_symlinks=False
        )
        print("✅ SAM 2 downloaded")
    except Exception as e:
        print(f"❌ SAM 2 download failed: {e}")

def download_ltx_video():
    """LTX-2 다운로드 (영상+오디오, Text는 GPT-4o 사용, ~35GB)"""
    print("📥 Downloading LTX-2 (Video+Audio, FP8 optimized)...")
    print("   ⚠️ Text Encoder excluded (using GPT-4o for text)")
    model_path = MODELS_DIR / "LTX-Video-2-Pro-13B"
    if model_path.exists() and len(list(model_path.glob("*"))) > 10:
        print("✅ LTX-2 already downloaded")
        return
    
    try:
        # Download FP8 model + Video/Audio components
        # Text Encoder excluded (40GB saved, using GPT-4o instead)
        snapshot_download(
            repo_id="Lightricks/LTX-2",
            local_dir=str(model_path),
            local_dir_use_symlinks=False,
            ignore_patterns=[
                # Exclude Text Encoder (40GB)
                "text_encoder/**",
                # Exclude other model variants
                "*-dev.safetensors",      # BF16 full precision
                "*distilled*",            # Distilled version
                "*lora*",                 # LoRA adapters
                "*upscaler*",             # Upscalers
                "*.bin",
                "*.pt",
                "*.onnx",
                "*.md",
                "*.mp4",
                "*.gitattributes",
            ]
        )
        print("✅ LTX-2 downloaded successfully (~35GB)")
        print("   ✅ Video: FP8 Model + VAE")
        print("   ✅ Audio: Audio VAE + Vocoder")
        print("   ℹ️ Text: Using GPT-4o API")
    except Exception as e:
        print(f"❌ LTX-2 download failed: {e}")

def download_rife():
    """RIFE v4.26 모델 다운로드 (~23MB)"""
    print("📥 Downloading RIFE v4.26...")
    model_path = MODELS_DIR / "rife"
    model_path.mkdir(exist_ok=True)
    
    try:
        # RIFE v4.26 weights from correct repository
        hf_hub_download(
            repo_id="r3gm/RIFE",
            filename="RIFEv4.26_0921.zip",
            local_dir=str(model_path)
        )
        print("✅ RIFE downloaded")
    except Exception as e:
        print(f"❌ RIFE download failed: {e}")

def download_real_cugan():
    """Real-CUGAN 모델 다운로드 (weights_v3)"""
    print("📥 Downloading Real-CUGAN...")
    model_path = MODELS_DIR / "real_cugan"
    model_path.mkdir(exist_ok=True)
    
    try:
        # Real-CUGAN weights_v3 from correct repository
        snapshot_download(
            repo_id="henfiyhi/Real-CUGAN",
            local_dir=str(model_path),
            local_dir_use_symlinks=False
        )
        print("✅ Real-CUGAN downloaded")
    except Exception as e:
        print(f"❌ Real-CUGAN download failed: {e}")

def main():
    print("🚀 Starting modern 3-step pipeline model downloads...")
    print(f"📁 Models directory: {MODELS_DIR.absolute()}")
    print()
    
    try:
        # 순차 다운로드
        download_sam2()         # Step 1
        print()
        
        download_ltx_video()     # Step 2
        print()
        
        download_rife()          # Step 3
        print()
        
        download_real_cugan()    # Step 3
        print()
        
        print("✅ Model download process completed!")
        print(f"📁 Total size: ~35-40GB")
        
    except KeyboardInterrupt:
        print("\n⚠️ Download interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
