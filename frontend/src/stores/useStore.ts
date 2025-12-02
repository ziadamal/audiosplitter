import { create } from 'zustand';
import type { 
  AppState, 
  AppActions, 
  TrackUIState, 
  AnalysisResult, 
  ProcessingStatus,
  MixConfig 
} from '../types';

const initialState: AppState = {
  uploadedFile: null,
  uploadProgress: 0,
  jobId: null,
  status: 'pending',
  progress: 0,
  currentStep: '',
  result: null,
  tracks: [],
  mainSpeakerBoostDb: 3.0,
  noiseReductionLevel: 0,
  outputFormat: 'wav',
  normalize: true,
  isPlaying: false,
  currentTime: 0,
  isExporting: false,
  exportUrl: null,
  error: null,
};

export const useStore = create<AppState & AppActions>((set, get) => ({
  ...initialState,

  setUploadedFile: (file) => set({ uploadedFile: file }),
  setJobId: (jobId) => set({ jobId }),
  setStatus: (status) => set({ status }),
  setProgress: (progress) => set({ progress }),
  setCurrentStep: (currentStep) => set({ currentStep }),
  
  setResult: (result) => {
    if (result) {
      // Convert tracks to UI state with default values
      const tracks: TrackUIState[] = result.tracks.map((track, index) => ({
        ...track,
        muted: false,
        solo: false,
        volume: 1.0,
        isMain: index === 0 && track.type === 'speaker', // First speaker is main by default
      }));
      set({ result, tracks });
    } else {
      set({ result: null, tracks: [] });
    }
  },
  
  setTracks: (tracks) => set({ tracks }),

  toggleTrackMute: (trackId) => {
    const { tracks } = get();
    set({
      tracks: tracks.map(track =>
        track.id === trackId
          ? { ...track, muted: !track.muted }
          : track
      ),
    });
  },

  toggleTrackSolo: (trackId) => {
    const { tracks } = get();
    set({
      tracks: tracks.map(track =>
        track.id === trackId
          ? { ...track, solo: !track.solo }
          : track
      ),
    });
  },

  setTrackVolume: (trackId, volume) => {
    const { tracks } = get();
    set({
      tracks: tracks.map(track =>
        track.id === trackId
          ? { ...track, volume: Math.max(0, Math.min(2, volume)) }
          : track
      ),
    });
  },

  setMainSpeaker: (trackId) => {
    const { tracks } = get();
    set({
      tracks: tracks.map(track => ({
        ...track,
        isMain: track.id === trackId,
      })),
    });
  },

  setMainSpeakerBoostDb: (db) => set({ mainSpeakerBoostDb: db }),
  setNoiseReductionLevel: (level) => set({ noiseReductionLevel: level }),
  setOutputFormat: (format) => set({ outputFormat: format }),
  setNormalize: (normalize) => set({ normalize }),

  setIsPlaying: (isPlaying) => set({ isPlaying }),
  setCurrentTime: (currentTime) => set({ currentTime }),

  setIsExporting: (isExporting) => set({ isExporting }),
  setExportUrl: (exportUrl) => set({ exportUrl }),

  setError: (error) => set({ error }),

  reset: () => set(initialState),

  getMixConfig: (): MixConfig => {
    const state = get();
    return {
      job_id: state.jobId || '',
      tracks: state.tracks.map(track => ({
        track_id: track.id,
        muted: track.muted,
        solo: track.solo,
        volume: track.volume,
        is_main: track.isMain,
      })),
      main_speaker_boost_db: state.mainSpeakerBoostDb,
      noise_reduction_level: state.noiseReductionLevel,
      output_format: state.outputFormat,
      normalize: state.normalize,
    };
  },
}));
