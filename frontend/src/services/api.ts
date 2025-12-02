import axios from 'axios';
import type {
  UploadResponse,
  JobStatusResponse,
  MixConfig,
  PreviewResponse,
  ExportResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const audioApi = {
  /**
   * Upload an audio file for processing
   */
  uploadFile: async (
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<UploadResponse>('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(progress);
        }
      },
    });

    return response.data;
  },

  /**
   * Start the analysis process for an uploaded file
   */
  startAnalysis: async (jobId: string): Promise<JobStatusResponse> => {
    const response = await api.post<JobStatusResponse>(`/api/analyze/${jobId}`);
    return response.data;
  },

  /**
   * Get the current status of a processing job
   */
  getJobStatus: async (jobId: string): Promise<JobStatusResponse> => {
    const response = await api.get<JobStatusResponse>(`/api/status/${jobId}`);
    return response.data;
  },

  /**
   * Get all tracks for a completed job
   */
  getTracks: async (jobId: string) => {
    const response = await api.get(`/api/tracks/${jobId}`);
    return response.data;
  },

  /**
   * Get the audio URL for a specific track
   */
  getTrackAudioUrl: (jobId: string, trackId: string): string => {
    return `${API_BASE_URL}/api/tracks/${jobId}/${trackId}/audio`;
  },

  /**
   * Generate a preview of the mixed audio
   */
  generatePreview: async (
    jobId: string,
    mixConfig: MixConfig,
    startTime: number = 0,
    duration: number = 30
  ): Promise<PreviewResponse> => {
    const response = await api.post<PreviewResponse>('/api/preview', {
      job_id: jobId,
      mix_config: mixConfig,
      start_time: startTime,
      duration: duration,
    });
    return response.data;
  },

  /**
   * Export the final mixed audio
   */
  exportAudio: async (
    jobId: string,
    mixConfig: MixConfig,
    filename?: string
  ): Promise<ExportResponse> => {
    const response = await api.post<ExportResponse>('/api/export', {
      job_id: jobId,
      mix_config: mixConfig,
      filename: filename,
    });
    return response.data;
  },

  /**
   * Delete a job and all associated files
   */
  deleteJob: async (jobId: string): Promise<void> => {
    await api.delete(`/api/jobs/${jobId}`);
  },

  /**
   * Get the full URL for an audio file path
   */
  getAudioUrl: (path: string): string => {
    if (path.startsWith('http')) {
      return path;
    }
    return `${API_BASE_URL}${path}`;
  },
};

export default audioApi;
