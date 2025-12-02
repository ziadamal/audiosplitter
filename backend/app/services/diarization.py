"""
Speaker diarization service using pyannote.audio.

This module handles:
1. Detecting how many speakers are in an audio file
2. Determining when each speaker is talking
3. Splitting the vocals track into individual speaker tracks

pyannote.audio requires a Hugging Face token with access to:
- pyannote/speaker-diarization-3.1
- pyannote/segmentation-3.0
"""
import os
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging
import soundfile as sf
from scipy.io import wavfile

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
    
    Uses pyannote.audio's state-of-the-art diarization pipeline.
    """
    
    def __init__(
        self,
        hf_token: str,
        model_name: str = "pyannote/speaker-diarization-3.1",
        device: str = None
    ):
        """
        Initialize the diarizer.
        
        Args:
            hf_token: Hugging Face token with access to pyannote models
            model_name: Diarization model to use
            device: 'cuda' or 'cpu'. Auto-detected if None.
        """
        self.hf_token = hf_token
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._pipeline = None
    
    def _load_pipeline(self):
        """Lazy load the diarization pipeline"""
        if self._pipeline is None:
            try:
                from pyannote.audio import Pipeline
                
                logger.info(f"Loading diarization pipeline: {self.model_name}")
                
                self._pipeline = Pipeline.from_pretrained(
                    self.model_name,
                    use_auth_token=self.hf_token
                )
                self._pipeline.to(torch.device(self.device))
                
                logger.info(f"Pipeline loaded on {self.device}")
            except Exception as e:
                logger.error(f"Failed to load pyannote pipeline: {e}")
                logger.warning("Falling back to simple VAD-based segmentation")
                self._pipeline = "fallback"
    
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
        
        Args:
            audio_path: Path to audio file (preferably vocals-only)
            output_dir: Directory to save speaker tracks
            min_speakers: Minimum expected speakers
            max_speakers: Maximum expected speakers
            min_segment_duration: Minimum segment duration in seconds
        
        Returns:
            DiarizationResult with segments and speaker audio paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_pipeline()
        
        if self._pipeline == "fallback":
            return self._fallback_diarization(audio_path, output_dir)
        
        # Run diarization
        logger.info(f"Running diarization on {audio_path}")
        
        diarization = self._pipeline(
            audio_path,
            min_speakers=min_speakers,
            max_speakers=max_speakers
        )
        
        # Extract segments
        segments = []
        speaker_segments_map: Dict[str, List[SpeakerSegment]] = {}
        
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            if turn.duration < min_segment_duration:
                continue
            
            segment = SpeakerSegment(
                speaker_id=speaker,
                start=turn.start,
                end=turn.end
            )
            segments.append(segment)
            
            if speaker not in speaker_segments_map:
                speaker_segments_map[speaker] = []
            speaker_segments_map[speaker].append(segment)
        
        # Sort segments by start time
        segments.sort(key=lambda s: s.start)
        
        # Load audio for splitting
        audio_data, sample_rate = sf.read(audio_path)
        
        # Create individual speaker tracks
        speaker_audio_paths = {}
        
        for speaker_id, speaker_segs in speaker_segments_map.items():
            speaker_audio = self._extract_speaker_audio(
                audio_data, sample_rate, speaker_segs
            )
            
            # Create friendly speaker name
            speaker_num = speaker_id.replace("SPEAKER_", "")
            output_path = output_dir / f"speaker_{speaker_num}.wav"
            
            sf.write(output_path, speaker_audio, sample_rate)
            speaker_audio_paths[speaker_id] = output_path
            
            logger.info(f"Created track for {speaker_id} at {output_path}")
        
        return DiarizationResult(
            num_speakers=len(speaker_segments_map),
            segments=segments,
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
        
        Uses crossfade to avoid clicks at segment boundaries.
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
            
            # Apply fade in
            if len(segment_data) > crossfade_samples * 2:
                fade_in = np.linspace(0, 1, crossfade_samples)
                if segment_data.ndim == 1:
                    segment_data[:crossfade_samples] *= fade_in
                else:
                    segment_data[:crossfade_samples] *= fade_in[:, np.newaxis]
                
                # Apply fade out
                fade_out = np.linspace(1, 0, crossfade_samples)
                if segment_data.ndim == 1:
                    segment_data[-crossfade_samples:] *= fade_out
                else:
                    segment_data[-crossfade_samples:] *= fade_out[:, np.newaxis]
            
            output[start_sample:end_sample] = segment_data
        
        return output
    
    def _fallback_diarization(
        self,
        audio_path: Path,
        output_dir: Path
    ) -> DiarizationResult:
        """
        Fallback diarization using energy-based VAD and clustering.
        Less accurate than pyannote but works without the model.
        """
        import librosa
        from scipy.cluster.hierarchy import fcluster, linkage
        from scipy.spatial.distance import pdist
        
        logger.info("Using fallback diarization (energy + clustering)")
        
        # Load audio
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        
        # Compute MFCC features for each frame
        hop_length = int(0.01 * sr)  # 10ms hop
        frame_length = int(0.025 * sr)  # 25ms frame
        
        mfccs = librosa.feature.mfcc(
            y=y, sr=sr,
            n_mfcc=20,
            hop_length=hop_length,
            n_fft=frame_length
        )
        
        # Compute energy (RMS)
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        
        # Voice activity detection (simple threshold)
        threshold = np.mean(rms) * 0.5
        voice_frames = rms > threshold
        
        # Find voiced segments
        segments = []
        in_segment = False
        seg_start = 0
        
        for i, is_voice in enumerate(voice_frames):
            if is_voice and not in_segment:
                seg_start = i
                in_segment = True
            elif not is_voice and in_segment:
                if i - seg_start > 20:  # Minimum 200ms segment
                    segments.append((seg_start, i))
                in_segment = False
        
        if in_segment and len(voice_frames) - seg_start > 20:
            segments.append((seg_start, len(voice_frames)))
        
        if not segments:
            # No speech detected, return single speaker
            return DiarizationResult(
                num_speakers=1,
                segments=[SpeakerSegment("SPEAKER_00", 0, len(y) / sr)],
                speaker_audio_paths={"SPEAKER_00": audio_path}
            )
        
        # Extract features for each segment
        segment_features = []
        for start, end in segments:
            seg_mfcc = mfccs[:, start:end]
            # Use mean and std of MFCCs as segment embedding
            feat = np.concatenate([
                np.mean(seg_mfcc, axis=1),
                np.std(seg_mfcc, axis=1)
            ])
            segment_features.append(feat)
        
        segment_features = np.array(segment_features)
        
        # Cluster segments into speakers (if enough segments)
        if len(segments) >= 2:
            distances = pdist(segment_features, metric='cosine')
            linkage_matrix = linkage(distances, method='ward')
            
            # Use threshold-based clustering
            labels = fcluster(linkage_matrix, t=0.5, criterion='distance')
            num_speakers = len(set(labels))
        else:
            labels = [1]
            num_speakers = 1
        
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
                confidence=0.7  # Lower confidence for fallback
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
        
        return DiarizationResult(
            num_speakers=num_speakers,
            segments=result_segments,
            speaker_audio_paths=speaker_audio_paths
        )


def diarize_audio(
    audio_path: Path,
    output_dir: Path,
    hf_token: str,
    min_speakers: int = 1,
    max_speakers: int = 10
) -> DiarizationResult:
    """
    Convenience function for speaker diarization.
    
    Args:
        audio_path: Path to audio file
        output_dir: Output directory for speaker tracks
        hf_token: Hugging Face token
        min_speakers: Minimum expected speakers
        max_speakers: Maximum expected speakers
    
    Returns:
        DiarizationResult with speaker information and tracks
    """
    diarizer = SpeakerDiarizer(hf_token=hf_token)
    return diarizer.diarize(
        audio_path,
        output_dir,
        min_speakers=min_speakers,
        max_speakers=max_speakers
    )
