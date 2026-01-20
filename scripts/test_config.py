# scripts/test_config.py
from common.config import Config

def test_config():
    cfg = Config.load()
    
    print("=== 프로젝트 정보 ===")
    print(f"Name: {cfg.get('app.name')}")
    print(f"Version: {cfg.get('app.version')}")
    
    print("\n=== 모델 설정 ===")
    print(f"Cache Dir: {cfg.get('models.cache_dir')}")
    print(f"Qwen-VL: {cfg.get('models.qwen_vl.repo_id')}")
    print(f"SDXL: {cfg.get('models.sdxl.repo_id')}")
    print(f"Wan output_fps: {cfg.get('models.wan.output_fps')}")
    
    print("\n=== 비디오 설정 ===")
    print(f"Resolution: {cfg.get('video.resolution.width')}x{cfg.get('video.resolution.height')}")
    print(f"FPS: {cfg.get('video.fps')}")
    print(f"Duration: {cfg.get('video.duration')}s")
    print(f"Scene counts: {cfg.get('video.scenes.frame_counts')}")
    print(f"Dissolve overlap: {cfg.get('video.transitions.overlap_frames')} frames")
    
    print("\n=== 키프레임 설정 ===")
    print(f"Keyframe size: {cfg.get('keyframe.size')}")
    print(f"ControlNet scale: {cfg.get('keyframe.controlnet_scale')}")
    
    print("\n=== VRAM 정책 ===")
    print(f"Gate1 free_gb: {cfg.get('vram.gate1.free_gb_required')}GB")
    print(f"Gate2 free_gb: {cfg.get('vram.gate2.free_gb_required')}GB")
    
    print("\n=== 품질 검증 ===")
    print(f"Identity threshold: {cfg.get('quality.identity_score_threshold')}")
    print(f"SSIM sample every: {cfg.get('quality.ssim.sample_every_n_frames')} frames")
    
    print("\n✅ Config 로드 성공! (워크플로우 v2.3 반영)")

if __name__ == "__main__":
    test_config()
