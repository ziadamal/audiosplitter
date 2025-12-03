"""
Audio utility functions for file handling, conversion, and analysis.
"""
import os
import hashlib
import uuid
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
import soundfile as sf
import librosa
import numpy as np
from pydub import AudioSegment
import logging

logger = logging.getLogger(__name__)


def generate_job_id(filename: str) -> str:
    """Generate a unique job ID"""
    import time
    data = f"{filename}-{time.time()}-{uuid.uuid4()}"
    return hashlib.md5(data.encode()).hexdigest()[:16]


def get_audio_info(file_path: Path) -> Dict[str, Any]:
    """Get information about an audio file."""
    try:
        info = sf.info(file_path)
        return {
            "duration_seconds": info.duration,
            "sample_rate": info.samplerate,
            "channels": info.channels,
            "format": info.format,
            "subtype": info.subtype,
            "frames": info.frames
        }
    except Exception as e:
        logger.warning(f"soundfile couldn't read {file_path}, trying pydub: {e}")
        audio = AudioSegment.from_file(file_path)
        return {
            "duration_seconds": len(audio) / 1000.0,
            "sample_rate": audio.frame_rate,
            "channels": audio.channels,
            "format": file_path.suffix.lstrip('.'),
            "subtype": None,
            "frames": len(audio.get_array_of_samples()) // audio.channels
        }


def convert_to_wav(
    input_path: Path,
    output_path: Path,
    target_sr: int = 44100,
    mono: bool = False
) -> Path:
    """Convert audio file to WAV format."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_frame_rate(target_sr)
    
    if mono:
        audio = audio.set_channels(1)
    
    audio.export(output_path, format='wav')
    logger.info(f"Converted {input_path} to {output_path}")
    
    return output_path


def validate_audio_file(
    file_path: Path,
    allowed_extensions: set,
    max_size_mb: int
) -> Tuple[bool, str]:
    """Validate an uploaded audio file."""
    ext = file_path.suffix.lower().lstrip('.')
    if ext not in allowed_extensions:
        return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
    
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File too large. Maximum size: {max_size_mb}MB"
    
    try:
        info = get_audio_info(file_path)
        if info["duration_seconds"] < 1:
            return False, "Audio file is too short (minimum 1 second)"
        if info["duration_seconds"] > 600:  # 10 minutes max for free tier
            return False, "Audio file is too long (maximum 10 minutes for free tier)"
    except Exception as e:
        return False, f"Invalid audio file: {str(e)}"
    
    return True, ""


def estimate_processing_time(duration_seconds: float) -> float:
    """Estimate processing time in seconds."""
    # Faster estimates for fallback mode
    return duration_seconds * 2


SPEAKER_COLORS = [
    "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
    "#EC4899", "#06B6D4", "#F97316", "#6366F1", "#84CC16",
]

NOISE_COLOR = "#6B7280"


def get_speaker_color(speaker_index: int) -> str:
    """Get a consistent color for a speaker"""
    return SPEAKER_COLORS[speaker_index % len(SPEAKER_COLORS)]


def format_time(seconds: float) -> str:
    """Format seconds as MM:SS or HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
