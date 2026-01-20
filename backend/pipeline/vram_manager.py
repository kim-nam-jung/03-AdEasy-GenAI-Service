# pipeline/vram_manager.py
"""
VRAM 관리자
- GPU 메모리 모니터링
- 자동 정리 (Gate 1, Gate 2)
- 모델 언로드
"""

import torch
import gc
from typing import Optional
from common.logger import TaskLogger
from common.config import Config


class VRAMManager:
    """
    VRAM 관리자
    
    Gate 1: Step 전환 시 체크 (8GB 필요)
    Gate 2: 모델 로드 전 체크 (8GB 필요)
    """
    
    def __init__(self, logger: Optional[TaskLogger] = None, cfg: Optional[Config] = None):
        self.logger = logger
        self.cfg = cfg or Config.load()
        
        self.vram_policy = self.cfg.get('vram', {})
        self.gate1_threshold = self.vram_policy.get('gate1', {}).get('free_gb_required', 8)
        self.gate2_threshold = self.vram_policy.get('gate2', {}).get('free_gb_required', 8)
        self.cleanup_target = self.vram_policy.get('gate1', {}).get('cleanup_target_gb', 2)
    
    def get_vram_info(self) -> dict:
        """
        현재 VRAM 상태 조회
        
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
    
    def check_gate1(self) -> bool:
        """
        Gate 1: Step 전환 체크
        
        Returns:
            bool: 충분한 VRAM 확보 여부
        """
        info = self.get_vram_info()
        
        if self.logger:
            self.logger.info(f"   [VRAM Gate 1] Free: {info['free_gb']:.2f}GB / Required: {self.gate1_threshold}GB")
        
        if info['free_gb'] < self.gate1_threshold:
            if self.logger:
                self.logger.warning(f"   [VRAM Gate 1] Insufficient! Cleaning up...")
            self.cleanup()
            return False
        
        return True
    
    def check_gate2(self) -> bool:
        """
        Gate 2: 모델 로드 전 체크
        
        Returns:
            bool: 충분한 VRAM 확보 여부
        """
        info = self.get_vram_info()
        
        if self.logger:
            self.logger.info(f"   [VRAM Gate 2] Free: {info['free_gb']:.2f}GB / Required: {self.gate2_threshold}GB")
        
        if info['free_gb'] < self.gate2_threshold:
            if self.logger:
                self.logger.warning(f"   [VRAM Gate 2] Insufficient! Cleaning up...")
            self.cleanup()
            return False
        
        return True
    
    def cleanup(self):
        """
        VRAM 정리
        """
        if self.logger:
            self.logger.info("   [VRAM] Cleaning up...")
        
        # PyTorch 캐시 비우기
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        
        # Python GC
        gc.collect()
        
        info = self.get_vram_info()
        
        if self.logger:
            self.logger.info(f"   [VRAM] After cleanup: {info['free_gb']:.2f}GB free")
    
    def log_status(self, step_name: str = ""):
        """
        VRAM 상태 로깅
        """
        info = self.get_vram_info()
        
        if self.logger:
            prefix = f"[{step_name}] " if step_name else ""
            self.logger.info(f"   {prefix}VRAM: {info['allocated_gb']:.2f}GB / {info['total_gb']:.2f}GB")
