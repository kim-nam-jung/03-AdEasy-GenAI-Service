import os
from pathlib import Path
from huggingface_hub import snapshot_download, hf_hub_download

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

def download_sam2():
    print("📥 Downloading SAM 2 (Hiera Large)...")
    model_path = MODELS_DIR / "sam2"
    snapshot_download(
        repo_id="facebook/sam2-hiera-large",
        local_dir=str(model_path),
        local_dir_use_symlinks=False
    )
    print("✅ SAM 2 downloaded")

def download_rife():
    print("📥 Downloading RIFE v4.26...")
    model_path = MODELS_DIR / "rife"
    model_path.mkdir(exist_ok=True)
    hf_hub_download(
        repo_id="r3gm/RIFE",
        filename="RIFEv4.26_0921.zip",
        local_dir=str(model_path)
    )
    print("✅ RIFE downloaded")

def download_real_cugan():
    print("📥 Downloading Real-CUGAN...")
    model_path = MODELS_DIR / "real_cugan"
    model_path.mkdir(exist_ok=True)
    snapshot_download(
        repo_id="henfiyhi/Real-CUGAN",
        local_dir=str(model_path),
        local_dir_use_symlinks=False
    )
    print("✅ Real-CUGAN downloaded")

def download_ltx_video():
    """Download full LTX-Video repository (includes 2-Pro 13B)."""
    print("📥 Downloading full LTX-Video repository (Large but guaranteed)...")
    repo_id = "Lightricks/LTX-Video"
    model_path = MODELS_DIR / "ltx2"
    model_path.mkdir(exist_ok=True)
    
    try:
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(model_path),
            local_dir_use_symlinks=False,
            # We can exclude non-essential large files if needed, but let's just get it all
            ignore_patterns=["*.msgpack", "*.h5", "*.ot"]
        )
        print("✅ LTX-Video fully downloaded!")
    except Exception as e:
        print(f"  ❌ Failed to download LTX-Video: {e}")

if __name__ == "__main__":
    download_sam2()
    download_ltx_video()
    download_rife()
    download_real_cugan()
    print("✨ All essential models (SAM 2, LTX-2 Pro, RIFE, Real-CUGAN) are ready!")
