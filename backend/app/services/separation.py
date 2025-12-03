"""
Audio source separation service.

This version uses lightweight fallback methods that work on Render's free tier.
For production with GPU, uncomment the Demucs imports.
"""
import os
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


class SourceSeparator:
    """
    Separates audio sources using filtering techniques.
    
    For voice-focused separation, we extract:
    - Vocals track (contains all speakers)
    - Other track (background music, noise, etc.)
    """
    
    def __init__(self, model_name: str = "htdemucs", device: str = None):
        """
        Initialize the source separator.
        """
        self.model_name = model_name
        self.device = device or "cpu"
        self._model = "fallback"  # Always use fallback on free tier
        logger.info(f"SourceSeparator initialized with fallback mode")
        
    def separate(
        self,
        input_path: Path,
        output_dir: Path,
        stems: List[str] = None
    ) -> Dict[str, Path]:
        """
        Separate audio into stems using filtering.
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory to save separated tracks
            stems: Which stems to extract. Default: ['vocals', 'other']
        
        Returns:
            Dictionary mapping stem names to output file paths
        """
        stems = stems or ['vocals', 'other']
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Separating {input_path} into stems: {stems}")
        
        return self._fallback_separation(input_path, output_dir, stems)
    
    def _fallback_separation(
        self,
        input_path: Path,
        output_dir: Path,
        stems: List[str]
    ) -> Dict[str, Path]:
        """
        Fallback separation using high-pass/low-pass filtering.
        Works without GPU or heavy ML models.
        """
        from pydub import AudioSegment
        from scipy import signal
        import soundfile as sf
        
        logger.info("Using fallback separation (filtering)")
        
        # Load audio
        audio = AudioSegment.from_file(input_path)
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        
        # Normalize samples
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            samples = samples / max_val
        
        if audio.channels == 2:
            samples = samples.reshape((-1, 2))
        else:
            samples = samples.reshape((-1, 1))
        
        sample_rate = audio.frame_rate
        
        results = {}
        
        if 'vocals' in stems:
            # Bandpass filter for voice frequencies (85-3400 Hz for speech)
            # Extended to 80-8000 Hz for better quality
            low_freq = 80 / (sample_rate / 2)
            high_freq = min(8000 / (sample_rate / 2), 0.99)  # Ensure < 1
            
            b, a = signal.butter(4, [low_freq, high_freq], btype='band')
            vocals = signal.filtfilt(b, a, samples, axis=0)
            
            vocals_path = output_dir / "vocals.wav"
            self._save_array_as_wav(vocals, sample_rate, vocals_path)
            results['vocals'] = vocals_path
            logger.info(f"Saved vocals to {vocals_path}")
        
        if 'other' in stems:
            # Everything outside voice frequencies
            # Low frequencies (bass, rumble) + high frequencies (hiss, cymbals)
            
            # Low-pass for bass
            low_cutoff = 80 / (sample_rate / 2)
            b_low, a_low = signal.butter(4, low_cutoff, btype='low')
            bass = signal.filtfilt(b_low, a_low, samples, axis=0)
            
            # High-pass for treble/noise
            high_cutoff = min(8000 / (sample_rate / 2), 0.99)
            b_high, a_high = signal.butter(4, high_cutoff, btype='high')
            treble = signal.filtfilt(b_high, a_high, samples, axis=0)
            
            # Combine
            other = bass + treble
            
            other_path = output_dir / "other.wav"
            self._save_array_as_wav(other, sample_rate, other_path)
            results['other'] = other_path
            logger.info(f"Saved other to {other_path}")
        
        return results
    
    def _save_array_as_wav(self, samples: np.ndarray, sample_rate: int, path: Path):
        """Save numpy array as WAV file"""
        import soundfile as sf
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            samples = samples / max_val * 0.95
        
        sf.write(path, samples, sample_rate)


def separate_vocals_and_noise(
    input_path: Path,
    output_dir: Path,
    model_name: str = "htdemucs"
) -> Tuple[Path, Path]:
    """
    Convenience function to separate vocals from background noise.
    
    Returns:
        Tuple of (vocals_path, noise_path)
    """
    separator = SourceSeparator(model_name=model_name)
    results = separator.separate(input_path, output_dir, stems=['vocals', 'other'])
    
    return results.get('vocals'), results.get('other')
