"""
Audio mixing service for combining separated tracks.
"""
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from scipy import signal

logger = logging.getLogger(__name__)


@dataclass
class TrackConfig:
    """Configuration for a single track"""
    track_id: str
    file_path: Path
    muted: bool = False
    solo: bool = False
    volume: float = 1.0
    is_main: bool = False


@dataclass
class MixSettings:
    """Global mix settings"""
    main_speaker_boost_db: float = 3.0
    noise_reduction_level: float = 0.0
    normalize: bool = True
    output_format: str = "wav"
    sample_rate: int = 44100


class AudioMixer:
    """Mixes multiple audio tracks with various controls."""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
    
    def mix_tracks(
        self,
        tracks: List[TrackConfig],
        settings: MixSettings,
        output_path: Optional[Path] = None
    ) -> Tuple[np.ndarray, int]:
        """Mix multiple tracks according to their configurations."""
        if not tracks:
            raise ValueError("No tracks provided for mixing")
        
        # Check if any tracks are soloed
        soloed_tracks = [t for t in tracks if t.solo and not t.muted]
        active_tracks = soloed_tracks if soloed_tracks else [t for t in tracks if not t.muted]
        
        if not active_tracks:
            duration_samples = self._get_track_duration(tracks[0].file_path)
            return np.zeros((duration_samples, 2)), self.sample_rate
        
        mixed = None
        target_sr = settings.sample_rate
        
        for track in active_tracks:
            audio, sr = sf.read(track.file_path, always_2d=True)
            
            if sr != target_sr:
                audio = self._resample(audio, sr, target_sr)
            
            if audio.shape[1] == 1:
                audio = np.column_stack([audio[:, 0], audio[:, 0]])
            elif audio.shape[1] > 2:
                audio = audio[:, :2]
            
            audio = audio * track.volume
            
            if track.is_main and settings.main_speaker_boost_db > 0:
                boost_linear = 10 ** (settings.main_speaker_boost_db / 20)
                audio = audio * boost_linear
            
            if "noise" in track.track_id.lower() or "other" in track.track_id.lower():
                if settings.noise_reduction_level > 0:
                    audio = audio * (1 - settings.noise_reduction_level)
            
            if mixed is None:
                mixed = audio
            else:
                if len(audio) > len(mixed):
                    mixed = np.pad(mixed, ((0, len(audio) - len(mixed)), (0, 0)))
                elif len(mixed) > len(audio):
                    audio = np.pad(audio, ((0, len(mixed) - len(audio)), (0, 0)))
                mixed = mixed + audio
        
        if settings.normalize:
            mixed = self._normalize(mixed)
        else:
            max_val = np.max(np.abs(mixed))
            if max_val > 1.0:
                mixed = mixed / max_val
        
        if output_path:
            self._save_audio(mixed, target_sr, output_path, settings.output_format)
        
        return mixed, target_sr
    
    def create_preview(
        self,
        tracks: List[TrackConfig],
        settings: MixSettings,
        start_time: float,
        duration: float,
        output_path: Path
    ) -> Path:
        """Create a preview mix of a specific segment."""
        mixed, sr = self.mix_tracks(tracks, settings)
        
        start_sample = int(start_time * sr)
        end_sample = int((start_time + duration) * sr)
        
        start_sample = max(0, min(start_sample, len(mixed)))
        end_sample = max(start_sample, min(end_sample, len(mixed)))
        
        preview = mixed[start_sample:end_sample]
        
        fade_samples = int(0.1 * sr)
        if len(preview) > fade_samples * 2:
            fade_in = np.linspace(0, 1, fade_samples)[:, np.newaxis]
            fade_out = np.linspace(1, 0, fade_samples)[:, np.newaxis]
            preview[:fade_samples] *= fade_in
            preview[-fade_samples:] *= fade_out
        
        self._save_audio(preview, sr, output_path, "wav")
        return output_path
    
    def export(
        self,
        tracks: List[TrackConfig],
        settings: MixSettings,
        output_path: Path
    ) -> Tuple[Path, int]:
        """Export the final mixed audio."""
        self.mix_tracks(tracks, settings, output_path)
        file_size = output_path.stat().st_size
        return output_path, file_size
    
    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        if orig_sr == target_sr:
            return audio
        new_length = int(len(audio) * target_sr / orig_sr)
        resampled = np.zeros((new_length, audio.shape[1]))
        for ch in range(audio.shape[1]):
            resampled[:, ch] = signal.resample(audio[:, ch], new_length)
        return resampled
    
    def _normalize(self, audio: np.ndarray, target_db: float = -3.0) -> np.ndarray:
        max_val = np.max(np.abs(audio))
        if max_val == 0:
            return audio
        target_linear = 10 ** (target_db / 20)
        return audio * (target_linear / max_val)
    
    def _get_track_duration(self, file_path: Path) -> int:
        info = sf.info(file_path)
        return int(info.frames)
    
    def _save_audio(self, audio: np.ndarray, sample_rate: int, output_path: Path, format: str):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() in ["wav", "mp3", "flac"]:
            sf.write(output_path, audio, sample_rate, subtype='PCM_16')
        else:
            sf.write(output_path, audio, sample_rate)


def generate_waveform_data(audio_path: Path, num_points: int = 200) -> List[float]:
    """Generate waveform visualization data for a track."""
    audio, sr = sf.read(audio_path, always_2d=True)
    
    if audio.shape[1] > 1:
        audio = np.mean(audio, axis=1)
    else:
        audio = audio[:, 0]
    
    samples_per_point = max(1, len(audio) // num_points)
    
    waveform = []
    for i in range(num_points):
        start = i * samples_per_point
        end = min(start + samples_per_point, len(audio))
        
        if start >= len(audio):
            waveform.append(0.0)
        else:
            segment = np.abs(audio[start:end])
            peak = float(np.max(segment)) if len(segment) > 0 else 0.0
            waveform.append(peak)
    
    max_peak = max(waveform) if waveform else 1.0
    if max_peak > 0:
        waveform = [v / max_peak for v in waveform]
    
    return waveform
