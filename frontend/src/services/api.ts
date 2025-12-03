import axios from 'axios';
import type { UploadResponse, JobStatusResponse, MixConfig, PreviewResponse, ExportResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://voxsplit-backend.onrender.com';
console.log('API Base URL:', API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 300000,
});

api.interceptors.request.use(
  (config) => { console.log('API Request:', config.method?.toUpperCase(), config.url); return config; },
  (error) => { console.error('API Request Error:', error); return Promise.reject(error); }
);

api.interceptors.response.use(
  (response) => { console.log('API Response:', response.status, response.config.url); return response; },
  (error) => { console.error('API Response Error:', error.response?.status, error.config?.url, error.message); return Promise.reject(error); }
);

export const audioApi = {
  uploadFile: async (file: File, onProgress?: (progress: number) => void): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<UploadResponse>('/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          onProgress(Math.round((progressEvent.loaded * 100) / progressEvent.total));
        }
      },
    });
    return response.data;
  },

  startAnalysis: async (jobId: string): Promise<JobStatusResponse> => {
    const response = await api.post<JobStatusResponse>(`/api/analyze/${jobId}`);
    return response.data;
  },

  getJobStatus: async (jobId: string): Promise<JobStatusResponse> => {
    const response = await api.get<JobStatusResponse>(`/api/status/${jobId}`);
    return response.data;
  },

  getTracks: async (jobId: string) => {
    const response = await api.get(`/api/tracks/${jobId}`);
    return response.data;
  },

  getTrackAudioUrl: (jobId: string, trackId: string): string => {
    return `${API_BASE_URL}/api/tracks/${jobId}/${trackId}/audio`;
  },

  generatePreview: async (jobId: string, mixConfig: MixConfig, startTime: number = 0, duration: number = 30): Promise<PreviewResponse> => {
    const response = await api.post<PreviewResponse>('/api/preview', {
      job_id: jobId,
      mix_config: mixConfig,
      start_time: startTime,
      duration: duration,
    });
    return response.data;
  },

  exportAudio: async (jobId: string, mixConfig: MixConfig, filename?: string): Promise<ExportResponse> => {
    const response = await api.post<ExportResponse>('/api/export', {
      job_id: jobId,
      mix_config: mixConfig,
      filename: filename,
    });
    return response.data;
  },

  deleteJob: async (jobId: string): Promise<void> => {
    await api.delete(`/api/jobs/${jobId}`);
  },

  getAudioUrl: (path: string): string => {
    if (path.startsWith('http')) return path;
    return `${API_BASE_URL}${path}`;
  },
};

export default audioApi;
