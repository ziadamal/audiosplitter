"""
VoxSplit - Audio Source Separation API

Main FastAPI application with all endpoints for:
- File upload
- Audio analysis (separation + diarization)
- Track management
- Preview generation
- Final export
"""
import os
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import shutil
import logging

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.config import get_settings
from app.models.schemas import (
    UploadResponse, JobStatusResponse, AnalysisResult, Track, TrackType,
    ProcessingStatus, MixConfig, TrackConfig, PreviewRequest, PreviewResponse,
    ExportRequest, ExportResponse, SpeakerSegment
)
from app.services.separation import SourceSeparator
from app.services.diarization import SpeakerDiarizer, DiarizationResult
from app.services.mixer import AudioMixer, TrackConfig as MixerTrackConfig, MixSettings, generate_waveform_data
from app.utils.audio import (
    generate_job_id, get_audio_info, convert_to_wav, validate_audio_file,
    get_speaker_color, NOISE_COLOR, estimate_processing_time
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="VoxSplit Audio Separator API",
    description="API for separating speakers and noise from audio files",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving audio
app.mount("/audio", StaticFiles(directory=str(settings.output_dir)), name="audio")

# In-memory job storage (use Redis in production)
jobs: Dict[str, dict] = {}


# ==================== UPLOAD ENDPOINT ====================

@app.post("/api/upload", response_model=UploadResponse)
async def upload_audio(file: UploadFile = File(...)):
    """
    Upload an audio file for processing.
    
    Accepts: MP3, WAV, M4A, FLAC, OGG, AAC
    Returns: Job ID and file info
    """
    # Validate file extension
    ext = Path(file.filename).suffix.lower().lstrip('.')
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(settings.allowed_extensions)}"
        )
    
    # Generate job ID
    job_id = generate_job_id(file.filename)
    job_dir = settings.upload_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Save uploaded file
    original_path = job_dir / f"original.{ext}"
    try:
        with open(original_path, 'wb') as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Validate file
    is_valid, error = validate_audio_file(
        original_path,
        settings.allowed_extensions,
        settings.max_file_size_mb
    )
    if not is_valid:
        shutil.rmtree(job_dir)
        raise HTTPException(status_code=400, detail=error)
    
    # Get audio info
    info = get_audio_info(original_path)
    
    # Convert to WAV if needed
    if ext != 'wav':
        wav_path = job_dir / "original.wav"
        convert_to_wav(original_path, wav_path, target_sr=settings.sample_rate)
    else:
        wav_path = original_path
    
    # Initialize job status
    jobs[job_id] = {
        "job_id": job_id,
        "status": ProcessingStatus.PENDING,
        "original_filename": file.filename,
        "original_path": str(original_path),
        "wav_path": str(wav_path),
        "job_dir": str(job_dir),
        "duration_seconds": info["duration_seconds"],
        "sample_rate": info["sample_rate"],
        "progress": 0,
        "current_step": "Uploaded",
        "created_at": datetime.utcnow().isoformat(),
        "tracks": [],
        "error_message": None
    }
    
    logger.info(f"Job {job_id} created for {file.filename}")
    
    return UploadResponse(
        job_id=job_id,
        filename=file.filename,
        duration_seconds=info["duration_seconds"],
        sample_rate=info["sample_rate"],
        status=ProcessingStatus.PENDING,
        message=f"File uploaded. Estimated processing time: {estimate_processing_time(info['duration_seconds']):.0f} seconds"
    )


# ==================== ANALYSIS ENDPOINT ====================

@app.post("/api/analyze/{job_id}", response_model=JobStatusResponse)
async def start_analysis(job_id: str, background_tasks: BackgroundTasks):
    """
    Start the audio analysis process.
    
    This runs source separation and speaker diarization in the background.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] not in [ProcessingStatus.PENDING, ProcessingStatus.FAILED]:
        return JobStatusResponse(
            job_id=job_id,
            status=job["status"],
            progress=job["progress"],
            current_step=job["current_step"]
        )
    
    # Update status
    job["status"] = ProcessingStatus.PROCESSING
    job["current_step"] = "Starting analysis..."
    
    # Run analysis in background
    background_tasks.add_task(run_analysis_pipeline, job_id)
    
    return JobStatusResponse(
        job_id=job_id,
        status=ProcessingStatus.PROCESSING,
        progress=0,
        current_step="Starting analysis..."
    )


async def run_analysis_pipeline(job_id: str):
    """Run the full analysis pipeline: separation + diarization"""
    job = jobs.get(job_id)
    if not job:
        return
    
    try:
        wav_path = Path(job["wav_path"])
        job_dir = Path(job["job_dir"])
        output_dir = settings.output_dir / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Source Separation
        job["status"] = ProcessingStatus.SEPARATING
        job["current_step"] = "Separating vocals from background..."
        job["progress"] = 10
        
        logger.info(f"Job {job_id}: Starting source separation")
        
        separator = SourceSeparator(model_name=settings.demucs_model)
        separated = separator.separate(
            wav_path,
            output_dir / "separated",
            stems=['vocals', 'other']
        )
        
        vocals_path = separated.get('vocals')
        noise_path = separated.get('other')
        
        job["progress"] = 40
        
        # Step 2: Speaker Diarization
        job["status"] = ProcessingStatus.DIARIZING
        job["current_step"] = "Detecting speakers..."
        job["progress"] = 50
        
        logger.info(f"Job {job_id}: Starting speaker diarization")
        
        diarizer = SpeakerDiarizer(
            hf_token=settings.hf_token,
            model_name=settings.diarization_model
        )
        
        diarization_result = diarizer.diarize(
            vocals_path,
            output_dir / "speakers",
            min_speakers=settings.min_speakers,
            max_speakers=settings.max_speakers
        )
        
        job["progress"] = 80
        
        # Step 3: Create track objects
        job["current_step"] = "Creating tracks..."
        
        tracks = []
        
        # Add speaker tracks
        for i, (speaker_id, speaker_path) in enumerate(diarization_result.speaker_audio_paths.items()):
            speaker_num = int(speaker_id.replace("SPEAKER_", ""))
            
            # Get segments for this speaker
            segments = [
                SpeakerSegment(
                    start=seg.start,
                    end=seg.end,
                    speaker_id=seg.speaker_id,
                    confidence=seg.confidence
                )
                for seg in diarization_result.segments
                if seg.speaker_id == speaker_id
            ]
            
            # Generate waveform data
            waveform = generate_waveform_data(speaker_path)
            
            track = Track(
                id=f"speaker_{speaker_num}",
                name=f"Speaker {speaker_num + 1}",
                type=TrackType.SPEAKER,
                file_path=str(speaker_path),
                duration_seconds=job["duration_seconds"],
                segments=segments,
                waveform_data=waveform,
                color=get_speaker_color(speaker_num)
            )
            tracks.append(track)
        
        # Add noise track
        if noise_path and noise_path.exists():
            noise_waveform = generate_waveform_data(noise_path)
            noise_track = Track(
                id="noise",
                name="Background / Noise",
                type=TrackType.NOISE,
                file_path=str(noise_path),
                duration_seconds=job["duration_seconds"],
                segments=[],
                waveform_data=noise_waveform,
                color=NOISE_COLOR
            )
            tracks.append(noise_track)
        
        # Update job with results
        job["status"] = ProcessingStatus.COMPLETE
        job["current_step"] = "Complete"
        job["progress"] = 100
        job["tracks"] = [t.model_dump() for t in tracks]
        job["speaker_count"] = diarization_result.num_speakers
        job["completed_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Job {job_id}: Analysis complete. Found {diarization_result.num_speakers} speakers")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
        job["status"] = ProcessingStatus.FAILED
        job["error_message"] = str(e)
        job["current_step"] = "Failed"


# ==================== STATUS ENDPOINT ====================

@app.get("/api/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the current status of a processing job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    result = None
    if job["status"] == ProcessingStatus.COMPLETE:
        result = AnalysisResult(
            job_id=job_id,
            status=job["status"],
            original_filename=job["original_filename"],
            duration_seconds=job["duration_seconds"],
            speaker_count=job.get("speaker_count", 0),
            tracks=[Track(**t) for t in job.get("tracks", [])],
            created_at=datetime.fromisoformat(job["created_at"]),
            completed_at=datetime.fromisoformat(job["completed_at"]) if job.get("completed_at") else None
        )
    
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0),
        current_step=job.get("current_step", ""),
        result=result
    )


# ==================== TRACKS ENDPOINT ====================

@app.get("/api/tracks/{job_id}")
async def get_tracks(job_id: str):
    """Get all tracks for a completed job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] != ProcessingStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Analysis not complete")
    
    return {
        "job_id": job_id,
        "tracks": job.get("tracks", []),
        "speaker_count": job.get("speaker_count", 0),
        "duration_seconds": job["duration_seconds"]
    }


@app.get("/api/tracks/{job_id}/{track_id}/audio")
async def get_track_audio(job_id: str, track_id: str):
    """Get audio file for a specific track"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    tracks = job.get("tracks", [])
    
    track = next((t for t in tracks if t["id"] == track_id), None)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    file_path = Path(track["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Track file not found")
    
    return FileResponse(
        file_path,
        media_type="audio/wav",
        filename=f"{track_id}.wav"
    )


# ==================== PREVIEW ENDPOINT ====================

@app.post("/api/preview", response_model=PreviewResponse)
async def generate_preview(request: PreviewRequest):
    """Generate a preview of the mixed audio with current settings"""
    if request.job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[request.job_id]
    
    if job["status"] != ProcessingStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Analysis not complete")
    
    # Convert mix config to mixer format
    tracks_config = []
    job_tracks = {t["id"]: t for t in job.get("tracks", [])}
    
    for tc in request.mix_config.tracks:
        if tc.track_id not in job_tracks:
            continue
        
        job_track = job_tracks[tc.track_id]
        tracks_config.append(MixerTrackConfig(
            track_id=tc.track_id,
            file_path=Path(job_track["file_path"]),
            muted=tc.muted,
            solo=tc.solo,
            volume=tc.volume,
            is_main=tc.is_main
        ))
    
    if not tracks_config:
        raise HTTPException(status_code=400, detail="No valid tracks in mix configuration")
    
    # Create preview
    output_dir = settings.output_dir / request.job_id / "previews"
    output_dir.mkdir(parents=True, exist_ok=True)
    preview_path = output_dir / f"preview_{uuid.uuid4().hex[:8]}.wav"
    
    mix_settings = MixSettings(
        main_speaker_boost_db=request.mix_config.main_speaker_boost_db,
        noise_reduction_level=request.mix_config.noise_reduction_level,
        normalize=request.mix_config.normalize
    )
    
    mixer = AudioMixer()
    mixer.create_preview(
        tracks_config,
        mix_settings,
        request.start_time,
        request.duration,
        preview_path
    )
    
    # Return URL to preview
    preview_url = f"/audio/{request.job_id}/previews/{preview_path.name}"
    
    return PreviewResponse(
        preview_url=preview_url,
        duration_seconds=request.duration
    )


# ==================== EXPORT ENDPOINT ====================

@app.post("/api/export", response_model=ExportResponse)
async def export_audio(request: ExportRequest):
    """Export the final mixed audio with current settings"""
    if request.job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[request.job_id]
    
    if job["status"] != ProcessingStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Analysis not complete")
    
    # Convert mix config to mixer format
    tracks_config = []
    job_tracks = {t["id"]: t for t in job.get("tracks", [])}
    
    for tc in request.mix_config.tracks:
        if tc.track_id not in job_tracks:
            continue
        
        job_track = job_tracks[tc.track_id]
        tracks_config.append(MixerTrackConfig(
            track_id=tc.track_id,
            file_path=Path(job_track["file_path"]),
            muted=tc.muted,
            solo=tc.solo,
            volume=tc.volume,
            is_main=tc.is_main
        ))
    
    if not tracks_config:
        raise HTTPException(status_code=400, detail="No valid tracks in mix configuration")
    
    # Determine output filename
    output_format = request.mix_config.output_format
    original_stem = Path(job["original_filename"]).stem
    filename = request.filename or f"{original_stem}_mixed.{output_format}"
    
    output_dir = settings.output_dir / request.job_id / "exports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    
    # Mix and export
    mix_settings = MixSettings(
        main_speaker_boost_db=request.mix_config.main_speaker_boost_db,
        noise_reduction_level=request.mix_config.noise_reduction_level,
        normalize=request.mix_config.normalize,
        output_format=output_format
    )
    
    mixer = AudioMixer()
    _, file_size = mixer.export(tracks_config, mix_settings, output_path)
    
    download_url = f"/audio/{request.job_id}/exports/{filename}"
    
    return ExportResponse(
        download_url=download_url,
        filename=filename,
        file_size_bytes=file_size,
        duration_seconds=job["duration_seconds"],
        format=output_format
    )


# ==================== CLEANUP ENDPOINT ====================

@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and all associated files"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # Remove files
    job_dir = Path(job["job_dir"])
    output_dir = settings.output_dir / job_id
    
    if job_dir.exists():
        shutil.rmtree(job_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    # Remove from memory
    del jobs[job_id]
    
    return {"message": "Job deleted successfully"}


# ==================== HEALTH CHECK ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
