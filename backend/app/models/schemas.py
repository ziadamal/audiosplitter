"""
Pydantic models for API request/response schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class ProcessingStatus(str, Enum):
    """Status of audio processing job"""
    PENDING = "pending"
    PROCESSING = "processing"
    SEPARATING = "separating"
    DIARIZING = "diarizing"
    COMPLETE = "complete"
    FAILED = "failed"


class TrackType(str, Enum):
    """Type of audio track"""
    SPEAKER = "speaker"
    NOISE = "noise"
    VOCALS = "vocals"
    DRUMS = "drums"
    BASS = "bass"
    OTHER = "other"


# ==================== Upload ====================

class UploadResponse(BaseModel):
    """Response after file upload"""
    job_id: str = Field(..., description="Unique identifier for this processing job")
    filename: str = Field(..., description="Original filename")
    duration_seconds: float = Field(..., description="Duration of the audio file")
    sample_rate: int = Field(..., description="Sample rate of the audio")
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    message: str = Field(default="File uploaded successfully")


# ==================== Analysis ====================

class SpeakerSegment(BaseModel):
    """A segment of audio attributed to a specific speaker"""
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    speaker_id: str = Field(..., description="Speaker identifier")
    confidence: float = Field(default=1.0, ge=0, le=1)


class Track(BaseModel):
    """An individual audio track (speaker or noise)"""
    id: str = Field(..., description="Unique track identifier")
    name: str = Field(..., description="Display name (e.g., 'Speaker 1', 'Background Noise')")
    type: TrackType = Field(..., description="Type of track")
    file_path: str = Field(..., description="Path to the separated audio file")
    duration_seconds: float = Field(..., description="Duration in seconds")
    segments: List[SpeakerSegment] = Field(default_factory=list, description="Time segments for this track")
    waveform_data: Optional[List[float]] = Field(None, description="Waveform visualization data")
    color: str = Field(default="#3B82F6", description="UI color for this track")


class AnalysisResult(BaseModel):
    """Complete analysis result for an audio file"""
    job_id: str
    status: ProcessingStatus
    original_filename: str
    duration_seconds: float
    speaker_count: int = Field(..., description="Number of detected speakers")
    tracks: List[Track] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class JobStatusResponse(BaseModel):
    """Response for job status check"""
    job_id: str
    status: ProcessingStatus
    progress: float = Field(default=0.0, ge=0, le=100, description="Progress percentage")
    current_step: str = Field(default="", description="Current processing step")
    result: Optional[AnalysisResult] = None


# ==================== Mix Configuration ====================

class TrackConfig(BaseModel):
    """Configuration for a single track in the mix"""
    track_id: str = Field(..., description="Track identifier")
    muted: bool = Field(default=False, description="Whether track is muted")
    solo: bool = Field(default=False, description="Whether track is soloed")
    volume: float = Field(default=1.0, ge=0, le=2, description="Volume multiplier")
    is_main: bool = Field(default=False, description="Whether this is the main/emphasized track")


class MixConfig(BaseModel):
    """Configuration for the final audio mix"""
    job_id: str = Field(..., description="Job identifier")
    tracks: List[TrackConfig] = Field(..., description="Configuration for each track")
    main_speaker_boost_db: float = Field(default=3.0, description="dB boost for main speaker")
    noise_reduction_level: float = Field(default=0.0, ge=0, le=1, description="Additional noise reduction")
    output_format: str = Field(default="wav", description="Output format (wav, mp3, flac)")
    normalize: bool = Field(default=True, description="Whether to normalize final audio")


# ==================== Preview ====================

class PreviewRequest(BaseModel):
    """Request for generating a preview mix"""
    job_id: str
    mix_config: MixConfig
    start_time: float = Field(default=0, ge=0, description="Preview start time in seconds")
    duration: float = Field(default=30, gt=0, le=60, description="Preview duration in seconds")


class PreviewResponse(BaseModel):
    """Response with preview audio"""
    preview_url: str = Field(..., description="URL to preview audio file")
    duration_seconds: float


# ==================== Export ====================

class ExportRequest(BaseModel):
    """Request to export final mixed audio"""
    job_id: str
    mix_config: MixConfig
    filename: Optional[str] = Field(None, description="Custom output filename")


class ExportResponse(BaseModel):
    """Response with exported file"""
    download_url: str = Field(..., description="URL to download the exported file")
    filename: str
    file_size_bytes: int
    duration_seconds: float
    format: str
