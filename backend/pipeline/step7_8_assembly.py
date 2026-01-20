# pipeline/step7_8_assembly.py
"""
Step 7-8: 최종 조립
- Scene 3개 합치기 (Dissolve 전환)
- BGM 추가
- 자막 추가
- 1080x1920, 24fps, 15초
"""

from pathlib import Path
from typing import List, Dict
from common.logger import TaskLogger
from common.paths import TaskPaths
from common.config import Config
from common.schema import AdPlan


def step7_8_assembly(
    task_id: str,
    paths: TaskPaths,
    logger: TaskLogger,
    cfg: Config,
    adplan: AdPlan,
    processed_videos: List[Path],
    **kwargs
) -> Dict:
    """
    Step 7-8: FFmpeg 최종 조립
    
    Args:
        adplan: 광고 기획
        processed_videos: 후처리된 Scene 영상
    
    Returns:
        {
            "final_video": Path,      # final.mp4
            "thumbnail": Path         # thumb.jpg
        }
    """
    logger.info("[Step 7-8] Final assembly starting...")
    
    try:
        final_video = paths.final_mp4
        video_cfg = cfg.get('video', {})
        fps = video_cfg.get('fps', 24)
        dissolve_frames = video_cfg.get('dissolve_frames', 12)
        
        # Step 7: Scene 합치기
        logger.info("   Step 7: Concatenating scenes with dissolve...")
        
        import subprocess
        
        # Calculate offsets for dissolve transition
        # Scene duration: 2.0s (from config or file)
        # Dissolve duration: 0.5s (approx 12 frames @ 24fps)
        
        # We assume all scenes have the same duration for simplicity now, 
        # or we could probe them. Let's trust the config/adplan for now or defaults.
        scene_durations = [2.0, 2.0, 2.0] # Fallback if probing fails
        fade_duration = 0.5
        
        offset1 = scene_durations[0] - fade_duration
        offset2 = offset1 + scene_durations[1] - fade_duration
        
        # Build filter complex for 3 videos
        filter_complex = (
            f"[0:v][1:v]xfade=transition=dissolve:duration={fade_duration}:offset={offset1}[v01]; "
            f"[v01][2:v]xfade=transition=dissolve:duration={fade_duration}:offset={offset2}[vout]"
        )
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(processed_videos[0]),
            '-i', str(processed_videos[1]),
            '-i', str(processed_videos[2]),
            '-filter_complex', filter_complex,
            '-map', '[vout]',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-r', str(fps),
            '-pix_fmt', 'yuv420p',
            str(paths.final_mp4)
        ]
        
        logger.info(f"   Executing FFmpeg command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
        
        # Step 8: BGM 및 자막 (TODO: 현재는 비디오만 병합)
        logger.info("   Step 8: BGM/Subtitle skipped (Placeholders). Video merged.")

        # 썸네일 생성 (첫 프레임)
        logger.info("   Generating thumbnail...")
        
        thumb_cmd = [
            'ffmpeg', '-y',
            '-i', str(paths.final_mp4),
            '-vf', 'select=eq(n\\,0)',
            '-vframes', '1',
            str(paths.thumb_jpg)
        ]
        subprocess.run(thumb_cmd, check=True, stderr=subprocess.PIPE)

        
        logger.info(f"[Step 7-8] Completed:")
        logger.info(f"   Final video: {final_video}")
        logger.info(f"   Thumbnail: {paths.thumb_jpg}")
        
        return {
            "final_video": final_video,
            "thumbnail": paths.thumb_jpg
        }
        
    except Exception as e:
        logger.error(f"[Step 7-8] Failed: {e}")
        raise
