"""
Real-CUGAN Model Loader
Handles video upscaling using Real-CUGAN (Cartoon Universal GAN).
Repository: bilibili/ailab Real-CUGAN
"""
import torch
import cv2
import numpy as np
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class RealCUGANLoader:
    def __init__(self, device: str = "cuda", model_name: str = "pro"):
        """
        Initialize Real-CUGAN loader.
        
        Args:
            device: Device to load model on ("cuda" or "cpu")
            model_name: Model variant ("pro", "conservative", "denoise3x")
        """
        self.device = device
        self.model_name = model_name
        self.model = None
        
    def load(self):
        """Load the Real-CUGAN model."""
        if self.model is not None:
            logger.info("Real-CUGAN already loaded")
            return
            
        logger.info(f"Loading Real-CUGAN ({self.model_name})")
        
        try:
            # Import Real-CUGAN (assuming it's installed)
            from .cugan_arch import RealCUGAN
            
            # Load model weights
            model_path = f"models/real_cugan/up2x-latest-{self.model_name}.pth"
            self.model = RealCUGAN(scale=2)
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("Real-CUGAN loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Real-CUGAN: {e}")
            raise
            
    def unload(self):
        """Unload the model to free VRAM."""
        if self.model is not None:
            logger.info("Unloading Real-CUGAN")
            del self.model
            self.model = None
            torch.cuda.empty_cache()
            
    @torch.no_grad()
    def upscale_video(
        self,
        input_video_path: str,
        output_video_path: str,
        scale: int = 2,
        tile_size: int = 256
    ) -> str:
        """
        Upscale video using Real-CUGAN.
        
        Args:
            input_video_path: Path to input video
            output_video_path: Path to save upscaled video
            scale: Upscaling factor (2 or 4)
            tile_size: Tile size for processing (smaller = less VRAM)
            
        Returns:
            Path to upscaled video
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")
            
        logger.info(f"Upscaling video by {scale}x")
        
        try:
            # Read input video
            cap = cv2.VideoCapture(input_video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Setup output video writer
            new_width = width * scale
            new_height = height * scale
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_video_path, fourcc, fps, (new_width, new_height))
            
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Upscale frame
                upscaled_frame = self._upscale_frame(frame, scale, tile_size)
                out.write(upscaled_frame)
                
                frame_count += 1
                if frame_count % 10 == 0:
                    logger.info(f"Processed {frame_count} frames")
            
            cap.release()
            out.release()
            
            logger.info(f"Upscaled video saved to: {output_video_path}")
            return output_video_path
            
        except Exception as e:
            logger.error(f"Video upscaling failed: {e}")
            raise
            
    def _upscale_frame(self, frame: np.ndarray, scale: int, tile_size: int) -> np.ndarray:
        """Upscale a single frame using tiling."""
        h, w, c = frame.shape
        
        # Process in tiles to manage VRAM
        tiles = []
        for y in range(0, h, tile_size):
            for x in range(0, w, tile_size):
                tile = frame[y:y+tile_size, x:x+tile_size]
                
                # Preprocess
                tile_tensor = torch.from_numpy(tile).permute(2, 0, 1).float() / 255.0
                tile_tensor = tile_tensor.unsqueeze(0).to(self.device)
                
                # Upscale
                with torch.no_grad():
                    upscaled_tile = self.model(tile_tensor)
                    upscaled_tile = upscaled_tile.squeeze(0).permute(1, 2, 0).cpu().numpy()
                    upscaled_tile = (upscaled_tile * 255).astype(np.uint8)
                
                tiles.append({
                    'tile': upscaled_tile,
                    'x': x * scale,
                    'y': y * scale
                })
        
        # Stitch tiles
        output = np.zeros((h * scale, w * scale, c), dtype=np.uint8)
        for tile_info in tiles:
            tile = tile_info['tile']
            x, y = tile_info['x'], tile_info['y']
            th, tw = tile.shape[:2]
            output[y:y+th, x:x+tw] = tile
        
        return output
        
    def estimate_vram(self) -> float:
        """Estimate VRAM usage in GB."""
        # Real-CUGAN is lightweight: ~1-2GB depending on tile size
        return 2.0
