# pipeline/step5_video.py
"""
Step 5: 영상 생성 (LTX-Video I2V)
- Scene별 영상 생성 (3개)
- 키프레임 → 영상 변환
- 각 Scene 길이: 5.5s, 5.0s, 5.0s
"""

import time
from pathlib import Path
from typing import List, Dict
from common.logger import TaskLogger
from common.paths import TaskPaths
from common.config import Config
from common.schema import AdPlan
from pipeline.models.ltx_video_loader import LTXVideoGenerator


def step5_video(
    task_id: str,
    paths: TaskPaths,
    logger: TaskLogger,
    cfg: Config,
    adplan: AdPlan,
    keyframes: List[Path],
    **kwargs
) -> Dict:
    """
    Step 5: LTX-Video I2V 영상 생성
    
    Args:
        task_id: 작업 ID
        paths: 경로 관리자
        logger: 로거
        cfg: 설정
        adplan: 광고 기획 (Scene별 video_prompt 포함)
        keyframes: 키프레임 이미지 경로 리스트 (3개)
    
    Returns:
        {
            "scene_videos": List[Path]  # Scene별 raw 영상 (3개)
        }
    """
    logger.info("=" * 60)
    logger.info("[Step 5] Video Generation (LTX-Video I2V)")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    try:
        # 설정 로드
        video_cfg = cfg.get('video', {})
        fps = video_cfg.get('fps', 24)
        num_inference_steps = video_cfg.get('num_inference_steps', 30)
        guidance_scale = video_cfg.get('guidance_scale', 7.5)
        
        logger.info(f"Configuration:")
        logger.info(f"  - FPS: {fps}")
        logger.info(f"  - Inference Steps: {num_inference_steps}")
        logger.info(f"  - Guidance Scale: {guidance_scale}")
        logger.info(f"  - Model: LTX-Video 13B Distilled (fp16)")
        logger.info("")
        
        # 입력 검증
        if len(keyframes) != len(adplan.scenes):
            raise ValueError(
                f"Keyframe count mismatch: {len(keyframes)} keyframes vs {len(adplan.scenes)} scenes"
            )
        
        for idx, keyframe in enumerate(keyframes):
            if not keyframe.exists():
                raise FileNotFoundError(f"Keyframe not found: {keyframe}")
        
        # LTX-Video 생성기 초기화
        logger.info("Initializing LTX-Video Generator...")
        generator = LTXVideoGenerator(logger=logger)
        
        # 모델 로드
        generator.load_model()
        logger.info("")
        
        scene_videos = []
        
        # Scene별 영상 생성
        for idx, scene in enumerate(adplan.scenes):
            logger.info(f"Scene {scene.scene_id} / {len(adplan.scenes)} - Video Generation")
            logger.info(f"  Duration: {scene.duration}s")
            logger.info(f"  FPS: {fps}")
            logger.info(f"  Frames: {int(scene.duration * fps)}")
            logger.info(f"  Keyframe: {keyframes[idx].name}")
            logger.info(f"  Prompt: {scene.keyframe_prompt_video[:100]}...")
            logger.info("")
            
            scene_start = time.time()
            
            # 출력 경로
            video_path = paths.scene_raw_mp4(scene.scene_id)
            video_path.parent.mkdir(parents=True, exist_ok=True)
            
            # LTX-Video I2V 생성
            try:
                result_path = generator.generate_video(
                    keyframe_path=keyframes[idx],
                    video_prompt=scene.keyframe_prompt_video,
                    duration=scene.duration,
                    fps=fps,
                    width=704,
                    height=1280,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    output_path=video_path
                )
                
                # 파일 검증
                if not result_path.exists():
                    raise FileNotFoundError(f"Generated video not found: {result_path}")
                
                file_size = result_path.stat().st_size / 1024**2  # MB
                
                scene_videos.append(result_path)
                
                scene_time = time.time() - scene_start
                logger.info(f"  ✅ Scene {scene.scene_id} completed in {scene_time:.1f}s")
                logger.info(f"  Output: {result_path.name}")
                logger.info(f"  Size: {file_size:.1f}MB")
                logger.info("")
                
            except Exception as e:
                logger.error(f"  ❌ Scene {scene.scene_id} generation failed: {e}")
                raise
        
        # 모델 언로드
        logger.info("Unloading LTX-Video model...")
        generator.unload()
        logger.info("")
        
        total_time = time.time() - start_time
        
        logger.info("=" * 60)
        logger.info(f"✅ [Step 5] Completed in {total_time:.1f}s ({total_time/60:.1f}m)")
        logger.info(f"Generated {len(scene_videos)} scene videos:")
        for video in scene_videos:
            size_mb = video.stat().st_size / 1024**2
            logger.info(f"  - {video.name} ({size_mb:.1f}MB)")
        logger.info("=" * 60)
        
        return {
            "scene_videos": scene_videos
        }
        
    except Exception as e:
        logger.error(f"❌ [Step 5] Failed: {e}")
        
        # 디버깅 정보
        logger.error(f"Debug Info:")
        logger.error(f"  - Task ID: {task_id}")
        logger.error(f"  - Keyframes: {len(keyframes)}")
        logger.error(f"  - Scenes: {len(adplan.scenes)}")
        
        raise
