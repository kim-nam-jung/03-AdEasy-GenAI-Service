"""
Qwen-Image-Layered Model Loader
Handles loading and inference for Qwen-Image-Layered segmentation model.
Model: Qwen/Qwen-Image-Layered (HuggingFace)
Official API: https://huggingface.co/Qwen/Qwen-Image-Layered
"""
import torch
from PIL import Image
from diffusers import QwenImageLayeredPipeline
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class QwenImageLayeredLoader:
    def __init__(self, device: str = "cuda", dtype: torch.dtype = torch.bfloat16):
        """
        Initialize Qwen-Image-Layered loader.
        
        Args:
            device: Device to load model on ("cuda" or "cpu")
            dtype: Data type for model weights (bfloat16 recommended for L4)
        """
        self.device = device
        self.dtype = dtype
        self.pipeline = None
        self.model_id = "Qwen/Qwen-Image-Layered"
        
    def load(self):
        """Load the Qwen-Image-Layered pipeline."""
        if self.pipeline is not None:
            logger.info("Qwen-Image-Layered already loaded")
            return
            
        logger.info(f"Loading Qwen-Image-Layered from {self.model_id}")
        
        try:
            self.pipeline = QwenImageLayeredPipeline.from_pretrained(
                self.model_id,
                torch_dtype=self.dtype
            )
            self.pipeline = self.pipeline.to(self.device)
            self.pipeline.set_progress_bar_config(disable=None)
            
            logger.info("Qwen-Image-Layered loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Qwen-Image-Layered: {e}")
            raise
            
    def unload(self):
        """Unload the model to free VRAM."""
        if self.pipeline is not None:
            logger.info("Unloading Qwen-Image-Layered")
            del self.pipeline
            self.pipeline = None
            torch.cuda.empty_cache()
            
    @torch.no_grad()
    def segment(
        self,
        image_path: str,
        num_layers: int = 4,
        resolution: int = 640,
        num_inference_steps: int = 50,
        true_cfg_scale: float = 4.0,
        seed: Optional[int] = None
    ) -> List[Image.Image]:
        """
        Segment an image into RGBA layers.
        
        Args:
            image_path: Path to input image
            num_layers: Number of layers to extract (3-8)
            resolution: Processing resolution (640 or 1024)
            num_inference_steps: Number of denoising steps (default: 50)
            true_cfg_scale: CFG scale (default: 4.0)
            seed: Random seed for reproducibility
            
        Returns:
            List of PIL Images (RGBA), with layers sorted from foreground to background
        """
        if self.pipeline is None:
            raise RuntimeError("Pipeline not loaded. Call load() first.")
            
        logger.info(f"Segmenting image: {image_path} (layers={num_layers}, res={resolution})")
        
        try:
            # Load and convert image to RGBA
            image = Image.open(image_path).convert("RGBA")
            
            # Prepare generation parameters
            generator = None
            if seed is not None:
                generator = torch.Generator(device=self.device).manual_seed(seed)
            
            inputs = {
                "image": image,
                "generator": generator,
                "true_cfg_scale": true_cfg_scale,
                "negative_prompt": " ",  # Empty negative prompt
                "num_inference_steps": num_inference_steps,
                "num_images_per_prompt": 1,
                "layers": num_layers,
                "resolution": resolution,  # 640 or 1024
                "cfg_normalize": True,  # Enable CFG normalization
                "use_en_prompt": True,  # Automatic English caption
            }
            
            # Generate layers
            with torch.inference_mode():
                output = self.pipeline(**inputs)
                layers = output.images[0]  # List of RGBA PIL Images
            
            logger.info(f"Successfully extracted {len(layers)} layers")
            return layers
            
        except Exception as e:
            logger.error(f"Segmentation failed: {e}")
            raise
            
    def estimate_vram(self) -> float:
        """Estimate VRAM usage in GB."""
        # Qwen-Image-Layered is based on diffusion model
        # bfloat16: 2 bytes per param
        # Estimated: ~8-10GB including activations
        return 10.0
