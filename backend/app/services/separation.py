"""
Audio source separation service using Facebook's Demucs model.

Demucs is a state-of-the-art source separation model that can separate:
- Vocals (all human voices)
- Drums
- Bass
- Other (instruments, noise, etc.)

We use the 'htdemucs' model which gives the best quality for voice separation.
"""
import os
import torch
import torchaudio
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import subprocess
import json
import logging

logger = logging.getLogger(__name__)


class SourceSeparator:
    """
    Separates audio sources using Demucs.
    
    For voice-focused separation, we extract:
    - Vocals track (contains all speakers)
    - Other track (background music, noise, etc.)
    """
    
    def __init__(self, model_name: str = "htdemucs", device: str = None):
        """
        Initialize the source separator.
        
        Args:
            model_name: Demucs model to use. Options:
                - 'htdemucs': Best quality, hybrid transformer
                - 'htdemucs_ft': Fine-tuned version
                - 'mdx_extra': Good for music
            device: 'cuda' or 'cpu'. Auto-detected if None.
        """
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model = None
        
    def _load_model(self):
        """Lazy load the Demucs model"""
        if self._model is None:
            try:
                from demucs.pretrained import get_model
                from demucs.apply import apply_model
                
                logger.info(f"Loading Demucs model: {self.model_name}")
                self._model = get_model(self.model_name)
                self._model.to(self.device)
                self._model.eval()
                logger.info(f"Model loaded on {self.device}")
            except ImportError:
                logger.warning("Demucs not available, using fallback separation")
                self._model = "fallback"
    
    def separate(
        self,
        input_path: Path,
        output_dir: Path,
        stems: List[str] = None
    ) -> Dict[str, Path]:
        """
        Separate audio into stems.
        
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
        
        self._load_model()
        
        if self._model == "fallback":
            return self._fallback_separation(input_path, output_dir, stems)
        
        # Load audio
        waveform, sample_rate = torchaudio.load(input_path)
        
        # Resample if needed (Demucs expects 44100 Hz)
        if sample_rate != 44100:
            resampler = torchaudio.transforms.Resample(sample_rate, 44100)
            waveform = resampler(waveform)
            sample_rate = 44100
        
        # Ensure stereo
        if waveform.shape[0] == 1:
            waveform = waveform.repeat(2, 1)
        elif waveform.shape[0] > 2:
            waveform = waveform[:2]
        
        # Add batch dimension
        waveform = waveform.unsqueeze(0).to(self.device)
        
        # Apply model
        from demucs.apply import apply_model
        
        with torch.no_grad():
            sources = apply_model(
                self._model,
                waveform,
                device=self.device,
                progress=True,
                num_workers=0
            )
        
        # Sources shape: (batch, num_sources, channels, samples)
        sources = sources.squeeze(0)  # Remove batch dim
        
        # Get source names from model
        source_names = self._model.sources  # e.g., ['drums', 'bass', 'other', 'vocals']
        
        results = {}
        
        for i, name in enumerate(source_names):
            if name in stems or stems == ['all']:
                output_path = output_dir / f"{name}.wav"
                torchaudio.save(
                    output_path,
                    sources[i].cpu(),
                    sample_rate,
                    encoding="PCM_S",
                    bits_per_sample=16
                )
                results[name] = output_path
                logger.info(f"Saved {name} to {output_path}")
        
        return results
    
    def _fallback_separation(
        self,
        input_path: Path,
        output_dir: Path,
        stems: List[str]
    ) -> Dict[str, Path]:
        """
        Fallback separation using high-pass/low-pass filtering.
        Not as good as Demucs but works without GPU.
        """
        from pydub import AudioSegment
        from scipy import signal
        import numpy as np
        
        # Load audio
        audio = AudioSegment.from_file(input_path)
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        
        if audio.channels == 2:
            samples = samples.reshape((-1, 2))
        else:
            samples = samples.reshape((-1, 1))
        
        sample_rate = audio.frame_rate
        
        results = {}
        
        if 'vocals' in stems:
            # High-pass filter for vocals (voice typically > 300 Hz)
            b, a = signal.butter(4, 300 / (sample_rate / 2), btype='high')
            vocals = signal.filtfilt(b, a, samples, axis=0)
            
            # Additional bandpass for speech frequencies (300-3400 Hz)
            b, a = signal.butter(4, [300, 3400], fs=sample_rate, btype='band')
            vocals = signal.filtfilt(b, a, vocals, axis=0)
            
            vocals_path = output_dir / "vocals.wav"
            self._save_array_as_wav(vocals, sample_rate, vocals_path)
            results['vocals'] = vocals_path
        
        if 'other' in stems:
            # Low-pass filter for bass/other
            b, a = signal.butter(4, 300 / (sample_rate / 2), btype='low')
            other = signal.filtfilt(b, a, samples, axis=0)
            
            other_path = output_dir / "other.wav"
            self._save_array_as_wav(other, sample_rate, other_path)
            results['other'] = other_path
        
        return results
    
    def _save_array_as_wav(self, samples: np.ndarray, sample_rate: int, path: Path):
        """Save numpy array as WAV file"""
        import soundfile as sf
        
        # Normalize
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


# Alternative: Using command-line Demucs for simpler integration
def separate_with_cli(
    input_path: Path,
    output_dir: Path,
    model: str = "htdemucs",
    two_stems: bool = True
) -> Dict[str, Path]:
    """
    Run Demucs via command line (simpler but requires demucs installed).
    
    Args:
        input_path: Input audio file
        output_dir: Output directory
        model: Model name
        two_stems: If True, only separate vocals/no_vocals
    
    Returns:
        Dictionary of stem names to paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "python", "-m", "demucs",
        "--out", str(output_dir),
        "--name", model,
        str(input_path)
    ]
    
    if two_stems:
        cmd.extend(["--two-stems", "vocals"])
    
    logger.info(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Demucs failed: {result.stderr}")
    
    # Find output files
    stem_dir = output_dir / model / input_path.stem
    
    results = {}
    for stem_file in stem_dir.glob("*.wav"):
        stem_name = stem_file.stem
        results[stem_name] = stem_file
    
    return results
