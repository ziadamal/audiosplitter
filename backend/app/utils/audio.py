"""
Audio utility functions for file handling, conversion, and analysis.
"""
import os
import hashlib
import uuid
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import soundfile as sf
import librosa
import numpy as np
from pydub import AudioSegment
import logging

logger = logging.getLogger(__name__)


def generate_job_id(filename: str) -> str:
    """Generate a unique job ID based on filename and timestamp"""
    import time
    data = f"{filename}-{time.time()}-{uuid.uuid4()}"
    return hashlib.md5(data.encode()).hexdigest()[:16]


def get_audio_info(file_path: Path) -> Dict[str, Any]:
    """
    Get information about an audio file.
    
    Returns:
        Dictionary with duration, sample_rate, channels, format
    """
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
        # Fallback to pydub for formats soundfile can't handle
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
    """
    Convert audio file to WAV format.
    
    Args:
        input_path: Input audio file
        output_path: Output WAV file path
        target_sr: Target sample rate
        mono: Convert to mono if True
    
    Returns:
        Path to converted file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use pydub for broad format support
    audio = AudioSegment.from_file(input_path)
    
    # Convert to target sample rate
    audio = audio.set_frame_rate(target_sr)
    
    # Convert to mono if requested
    if mono:
        audio = audio.set_channels(1)
    
    # Export as WAV
    audio.export(output_path, format='wav')
    logger.info(f"Converted {input_path} to {output_path}")
    
    return output_path


def validate_audio_file(
    file_path: Path,
    allowed_extensions: set,
    max_size_mb: int
) -> Tuple[bool, str]:
    """
    Validate an uploaded audio file.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check extension
    ext = file_path.suffix.lower().lstrip('.')
    if ext not in allowed_extensions:
        return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
    
    # Check file size
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File too large. Maximum size: {max_size_mb}MB"
    
    # Try to read the file
    try:
        info = get_audio_info(file_path)
        if info["duration_seconds"] < 1:
            return False, "Audio file is too short (minimum 1 second)"
        if info["duration_seconds"] > 7200:  # 2 hours max
            return False, "Audio file is too long (maximum 2 hours)"
    except Exception as e:
        return False, f"Invalid audio file: {str(e)}"
    
    return True, ""


def get_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def cleanup_job_files(job_dir: Path):
    """Remove all files for a job"""
    import shutil
    if job_dir.exists():
        shutil.rmtree(job_dir)
        logger.info(f"Cleaned up job directory: {job_dir}")


def estimate_processing_time(duration_seconds: float) -> float:
    """
    Estimate processing time in seconds based on audio duration.
    
    This is a rough estimate. Actual time depends on:
    - Hardware (GPU vs CPU)
    - Model being used
    - Number of speakers
    """
    # Rough estimates based on testing:
    # - Source separation: ~0.5x realtime on GPU, ~3x on CPU
    # - Diarization: ~0.3x realtime on GPU, ~2x on CPU
    
    # Conservative CPU estimate
    separation_time = duration_seconds * 3
    diarization_time = duration_seconds * 2
    
    return separation_time + diarization_time


SPEAKER_COLORS = [
    "#3B82F6",  # Blue
    "#EF4444",  # Red
    "#10B981",  # Green
    "#F59E0B",  # Amber
    "#8B5CF6",  # Purple
    "#EC4899",  # Pink
    "#06B6D4",  # Cyan
    "#F97316",  # Orange
    "#6366F1",  # Indigo
    "#84CC16",  # Lime
]

NOISE_COLOR = "#6B7280"  # Gray


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
