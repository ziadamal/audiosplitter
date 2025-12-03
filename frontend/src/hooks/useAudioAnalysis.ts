import { useState, useCallback, useEffect, useRef } from 'react';
import { useStore } from '../stores/useStore';
import audioApi from '../services/api';

export function useAudioAnalysis() {
  const { jobId, setJobId, setStatus, setProgress, setCurrentStep, setResult, setError, setUploadedFile } = useStore();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => { return () => { if (pollingRef.current) clearInterval(pollingRef.current); }; }, []);

  const uploadAndAnalyze = useCallback(async (file: File) => {
    setIsUploading(true); setUploadProgress(0); setError(null); setUploadedFile(file);
    try {
      const uploadResponse = await audioApi.uploadFile(file, (progress) => setUploadProgress(progress));
      setJobId(uploadResponse.job_id); setStatus('pending');
      await audioApi.startAnalysis(uploadResponse.job_id);
      setStatus('processing'); pollJobStatus(uploadResponse.job_id);
    } catch (error: any) {
      console.error('Upload/analysis error:', error);
      setError(error.response?.data?.detail || error.message || 'An error occurred'); setStatus('failed');
    } finally { setIsUploading(false); }
  }, [setJobId, setStatus, setError, setUploadedFile]);

  const pollJobStatus = useCallback((jobId: string) => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    const poll = async () => {
      try {
        const status = await audioApi.getJobStatus(jobId);
        setStatus(status.status); setProgress(status.progress); setCurrentStep(status.current_step);
        if (status.status === 'complete' && status.result) { setResult(status.result); if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; } }
        else if (status.status === 'failed') { setError(status.result?.error_message || 'Processing failed'); if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; } }
      } catch (error: any) { console.error('Polling error:', error); setError('Failed to get job status'); if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; } }
    };
    poll(); pollingRef.current = setInterval(poll, 2000);
  }, [setStatus, setProgress, setCurrentStep, setResult, setError]);

  const cancelAnalysis = useCallback(async () => {
    if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
    if (jobId) { try { await audioApi.deleteJob(jobId); } catch (error) { console.error('Failed to delete job:', error); } }
    setJobId(null); setStatus('pending'); setProgress(0); setCurrentStep(''); setResult(null); setUploadedFile(null);
  }, [jobId, setJobId, setStatus, setProgress, setCurrentStep, setResult, setUploadedFile]);

  return { uploadAndAnalyze, cancelAnalysis, isUploading, uploadProgress };
}

export function useAudioExport() {
  const { jobId, getMixConfig, setIsExporting, setExportUrl, setError } = useStore();
  const [isExporting, setLocalIsExporting] = useState(false);

  const exportAudio = useCallback(async (filename?: string) => {
    if (!jobId) { setError('No job to export'); return; }
    setLocalIsExporting(true); setIsExporting(true); setError(null);
    try {
      const mixConfig = getMixConfig();
      const response = await audioApi.exportAudio(jobId, mixConfig, filename);
      const downloadUrl = audioApi.getAudioUrl(response.download_url);
      setExportUrl(downloadUrl);
      const link = document.createElement('a'); link.href = downloadUrl; link.download = response.filename;
      document.body.appendChild(link); link.click(); document.body.removeChild(link);
    } catch (error: any) { console.error('Export error:', error); setError(error.response?.data?.detail || error.message || 'Export failed'); }
    finally { setLocalIsExporting(false); setIsExporting(false); }
  }, [jobId, getMixConfig, setIsExporting, setExportUrl, setError]);

  return { exportAudio, isExporting };
}

export function useAudioPreview() {
  const { jobId, getMixConfig, setError } = useStore();
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const generatePreview = useCallback(async (startTime: number = 0, duration: number = 30) => {
    if (!jobId) { setError('No job to preview'); return null; }
    setIsGenerating(true); setError(null);
    try {
      const mixConfig = getMixConfig();
      const response = await audioApi.generatePreview(jobId, mixConfig, startTime, duration);
      const url = audioApi.getAudioUrl(response.preview_url);
      setPreviewUrl(url); return url;
    } catch (error: any) { console.error('Preview error:', error); setError(error.response?.data?.detail || error.message || 'Preview generation failed'); return null; }
    finally { setIsGenerating(false); }
  }, [jobId, getMixConfig, setError]);

  return { generatePreview, previewUrl, isGenerating };
}
