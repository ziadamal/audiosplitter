// Types for the VoxSplit audio separator application

export type ProcessingStatus = 
  | 'pending'
  | 'processing'
  | 'separating'
  | 'diarizing'
  | 'complete'
  | 'failed';

export type TrackType = 'speaker' | 'noise' | 'vocals' | 'drums' | 'bass' | 'other';

export interface SpeakerSegment {
  start: number;
  end: number;
  speaker_id: string;
  confidence: number;
}

export interface Track {
  id: string;
  name: string;
  type: TrackType;
  file_path: string;
  duration_seconds: number;
  segments: SpeakerSegment[];
  waveform_data: number[] | null;
  color: string;
}

export interface TrackConfig {
  track_id: string;
  muted: boolean;
  solo: boolean;
  volume: number;
  is_main: boolean;
}

export interface MixConfig {
  job_id: string;
  tracks: TrackConfig[];
  main_speaker_boost_db: number;
  noise_reduction_level: number;
  output_format: string;
  normalize: boolean;
}

export interface UploadResponse {
  job_id: string;
  filename: string;
  duration_seconds: number;
  sample_rate: number;
  status: ProcessingStatus;
  message: string;
}

export interface AnalysisResult {
  job_id: string;
  status: ProcessingStatus;
  original_filename: string;
  duration_seconds: number;
  speaker_count: number;
  tracks: Track[];
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
}

export interface JobStatusResponse {
  job_id: string;
  status: ProcessingStatus;
  progress: number;
  current_step: string;
  result: AnalysisResult | null;
}

export interface PreviewResponse {
  preview_url: string;
  duration_seconds: number;
}

export interface ExportResponse {
  download_url: string;
  filename: string;
  file_size_bytes: number;
  duration_seconds: number;
  format: string;
}

// UI State types
export interface TrackUIState extends Track {
  muted: boolean;
  solo: boolean;
  volume: number;
  isMain: boolean;
}

export interface AppState {
  uploadedFile: File | null;
  uploadProgress: number;
  jobId: string | null;
  status: ProcessingStatus;
  progress: number;
  currentStep: string;
  result: AnalysisResult | null;
  tracks: TrackUIState[];
  mainSpeakerBoostDb: number;
  noiseReductionLevel: number;
  outputFormat: 'wav' | 'mp3' | 'flac';
  normalize: boolean;
  isPlaying: boolean;
  currentTime: number;
  isExporting: boolean;
  exportUrl: string | null;
  error: string | null;
}

export interface AppActions {
  setUploadedFile: (file: File | null) => void;
  setJobId: (jobId: string | null) => void;
  setStatus: (status: ProcessingStatus) => void;
  setProgress: (progress: number) => void;
  setCurrentStep: (step: string) => void;
  setResult: (result: AnalysisResult | null) => void;
  setTracks: (tracks: TrackUIState[]) => void;
  toggleTrackMute: (trackId: string) => void;
  toggleTrackSolo: (trackId: string) => void;
  setTrackVolume: (trackId: string, volume: number) => void;
  setMainSpeaker: (trackId: string) => void;
  setMainSpeakerBoostDb: (db: number) => void;
  setNoiseReductionLevel: (level: number) => void;
  setOutputFormat: (format: 'wav' | 'mp3' | 'flac') => void;
  setNormalize: (normalize: boolean) => void;
  setIsPlaying: (playing: boolean) => void;
  setCurrentTime: (time: number) => void;
  setIsExporting: (exporting: boolean) => void;
  setExportUrl: (url: string | null) => void;
  setError: (error: string | null) => void;
  reset: () => void;
  getMixConfig: () => MixConfig;
}
