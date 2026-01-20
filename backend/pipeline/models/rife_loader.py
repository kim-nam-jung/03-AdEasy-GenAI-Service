"""
RIFE 4.26 Model Loader
Handles frame interpolation using RIFE (Real-Time Intermediate Flow Estimation).
Repository: hzwer/Practical-RIFE
"""
import torch
import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class RIFELoader:
    def __init__(self, device: str = "cuda", model_version: str = "4.26"):
        """
        Initialize RIFE loader.
        
        Args:
            device: Device to load model on ("cuda" or "cpu")
            model_version: RIFE model version (4.26 recommended)
        """
        self.device = device
        self.model_version = model_version
        self.model = None
        
    def load(self):
        """Load the RIFE model."""
        if self.model is not None:
            logger.info("RIFE already loaded")
            return
            
        logger.info(f"Loading RIFE v{self.model_version}")
        
        try:
            # Import RIFE model (assuming RIFE is installed)
            from .rife_arch import IFNet
            
            # Load model weights
            model_path = f"models/rife/rife{self.model_version}.pth"
            self.model = IFNet()
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("RIFE loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load RIFE: {e}")
            raise
            
    def unload(self):
        """Unload the model to free VRAM."""
        if self.model is not None:
            logger.info("Unloading RIFE")
            del self.model
            self.model = None
            torch.cuda.empty_cache()
            
    @torch.no_grad()
    def interpolate_video(
        self,
        input_video_path: str,
        output_video_path: str,
        target_fps: int = 48,
        scale: float = 1.0
    ) -> str:
        """
        Interpolate frames in video to increase FPS.
        
        Args:
            input_video_path: Path to input video
            output_video_path: Path to save interpolated video
            target_fps: Target FPS after interpolation
            scale: Upscaling factor (1.0 = no scaling)
            
        Returns:
            Path to interpolated video
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")
            
        logger.info(f"Interpolating video to {target_fps} FPS")
        
        try:
            # Read input video
            cap = cv2.VideoCapture(input_video_path)
            original_fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Calculate interpolation factor
            interp_factor = int(target_fps / original_fps)
            
            logger.info(f"Original: {original_fps} FPS, Target: {target_fps} FPS, Factor: {interp_factor}x")
            
            # Setup output video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_video_path, fourcc, target_fps, (width, height))
            
            # Read all frames
            frames = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frames.append(frame)
            cap.release()
            
            # Interpolate between each pair of frames
            interpolated_frames = []
            for i in range(len(frames) - 1):
                frame0 = self._preprocess_frame(frames[i])
                frame1 = self._preprocess_frame(frames[i + 1])
                
                # Add original frame
                interpolated_frames.append(frames[i])
                
                # Generate intermediate frames
                for j in range(1, interp_factor):
                    timestep = j / interp_factor
                    interp_frame = self._infer(frame0, frame1, timestep)
                    interpolated_frames.append(interp_frame)
            
            # Add last frame
            interpolated_frames.append(frames[-1])
            
            # Write interpolated frames
            for frame in interpolated_frames:
                out.write(frame)
            out.release()
            
            logger.info(f"Interpolated video saved to: {output_video_path}")
            return output_video_path
            
        except Exception as e:
            logger.error(f"Frame interpolation failed: {e}")
            raise
            
    def _preprocess_frame(self, frame: np.ndarray) -> torch.Tensor:
        """Convert OpenCV frame to tensor."""
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = torch.from_numpy(frame).permute(2, 0, 1).float() / 255.0
        return frame.unsqueeze(0).to(self.device)
        
    def _infer(self, frame0: torch.Tensor, frame1: torch.Tensor, timestep: float) -> np.ndarray:
        """Infer intermediate frame."""
        with torch.no_grad():
            output = self.model(frame0, frame1, timestep)
            output = output.squeeze(0).permute(1, 2, 0).cpu().numpy()
            output = (output * 255).astype(np.uint8)
            output = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
        return output
        
    def estimate_vram(self) -> float:
        """Estimate VRAM usage in GB."""
        # RIFE is lightweight: ~1-2GB
        return 1.5
