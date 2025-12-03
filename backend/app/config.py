"""
Application configuration using Pydantic Settings
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "VoxSplit Audio Separator"
    debug: bool = False
    
    # Paths - Use /tmp for Render compatibility
    upload_dir: Path = Path("/tmp/voxsplit/uploads")
    output_dir: Path = Path("/tmp/voxsplit/outputs")
    models_dir: Path = Path("/tmp/voxsplit/models")
    
    # Audio settings
    max_file_size_mb: int = 100  # Reduced for free tier
    allowed_extensions: set = {"mp3", "wav", "m4a", "flac", "ogg", "aac"}
    output_format: str = "wav"
    sample_rate: int = 44100
    
    # Processing
    demucs_model: str = "htdemucs"
    diarization_model: str = "pyannote/speaker-diarization-3.1"
    min_speakers: int = 1
    max_speakers: int = 5  # Reduced for faster processing
    
    # Hugging Face token (optional for fallback mode)
    hf_token: str = ""
    
    # Redis/Celery (not used in free tier)
    redis_url: str = "redis://localhost:6379/0"
    
    # CORS - Allow all for now
    cors_origins: list = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    
    # Create directories if they don't exist
    try:
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        settings.output_dir.mkdir(parents=True, exist_ok=True)
        settings.models_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create directories: {e}")
    
    return settings
