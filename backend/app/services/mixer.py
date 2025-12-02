"""
Audio mixing service for combining separated tracks.

Handles:
- Muting/unmuting tracks
- Solo functionality
- Volume adjustment
- Main speaker emphasis
- Final export with various formats
"""
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from scipy import signal
from pydub import AudioSegment
import io

logger = logging.getLogger(__name__)


@dataclass
class TrackConfig:
    """Configuration for a single track"""
    track_id: str
    file_path: Path
    muted: bool = False
    solo: bool = False
    volume: float = 1.0  # 0.0 to 2.0
    is_main: bool = False


@dataclass
class MixSettings:
    """Global mix settings"""
    main_speaker_boost_db: float = 3.0
    noise_reduction_level: float = 0.0  # 0 to 1
    normalize: bool = True
    output_format: str = "wav"
    sample_rate: int = 44100


class AudioMixer:
    """
    Mixes multiple audio tracks with various controls.
    """
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
    
    def mix_tracks(
        self,
        tracks: List[TrackConfig],
        settings: MixSettings,
        output_path: Optional[Path] = None
    ) -> Tuple[np.ndarray, int]:
        """
        Mix multiple tracks according to their configurations.
        
        Args:
            tracks: List of track configurations
            settings: Global mix settings
            output_path: Optional path to save the mixed audio
        
        Returns:
            Tuple of (mixed_audio_array, sample_rate)
        """
        if not tracks:
            raise ValueError("No tracks provided for mixing")
        
        # Check if any tracks are soloed
        soloed_tracks = [t for t in tracks if t.solo and not t.muted]
        active_tracks = soloed_tracks if soloed_tracks else [t for t in tracks if not t.muted]
        
        if not active_tracks:
            # All tracks muted - return silence
            duration_samples = self._get_track_duration(tracks[0].file_path)
            return np.zeros((duration_samples, 2)), self.sample_rate
        
        # Load and process each active track
        mixed = None
        target_sr = settings.sample_rate
        
        for track in active_tracks:
            # Load audio
            audio, sr = sf.read(track.file_path, always_2d=True)
            
            # Resample if needed
            if sr != target_sr:
                audio = self._resample(audio, sr, target_sr)
            
            # Ensure stereo
            if audio.shape[1] == 1:
                audio = np.column_stack([audio[:, 0], audio[:, 0]])
            elif audio.shape[1] > 2:
                audio = audio[:, :2]
            
            # Apply volume
            audio = audio * track.volume
            
            # Apply main speaker boost
            if track.is_main and settings.main_speaker_boost_db > 0:
                boost_linear = 10 ** (settings.main_speaker_boost_db / 20)
                audio = audio * boost_linear
                logger.info(f"Applied {settings.main_speaker_boost_db}dB boost to main track {track.track_id}")
            
            # Apply noise reduction if this is a noise track
            if "noise" in track.track_id.lower() or "other" in track.track_id.lower():
                if settings.noise_reduction_level > 0:
                    audio = audio * (1 - settings.noise_reduction_level)
                    logger.info(f"Applied {settings.noise_reduction_level * 100}% noise reduction")
            
            # Mix into output
            if mixed is None:
                mixed = audio
            else:
                # Ensure same length
                if len(audio) > len(mixed):
                    mixed = np.pad(mixed, ((0, len(audio) - len(mixed)), (0, 0)))
                elif len(mixed) > len(audio):
                    audio = np.pad(audio, ((0, len(mixed) - len(audio)), (0, 0)))
                
                mixed = mixed + audio
        
        # Normalize
        if settings.normalize:
            mixed = self._normalize(mixed)
        else:
            # Prevent clipping
            max_val = np.max(np.abs(mixed))
            if max_val > 1.0:
                mixed = mixed / max_val
        
        # Save if output path provided
        if output_path:
            self._save_audio(mixed, target_sr, output_path, settings.output_format)
            logger.info(f"Saved mixed audio to {output_path}")
        
        return mixed, target_sr
    
    def create_preview(
        self,
        tracks: List[TrackConfig],
        settings: MixSettings,
        start_time: float,
        duration: float,
        output_path: Path
    ) -> Path:
        """
        Create a preview mix of a specific segment.
        
        Args:
            tracks: Track configurations
            settings: Mix settings
            start_time: Start time in seconds
            duration: Duration in seconds
            output_path: Path to save preview
        
        Returns:
            Path to the preview file
        """
        # Mix full audio
        mixed, sr = self.mix_tracks(tracks, settings)
        
        # Extract preview segment
        start_sample = int(start_time * sr)
        end_sample = int((start_time + duration) * sr)
        
        # Clamp to valid range
        start_sample = max(0, min(start_sample, len(mixed)))
        end_sample = max(start_sample, min(end_sample, len(mixed)))
        
        preview = mixed[start_sample:end_sample]
        
        # Add fade in/out for smooth preview
        fade_samples = int(0.1 * sr)  # 100ms fade
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
        """
        Export the final mixed audio.
        
        Args:
            tracks: Track configurations
            settings: Mix settings
            output_path: Output file path
        
        Returns:
            Tuple of (output_path, file_size_bytes)
        """
        mixed, sr = self.mix_tracks(tracks, settings, output_path)
        
        file_size = output_path.stat().st_size
        return output_path, file_size
    
    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio to target sample rate"""
        if orig_sr == target_sr:
            return audio
        
        # Calculate new length
        new_length = int(len(audio) * target_sr / orig_sr)
        
        # Resample each channel
        resampled = np.zeros((new_length, audio.shape[1]))
        for ch in range(audio.shape[1]):
            resampled[:, ch] = signal.resample(audio[:, ch], new_length)
        
        return resampled
    
    def _normalize(self, audio: np.ndarray, target_db: float = -3.0) -> np.ndarray:
        """Normalize audio to target dB level"""
        max_val = np.max(np.abs(audio))
        if max_val == 0:
            return audio
        
        target_linear = 10 ** (target_db / 20)
        return audio * (target_linear / max_val)
    
    def _get_track_duration(self, file_path: Path) -> int:
        """Get duration of a track in samples"""
        info = sf.info(file_path)
        return int(info.frames)
    
    def _save_audio(
        self,
        audio: np.ndarray,
        sample_rate: int,
        output_path: Path,
        format: str
    ):
        """Save audio to file with specified format"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "wav":
            sf.write(output_path, audio, sample_rate, subtype='PCM_16')
        
        elif format.lower() == "mp3":
            # Use pydub for MP3 export
            # First save as WAV
            temp_wav = output_path.with_suffix('.temp.wav')
            sf.write(temp_wav, audio, sample_rate, subtype='PCM_16')
            
            # Convert to MP3
            audio_segment = AudioSegment.from_wav(temp_wav)
            audio_segment.export(output_path, format='mp3', bitrate='192k')
            
            # Clean up temp file
            temp_wav.unlink()
        
        elif format.lower() == "flac":
            sf.write(output_path, audio, sample_rate, format='FLAC')
        
        else:
            # Default to WAV
            sf.write(output_path, audio, sample_rate)


def mix_and_export(
    track_configs: List[Dict],
    output_path: Path,
    main_speaker_boost_db: float = 3.0,
    noise_reduction: float = 0.0,
    output_format: str = "wav"
) -> Path:
    """
    Convenience function for mixing and exporting.
    
    Args:
        track_configs: List of dicts with track configuration
        output_path: Output file path
        main_speaker_boost_db: dB boost for main speaker
        noise_reduction: Noise reduction level (0-1)
        output_format: Output format
    
    Returns:
        Path to exported file
    """
    tracks = [
        TrackConfig(
            track_id=tc['track_id'],
            file_path=Path(tc['file_path']),
            muted=tc.get('muted', False),
            solo=tc.get('solo', False),
            volume=tc.get('volume', 1.0),
            is_main=tc.get('is_main', False)
        )
        for tc in track_configs
    ]
    
    settings = MixSettings(
        main_speaker_boost_db=main_speaker_boost_db,
        noise_reduction_level=noise_reduction,
        output_format=output_format
    )
    
    mixer = AudioMixer()
    path, _ = mixer.export(tracks, settings, output_path)
    return path


def generate_waveform_data(
    audio_path: Path,
    num_points: int = 200
) -> List[float]:
    """
    Generate waveform visualization data for a track.
    
    Args:
        audio_path: Path to audio file
        num_points: Number of points in the waveform
    
    Returns:
        List of peak values normalized to 0-1
    """
    audio, sr = sf.read(audio_path, always_2d=True)
    
    # Convert to mono
    if audio.shape[1] > 1:
        audio = np.mean(audio, axis=1)
    else:
        audio = audio[:, 0]
    
    # Calculate samples per point
    samples_per_point = max(1, len(audio) // num_points)
    
    waveform = []
    for i in range(num_points):
        start = i * samples_per_point
        end = min(start + samples_per_point, len(audio))
        
        if start >= len(audio):
            waveform.append(0.0)
        else:
            # Get peak value in this segment
            segment = np.abs(audio[start:end])
            peak = float(np.max(segment)) if len(segment) > 0 else 0.0
            waveform.append(peak)
    
    # Normalize to 0-1
    max_peak = max(waveform) if waveform else 1.0
    if max_peak > 0:
        waveform = [v / max_peak for v in waveform]
    
    return waveform
