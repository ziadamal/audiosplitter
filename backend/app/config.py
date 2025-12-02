"""
Application configuration using Pydantic Settings
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "VoxSplit Audio Separator"
    debug: bool = False
    
    # Paths
    upload_dir: Path = Path("/tmp/voxsplit/uploads")
    output_dir: Path = Path("/tmp/voxsplit/outputs")
    models_dir: Path = Path("/tmp/voxsplit/models")
    
    # Audio settings
    max_file_size_mb: int = 500
    allowed_extensions: set = {"mp3", "wav", "m4a", "flac", "ogg", "aac"}
    output_format: str = "wav"
    sample_rate: int = 44100
    
    # Processing
    demucs_model: str = "htdemucs"  # Best quality model
    diarization_model: str = "pyannote/speaker-diarization-3.1"
    min_speakers: int = 1
    max_speakers: int = 10
    
    # Hugging Face token (required for pyannote models)
    hf_token: str = ""
    
    # Redis/Celery
    redis_url: str = "redis://localhost:6379/0"
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    
    # Create directories if they don't exist
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.models_dir.mkdir(parents=True, exist_ok=True)
    
    return settings
