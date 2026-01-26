import os
import yaml
from pathlib import Path
from typing import List, Union, Any, Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator

# ==============================================================================
# 1. Pydantic Settings (FastAPI & System Config)
# ==============================================================================
class Settings(BaseSettings):
    PROJECT_NAME: str = "AdEasy GenAI Service"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: Any = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str):
            if v.startswith("["):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    return [v]
            return [i.strip() for i in v.split(",")]
        return v

    # Redis (Env var takes precedence)
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Paths
    UPLOAD_DIR: str = "/app/data/inputs"
    OUTPUT_DIR: str = "/app/outputs"
    MODEL_DIR: str = "/app/models"
    
    # vLLM
    VLLM_URL: Optional[str] = None  # e.g., "http://localhost:8000/v1"
    VLLM_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    
    # Security
    API_KEY: str = "adeasy-secret-key"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra='ignore')

settings = Settings()


# ==============================================================================
# 2. Legacy YAML Config (Pipeline Config)
# ==============================================================================
class Config:
    """Global config loader (singleton pattern) for variables.yaml logic"""
    _instance: 'Config | None' = None
    _data: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def load(cls, config_path: Path | str | None = None) -> "Config":
        instance = cls()
        if not instance._data:
            if config_path is None:
                # Try to locate config/config.yaml relative to project root
                # Assuming this file is in backend/app/core/config.py
                # Root is backend/
                root = Path(__file__).resolve().parents[2] 
                config_path = root / "config" / "config.yaml"
            
            if not isinstance(config_path, Path):
                config_path = Path(config_path)

            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    instance._data = yaml.safe_load(f) or {}
                
                # 환경변수 치환 (REDIS_URL 등)
                instance._resolve_env_vars()
            else:
                print(f"Warning: Config file not found at {config_path}")
                instance._data = {}
        
        return instance

    def _resolve_env_vars(self) -> None:
        """환경변수 값 치환"""
        redis_url_env = self._data.get("redis", {}).get("url_env")
        if redis_url_env:
            redis_url = os.getenv(redis_url_env)
            if redis_url:
                if "redis" in self._data:
                    self._data["redis"]["url"] = redis_url

    def get(self, key: str, default: Any = None) -> Any:
        """Dot notation: 'models.qwen_vl.repo_id'"""
        keys = key.split(".")
        val = self._data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
            if val is None:
                return default
        return val

    def __getitem__(self, key: str) -> Any:
        return self.get(key)
