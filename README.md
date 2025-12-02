# VoxSplit - Audio Source Separation & Speaker Diarization Application

A full-stack application for separating speakers and background noise from audio files, with an intuitive mixing interface.

![VoxSplit Architecture](https://via.placeholder.com/800x400?text=VoxSplit+Audio+Separator)

## Features

- **Audio Upload & Analysis**: Upload MP3, WAV, M4A, FLAC, OGG, AAC files up to 500MB
- **Source Separation**: AI-powered separation of vocals from background noise using Facebook's Demucs
- **Speaker Diarization**: Automatic detection and separation of multiple speakers using pyannote.audio
- **Track Management**: Mute, solo, adjust volume, and set main speaker for each track
- **Real-time Preview**: Listen to your mix before exporting
- **Flexible Export**: Export in WAV, MP3, or FLAC formats with normalization options

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Upload    │  │   Track     │  │   Audio     │  │      Export         │ │
│  │   Module    │  │   Manager   │  │   Player    │  │      Module         │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BACKEND (FastAPI)                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Upload    │  │  Analysis   │  │   Mix       │  │     Export          │ │
│  │   API       │  │   API       │  │   API       │  │     API             │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AUDIO PROCESSING PIPELINE                             │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │   Source Separation │  │  Speaker Diarization│  │   Audio Mixing      │  │
│  │   (Demucs)          │  │  (pyannote.audio)   │  │   (scipy/pydub)     │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI | High-performance async API |
| Source Separation | Demucs (htdemucs) | Separate vocals from background |
| Speaker Diarization | pyannote.audio 3.1 | Detect and segment speakers |
| Audio Processing | pydub, scipy, librosa | Mix, normalize, convert |
| Task Queue | Celery + Redis | Async processing |

### Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | React 18 + TypeScript | UI components |
| Styling | Tailwind CSS | Responsive design |
| State Management | Zustand | Global state |
| HTTP Client | Axios | API communication |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- FFmpeg
- CUDA-capable GPU (recommended) or CPU
- Hugging Face account with access to pyannote models

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/audio-separator.git
cd audio-separator
```

### 2. Get Hugging Face Token

1. Create account at [huggingface.co](https://huggingface.co)
2. Accept terms at:
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0
3. Get token from: https://huggingface.co/settings/tokens

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your HF_TOKEN
```

### 4. Start with Docker (Recommended)

```bash
docker-compose up -d
```

### 5. Or Start Manually

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 6. Open Application

Navigate to http://localhost:3000

## API Reference

### Endpoints

#### Upload Audio
```http
POST /api/upload
Content-Type: multipart/form-data

file: <audio_file>
```

**Response:**
```json
{
  "job_id": "abc123def456",
  "filename": "podcast.mp3",
  "duration_seconds": 1234.56,
  "sample_rate": 44100,
  "status": "pending",
  "message": "File uploaded. Estimated processing time: 300 seconds"
}
```

#### Start Analysis
```http
POST /api/analyze/{job_id}
```

**Response:**
```json
{
  "job_id": "abc123def456",
  "status": "processing",
  "progress": 0,
  "current_step": "Starting analysis..."
}
```

#### Check Status
```http
GET /api/status/{job_id}
```

**Response:**
```json
{
  "job_id": "abc123def456",
  "status": "complete",
  "progress": 100,
  "current_step": "Complete",
  "result": {
    "speaker_count": 3,
    "tracks": [
      {
        "id": "speaker_0",
        "name": "Speaker 1",
        "type": "speaker",
        "color": "#3B82F6",
        "waveform_data": [0.1, 0.3, ...]
      },
      {
        "id": "noise",
        "name": "Background / Noise",
        "type": "noise",
        "color": "#6B7280"
      }
    ]
  }
}
```

#### Generate Preview
```http
POST /api/preview
Content-Type: application/json

{
  "job_id": "abc123def456",
  "mix_config": {
    "tracks": [
      {"track_id": "speaker_0", "muted": false, "solo": false, "volume": 1.0, "is_main": true},
      {"track_id": "speaker_1", "muted": true, "solo": false, "volume": 1.0, "is_main": false},
      {"track_id": "noise", "muted": true, "solo": false, "volume": 0.5, "is_main": false}
    ],
    "main_speaker_boost_db": 3.0,
    "noise_reduction_level": 0.5,
    "normalize": true
  },
  "start_time": 0,
  "duration": 30
}
```

#### Export Audio
```http
POST /api/export
Content-Type: application/json

{
  "job_id": "abc123def456",
  "mix_config": { ... },
  "filename": "my_cleaned_audio.wav"
}
```

**Response:**
```json
{
  "download_url": "/audio/abc123def456/exports/my_cleaned_audio.wav",
  "filename": "my_cleaned_audio.wav",
  "file_size_bytes": 12345678,
  "duration_seconds": 1234.56,
  "format": "wav"
}
```

## Data Structures

### Track Configuration
```typescript
interface TrackConfig {
  track_id: string;      // Track identifier
  muted: boolean;        // Is track muted
  solo: boolean;         // Is track soloed
  volume: number;        // Volume multiplier (0-2)
  is_main: boolean;      // Is this the main speaker
}
```

### Mix Configuration
```typescript
interface MixConfig {
  job_id: string;
  tracks: TrackConfig[];
  main_speaker_boost_db: number;  // dB boost for main speaker (0-10)
  noise_reduction_level: number;  // 0-1
  output_format: 'wav' | 'mp3' | 'flac';
  normalize: boolean;
}
```

## Processing Pipeline

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│   Upload    │───▶│   Convert    │───▶│ Source Separate │───▶│  Diarize     │
│   Audio     │    │   to WAV     │    │ (Demucs)        │    │  (pyannote)  │
└─────────────┘    └──────────────┘    └─────────────────┘    └──────────────┘
                                               │                      │
                                               ▼                      ▼
                                        ┌──────────────┐    ┌──────────────┐
                                        │   Vocals     │    │  Speaker 1   │
                                        │   Track      │    │  Track       │
                                        └──────────────┘    └──────────────┘
                                               │                      │
                                        ┌──────────────┐    ┌──────────────┐
                                        │   Noise      │    │  Speaker 2   │
                                        │   Track      │    │  Track       │
                                        └──────────────┘    └──────────────┘
```

## Directory Structure

```
audio-separator/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app & endpoints
│   │   ├── config.py         # Settings
│   │   ├── models/
│   │   │   └── schemas.py    # Pydantic models
│   │   ├── services/
│   │   │   ├── separation.py # Demucs integration
│   │   │   ├── diarization.py# pyannote integration
│   │   │   └── mixer.py      # Audio mixing
│   │   └── utils/
│   │       └── audio.py      # Utilities
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks
│   │   ├── stores/           # Zustand store
│   │   ├── services/         # API client
│   │   └── types/            # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Performance Considerations

| Hardware | 10min Audio | 1hr Audio |
|----------|-------------|-----------|
| GPU (RTX 3080) | ~3 min | ~15 min |
| CPU (8-core) | ~15 min | ~90 min |

## Troubleshooting

### "pyannote model not found"
Make sure you've accepted the model terms on Hugging Face and your token has access.

### "CUDA out of memory"
Try reducing batch size or use CPU fallback by setting `CUDA_VISIBLE_DEVICES=""`.

### "Audio file not supported"
Ensure FFmpeg is installed: `apt install ffmpeg` or `brew install ffmpeg`.

## License

MIT License - See LICENSE file for details.

## Acknowledgments

- [Facebook Demucs](https://github.com/facebookresearch/demucs) - Source separation
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) - Speaker diarization
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
