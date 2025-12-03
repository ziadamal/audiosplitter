"""
Speaker diarization service.

This version uses a lightweight fallback method that works on Render's free tier.
For production, uncomment the pyannote imports.
"""
import os
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging
import soundfile as sf

logger = logging.getLogger(__name__)


@dataclass
class SpeakerSegment:
    """A segment of audio attributed to a speaker"""
    speaker_id: str
    start: float  # seconds
    end: float    # seconds
    confidence: float = 1.0


@dataclass
class DiarizationResult:
    """Result of speaker diarization"""
    num_speakers: int
    segments: List[SpeakerSegment]
    speaker_audio_paths: Dict[str, Path]  # speaker_id -> audio file path


class SpeakerDiarizer:
    """
    Performs speaker diarization and creates individual speaker tracks.
    
    Uses a lightweight energy-based method for free tier compatibility.
    """
    
    def __init__(
        self,
        hf_token: str = "",
        model_name: str = "pyannote/speaker-diarization-3.1",
        device: str = None
    ):
        """
        Initialize the diarizer.
        """
        self.hf_token = hf_token
        self.model_name = model_name
        self.device = device or "cpu"
        self._pipeline = "fallback"  # Always use fallback on free tier
        logger.info("SpeakerDiarizer initialized with fallback mode")
    
    def diarize(
        self,
        audio_path: Path,
        output_dir: Path,
        min_speakers: int = 1,
        max_speakers: int = 10,
        min_segment_duration: float = 0.5
    ) -> DiarizationResult:
        """
        Perform speaker diarization and create individual speaker tracks.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Running fallback diarization on {audio_path}")
        
        return self._fallback_diarization(audio_path, output_dir, max_speakers)
    
    def _fallback_diarization(
        self,
        audio_path: Path,
        output_dir: Path,
        max_speakers: int = 3
    ) -> DiarizationResult:
        """
        Fallback diarization using energy-based VAD and simple clustering.
        Less accurate than pyannote but works without GPU/heavy dependencies.
        """
        import librosa
        
        logger.info("Using fallback diarization (energy + MFCC clustering)")
        
        # Load audio
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        duration = len(y) / sr
        
        # Compute features
        hop_length = int(0.01 * sr)  # 10ms hop
        frame_length = int(0.025 * sr)  # 25ms frame
        
        # Get MFCCs for speaker characteristics
        mfccs = librosa.feature.mfcc(
            y=y, sr=sr,
            n_mfcc=13,
            hop_length=hop_length,
            n_fft=max(frame_length, 512)
        )
        
        # Compute energy (RMS)
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        
        # Voice activity detection
        threshold = np.mean(rms) * 0.3
        voice_frames = rms > threshold
        
        # Find voiced segments
        segments = []
        in_segment = False
        seg_start = 0
        min_frames = 30  # Minimum 300ms segment
        
        for i, is_voice in enumerate(voice_frames):
            if is_voice and not in_segment:
                seg_start = i
                in_segment = True
            elif not is_voice and in_segment:
                if i - seg_start > min_frames:
                    segments.append((seg_start, i))
                in_segment = False
        
        if in_segment and len(voice_frames) - seg_start > min_frames:
            segments.append((seg_start, len(voice_frames)))
        
        logger.info(f"Found {len(segments)} voice segments")
        
        if not segments:
            # No speech detected, return single speaker with full audio
            speaker_path = output_dir / "speaker_00.wav"
            audio_data, sample_rate = sf.read(audio_path)
            sf.write(speaker_path, audio_data, sample_rate)
            
            return DiarizationResult(
                num_speakers=1,
                segments=[SpeakerSegment("SPEAKER_00", 0, duration)],
                speaker_audio_paths={"SPEAKER_00": speaker_path}
            )
        
        # Extract MFCC features for each segment
        segment_features = []
        for start, end in segments:
            seg_mfcc = mfccs[:, start:end]
            if seg_mfcc.shape[1] > 0:
                feat = np.concatenate([
                    np.mean(seg_mfcc, axis=1),
                    np.std(seg_mfcc, axis=1)
                ])
                segment_features.append(feat)
            else:
                segment_features.append(np.zeros(26))
        
        segment_features = np.array(segment_features)
        
        # Simple clustering based on MFCC similarity
        num_speakers = min(max_speakers, max(1, len(segments) // 5))  # Estimate speakers
        
        if len(segments) >= 2 and num_speakers > 1:
            try:
                from scipy.cluster.hierarchy import fcluster, linkage
                from scipy.spatial.distance import pdist
                
                # Cluster using cosine distance
                if len(segment_features) > 1:
                    distances = pdist(segment_features, metric='cosine')
                    # Replace NaN with max distance
                    distances = np.nan_to_num(distances, nan=1.0)
                    linkage_matrix = linkage(distances, method='ward')
                    
                    # Determine number of clusters
                    labels = fcluster(linkage_matrix, t=num_speakers, criterion='maxclust')
                    num_speakers = len(set(labels))
                else:
                    labels = [1]
                    num_speakers = 1
            except Exception as e:
                logger.warning(f"Clustering failed: {e}, using single speaker")
                labels = [1] * len(segments)
                num_speakers = 1
        else:
            labels = [1] * len(segments)
            num_speakers = 1
        
        logger.info(f"Identified {num_speakers} speakers")
        
        # Convert to SpeakerSegments
        frame_to_time = lambda f: f * hop_length / sr
        
        result_segments = []
        speaker_segments_map: Dict[str, List[SpeakerSegment]] = {}
        
        for (start, end), label in zip(segments, labels):
            speaker_id = f"SPEAKER_{label - 1:02d}"
            seg = SpeakerSegment(
                speaker_id=speaker_id,
                start=frame_to_time(start),
                end=frame_to_time(end),
                confidence=0.7
            )
            result_segments.append(seg)
            
            if speaker_id not in speaker_segments_map:
                speaker_segments_map[speaker_id] = []
            speaker_segments_map[speaker_id].append(seg)
        
        # Create speaker tracks
        audio_data, sample_rate = sf.read(audio_path)
        speaker_audio_paths = {}
        
        for speaker_id, speaker_segs in speaker_segments_map.items():
            speaker_audio = self._extract_speaker_audio(
                audio_data, sample_rate, speaker_segs
            )
            
            speaker_num = speaker_id.replace("SPEAKER_", "")
            output_path = output_dir / f"speaker_{speaker_num}.wav"
            
            sf.write(output_path, speaker_audio, sample_rate)
            speaker_audio_paths[speaker_id] = output_path
            logger.info(f"Created track for {speaker_id}")
        
        return DiarizationResult(
            num_speakers=num_speakers,
            segments=result_segments,
            speaker_audio_paths=speaker_audio_paths
        )
    
    def _extract_speaker_audio(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        segments: List[SpeakerSegment],
        crossfade_ms: int = 10
    ) -> np.ndarray:
        """
        Extract audio for a specific speaker, silencing other parts.
        """
        # Create output array (same shape as input)
        output = np.zeros_like(audio_data)
        
        crossfade_samples = int(crossfade_ms * sample_rate / 1000)
        
        for seg in segments:
            start_sample = int(seg.start * sample_rate)
            end_sample = int(seg.end * sample_rate)
            
            # Clamp to valid range
            start_sample = max(0, start_sample)
            end_sample = min(len(audio_data), end_sample)
            
            if start_sample >= end_sample:
                continue
            
            # Copy segment
            segment_data = audio_data[start_sample:end_sample].copy()
            
            # Apply fade in/out
            if len(segment_data) > crossfade_samples * 2:
                fade_in = np.linspace(0, 1, crossfade_samples)
                fade_out = np.linspace(1, 0, crossfade_samples)
                
                if segment_data.ndim == 1:
                    segment_data[:crossfade_samples] *= fade_in
                    segment_data[-crossfade_samples:] *= fade_out
                else:
                    segment_data[:crossfade_samples] *= fade_in[:, np.newaxis]
                    segment_data[-crossfade_samples:] *= fade_out[:, np.newaxis]
            
            output[start_sample:end_sample] = segment_data
        
        return output


def diarize_audio(
    audio_path: Path,
    output_dir: Path,
    hf_token: str = "",
    min_speakers: int = 1,
    max_speakers: int = 10
) -> DiarizationResult:
    """
    Convenience function for speaker diarization.
    """
    diarizer = SpeakerDiarizer(hf_token=hf_token)
    return diarizer.diarize(
        audio_path,
        output_dir,
        min_speakers=min_speakers,
        max_speakers=max_speakers
    )
