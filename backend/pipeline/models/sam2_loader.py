"""
SAM 2 (Segment Anything Model 2) Loader
Handles loading and inference for SAM 2 segmentation model.
Model: facebook/sam2-hiera-large (HuggingFace)
"""
import torch
import numpy as np
from PIL import Image
try:
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor
except ImportError as e:
    # We will need to install sam2 on the VM
    # Log the error to debug
    logging.getLogger(__name__).error(f"SAM 2 Import Failed: {e}")
    build_sam2 = None
    SAM2ImagePredictor = None

from typing import List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SAM2Loader:
    def __init__(self, device: str = "cuda", dtype: torch.dtype = torch.bfloat16):
        """
        Initialize SAM 2 loader.
        
        Args:
            device: Device to load model on ("cuda" or "cpu")
            dtype: Data type for model weights
        """
        self.device = device
        self.dtype = dtype
        self.predictor = None
        self.model_id = "facebook/sam2-hiera-large"
        
        # SAM 2 checkpoint and config
        # Will be resolved after package installation
        self.checkpoint_path = None
        self.config_name = "sam2_hiera_l.yaml"  # Config name from SAM 2 package
        
    def load(self):
        """Load the SAM 2 model."""
        if self.predictor is not None:
            logger.info("SAM 2 already loaded")
            return
            
        logger.info(f"Loading SAM 2 from {self.model_id}")
        
        try:
            # Resolve checkpoint path
            if self.checkpoint_path is None:
                # Try to find it in the local_dir
                local_dir = Path("/app/models/sam2")
                pt_files = list(local_dir.glob("*.pt"))
                if pt_files:
                    self.checkpoint_path = str(pt_files[0])
                    logger.info(f"Using checkpoint: {self.checkpoint_path}")
                else:
                    raise FileNotFoundError(f"SAM 2 checkpoint not found in models/sam2")
                
                # Local config resolution removed - rely on package defaults
                # config_name should be "sam2_hiera_l.yaml" as predefined
                
            # Build SAM 2 model using config name and checkpoint path
            # Note: config_name must be relative to sam2 package configs if build_sam2 uses hydra.initialize_config_module
            model = build_sam2(self.config_name, self.checkpoint_path, device=self.device)
            self.predictor = SAM2ImagePredictor(model)
            
            logger.info("SAM 2 loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load SAM 2: {e}")
            raise
            
    def unload(self):
        """Unload the model to free VRAM."""
        if self.predictor is not None:
            logger.info("Unloading SAM 2")
            del self.predictor
            self.predictor = None
            torch.cuda.empty_cache()
            
    @torch.no_grad()
    def segment_product(
        self,
        image_path: str,
        threshold: float = 0.5,
        prompt_mode: str = "center"  # center, grid
    ) -> Image.Image:
        """
        Segment context-aware product.
        Args:
            prompt_mode: 'center' for single point, 'grid' for multiple points.
        """
        if self.predictor is None:
            raise RuntimeError("Predictor not loaded. Call load() first.")
            
        logger.info(f"Segmenting image: {image_path} with mode: {prompt_mode}")
        
        try:
            # Load image
            image = Image.open(image_path).convert("RGB")
            image_np = np.array(image)
            self.predictor.set_image(image_np)
            
            w, h = image.size
            
            if prompt_mode == "grid":
                # Use a 2x2 grid of positive points to catch larger objects
                input_point = np.array([
                    [w//3, h//3], [2*w//3, h//3],
                    [w//3, 2*h//3], [2*w//3, 2*h//3],
                    [w//2, h//2] # Center too
                ])
                input_label = np.array([1, 1, 1, 1, 1])
            else:
                # Default: Center point
                input_point = np.array([[w // 2, h // 2]])
                input_label = np.array([1])
            
            masks, scores, logits = self.predictor.predict(
                point_coords=input_point,
                point_labels=input_label,
                multimask_output=True,
            )
            
            # Select best mask
            best_mask_idx = np.argmax(scores)
            mask = masks[best_mask_idx]
            
            # Create RGBA
            rgba_image = Image.open(image_path).convert("RGBA")
            rgba_np = np.array(rgba_image)
            rgba_np[..., 3] = (mask * 255).astype(np.uint8)
            
            return Image.fromarray(rgba_np)
            
        except Exception as e:
            logger.error(f"Background removal failed: {e}")
            raise
            
        except Exception as e:
            logger.error(f"Background removal failed: {e}")
            raise
            
    def estimate_vram(self) -> float:
        """Estimate VRAM usage in GB."""
        # SAM 2 Hiera Large is relatively small
        return 2.0
