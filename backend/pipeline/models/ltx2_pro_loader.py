"""
LTX-Video Model Loader
Handles loading and inference for LTX-Video image-to-video generation.
Model: Lightricks/LTX-Video (HuggingFace)
Official API: https://huggingface.co/Lightricks/LTX-Video

Note: This uses the base LTX-Video model. For higher quality, consider using
the LTX-2 Pro version when available.
"""
import torch
from PIL import Image
from diffusers import LTXConditionPipeline
from diffusers.pipelines.ltx.pipeline_ltx_condition import LTXVideoCondition
from diffusers.utils import export_to_video, load_video
from typing import Optional
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class LTX2ProLoader:
    def __init__(self, device: str = "cuda", use_fp8: bool = False):
        """
        Initialize LTX-Video loader.
        
        Args:
            device: Device to load model on ("cuda" or "cpu")
            use_fp8: Use FP8 quantization (not yet available, placeholder)
        """
        self.device = device
        self.use_fp8 = use_fp8  # Placeholder for future FP8 support
        self.pipeline = None
        # Using LTX-Video 0.9.8 (latest stable version)
        self.model_id = "Lightricks/LTX-Video-0.9.8-dev"
        
    def load(self):
        """Load the LTX-Video pipeline."""
        if self.pipeline is not None:
            logger.info("LTX-Video already loaded")
            return
            
        logger.info(f"Loading LTX-Video from {self.model_id}")
        
        try:
            # Load with bfloat16 for memory efficiency
            # FP8 support to be added when available
            torch_dtype = torch.bfloat16
            
            self.pipeline = LTXConditionPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch_dtype
            )
            
            self.pipeline.to(self.device)
            
            # Enable VAE tiling for large resolutions
            self.pipeline.vae.enable_tiling()
            
            logger.info("LTX-Video loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load LTX-Video: {e}")
            raise
            
    def unload(self):
        """Unload the pipeline to free VRAM."""
        if self.pipeline is not None:
            logger.info("Unloading LTX-Video")
            del self.pipeline
            self.pipeline = None
            torch.cuda.empty_cache()
            
    def _round_to_vae_resolution(self, height: int, width: int) -> tuple:
        """Round resolution to be acceptable by VAE."""
        compression_ratio = self.pipeline.vae_spatial_compression_ratio
        height = height - (height % compression_ratio)
        width = width - (width % compression_ratio)
        return height, width
            
    @torch.no_grad()
    def generate_video(
        self,
        image_path: str,
        prompt: str,
        num_frames: int = 96,
        width: int = 832,
        height: int = 480,
        fps: int = 24,
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        negative_prompt: str = "worst quality, inconsistent motion, blurry, jittery, distorted"
    ) -> str:
        """
        Generate video from image using LTX-Video I2V.
        
        Args:
            image_path: Path to input image (segmented product)
            prompt: Text prompt for video generation
            num_frames: Number of frames to generate (96 recommended)
            width: Video width (must be divisible by VAE compression ratio)
            height: Video height (must be divisible by VAE compression ratio)
            fps: Frames per second for output video
            num_inference_steps: Number of denoising steps (20-40)
            guidance_scale: Classifier-free guidance scale
            seed: Random seed for reproducibility
            negative_prompt: Negative prompt to avoid unwanted features
            
        Returns:
            Path to generated video file
        """
        if self.pipeline is None:
            raise RuntimeError("Pipeline not loaded. Call load() first.")
            
        # Round resolution to VAE-compatible values
        height, width = self._round_to_vae_resolution(height, width)
        
        logger.info(f"Generating video: {num_frames} frames @ {width}x{height}")
        
        try:
            # Load input image and prepare as condition
            image = Image.open(image_path).convert("RGB")
            
            # Convert image to video format for conditioning
            video = load_video(export_to_video([image]))
            condition = LTXVideoCondition(video=video, frame_index=0)
            
            # Set random seed
            generator = None
            if seed is not None:
                generator = torch.Generator(device=self.device).manual_seed(seed)
                
            # Generate video
            output = self.pipeline(
                conditions=[condition],
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                generator=generator,
                output_type="pil"
            )
            
            video_frames = output.frames[0]
            
            # Save video
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = "outputs/videos"
            os.makedirs(output_dir, exist_ok=True)
            output_path = f"{output_dir}/ltx_raw_{timestamp}.mp4"
            
            export_to_video(video_frames, output_path, fps=fps)
            
            logger.info(f"Video saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            raise
            
    def estimate_vram(self) -> float:
        """Estimate VRAM usage in GB."""
        # LTX-Video with bfloat16: ~14-18GB with VAE tiling
        # FP8 would reduce to ~10-12GB when available
        return 16.0 if not self.use_fp8 else 12.0
