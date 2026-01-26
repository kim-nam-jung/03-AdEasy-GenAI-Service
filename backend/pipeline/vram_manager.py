# pipeline/vram_manager.py
"""
VRAM Manager
- GPU memory monitoring
- Automatic cleanup
- Model loading/unloading for simplified pipeline
"""

import torch
import gc
from typing import Optional, Dict, Any
from common.logger import TaskLogger
from common.config import Config


class VRAMManager:
    """
    VRAM Manager for 3-step pipeline
    
    Manages loading/unloading of:
    - Qwen-Image-Layered (Step 1)
    - LTX-2 Pro (Step 2)
    - RIFE (Step 3.1)
    - Real-CUGAN (Step 3.2)
    """
    
    def __init__(self, logger: Optional[TaskLogger] = None, cfg: Optional[Config] = None):
        self.logger = logger
        self.cfg = cfg or Config.load()
        
        # Model registry
        self.loaded_models: Dict[str, Any] = {}
        
        # VRAM thresholds
        self.vram_policy = self.cfg.get('vram', {})
        self.free_gb_required = self.vram_policy.get('free_gb_required', 8)
    
    def get_vram_info(self) -> dict:
        """
        Get current VRAM status
        
        Returns:
            {
                "total_gb": float,
                "allocated_gb": float,
                "free_gb": float
            }
        """
        if not torch.cuda.is_available():
            return {"total_gb": 0, "allocated_gb": 0, "free_gb": 0}
        
        total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        allocated = torch.cuda.memory_allocated(0) / (1024**3)
        free = total - allocated
        
        return {
            "total_gb": round(total, 2),
            "allocated_gb": round(allocated, 2),
            "free_gb": round(free, 2)
        }
    
    def load_model(self, model_name: str, loader: Any):
        """
        Load a model and track it in registry
        
        Args:
            model_name: Name of model (e.g., "qwen_layered", "ltx2_pro", etc.)
            loader: Model loader instance with load() method
        """
        if model_name in self.loaded_models:
            if self.logger:
                self.logger.info(f"   [VRAM] Model '{model_name}' already loaded")
            return
        
        # Check VRAM before loading
        info = self.get_vram_info()
        if info['free_gb'] < self.free_gb_required:
            if self.logger:
                self.logger.warning(f"   [VRAM] Low memory ({info['free_gb']:.2f}GB). Cleaning up...")
            self.cleanup()
        
        if self.logger:
            self.logger.info(f"   [VRAM] Loading model: {model_name}")
        
        loader.load()
        self.loaded_models[model_name] = loader
        
        self.log_status(f"After loading {model_name}")
    
    def unload_model(self, model_name: str):
        """
        Unload a model to free VRAM
        
        Args:
            model_name: Name of model to unload
        """
        if model_name not in self.loaded_models:
            if self.logger:
                self.logger.warning(f"   [VRAM] Model '{model_name}' not in registry")
            return
        
        if self.logger:
            self.logger.info(f"   [VRAM] Unloading model: {model_name}")
        
        loader = self.loaded_models[model_name]
        loader.unload()
        del self.loaded_models[model_name]
        
        self.cleanup()
        self.log_status(f"After unloading {model_name}")
    
    def unload_all(self):
        """
        Unload all models
        """
        if self.logger:
            self.logger.info("   [VRAM] Unloading all models")
        
        for model_name in list(self.loaded_models.keys()):
            self.unload_model(model_name)
    
    def cleanup(self):
        """
        Clean up VRAM and verify results.
        """
        if self.logger:
            self.logger.info("   [VRAM] Cleaning up...")
        
        # Clear PyTorch cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        
        # Python GC
        gc.collect()
        
        info = self.get_vram_info()
        
        if self.logger:
            self.logger.info(f"   [VRAM] After cleanup: {info['free_gb']:.2f}GB free")
            
            # Warning if still low
            if info['total_gb'] > 0:
                usage_pct = (info['allocated_gb'] / info['total_gb']) * 100
                if usage_pct > 90:
                    self.logger.warning(f"   [VRAM] HIGH RESIDENCY DETECTED: {usage_pct:.1f}% still in use after cleanup.")
    
    def log_status(self, step_name: str = ""):
        """
        Log VRAM status
        """
        info = self.get_vram_info()
        
        if self.logger:
            prefix = f"[{step_name}] " if step_name else ""
            self.logger.info(f"   {prefix}VRAM: {info['allocated_gb']:.2f}GB / {info['total_gb']:.2f}GB (Free: {info['free_gb']:.2f}GB)")
