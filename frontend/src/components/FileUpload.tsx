import React, { useCallback, useState } from 'react';
import { Upload, FileAudio, X, AlertCircle } from 'lucide-react';
import { useStore } from '../stores/useStore';
import { useAudioAnalysis } from '../hooks/useAudioAnalysis';

const ALLOWED_TYPES = [
  'audio/mpeg',
  'audio/wav',
  'audio/wave',
  'audio/x-wav',
  'audio/mp4',
  'audio/x-m4a',
  'audio/flac',
  'audio/ogg',
  'audio/aac',
];

const ALLOWED_EXTENSIONS = ['mp3', 'wav', 'm4a', 'flac', 'ogg', 'aac'];

export function FileUpload() {
  const { uploadedFile, error } = useStore();
  const { uploadAndAnalyze, isUploading, uploadProgress } = useAudioAnalysis();
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const validateFile = (file: File): boolean => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    
    if (!extension || !ALLOWED_EXTENSIONS.includes(extension)) {
      setValidationError(`Invalid file type. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`);
      return false;
    }

    // 500MB max
    if (file.size > 500 * 1024 * 1024) {
      setValidationError('File too large. Maximum size: 500MB');
      return false;
    }

    setValidationError(null);
    return true;
  };

  const handleFile = useCallback((file: File) => {
    if (validateFile(file)) {
      uploadAndAnalyze(file);
    }
  }, [uploadAndAnalyze]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  }, [handleFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  }, [handleFile]);

  const displayError = validationError || error;

  return (
    <div className="w-full">
      <div
        className={`
          relative border-2 border-dashed rounded-2xl p-12
          transition-all duration-300 ease-out
          ${isDragging 
            ? 'border-amber-400 bg-amber-950/30 scale-[1.02]' 
            : 'border-zinc-700 hover:border-zinc-500 bg-zinc-900/50'
          }
          ${isUploading ? 'pointer-events-none' : 'cursor-pointer'}
        `}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <input
          type="file"
          accept={ALLOWED_EXTENSIONS.map(ext => `.${ext}`).join(',')}
          onChange={handleInputChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={isUploading}
        />

        <div className="flex flex-col items-center text-center">
          {isUploading ? (
            <>
              <div className="relative w-20 h-20 mb-6">
                <svg className="w-20 h-20 transform -rotate-90">
                  <circle
                    cx="40"
                    cy="40"
                    r="36"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                    className="text-zinc-800"
                  />
                  <circle
                    cx="40"
                    cy="40"
                    r="36"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                    strokeDasharray={`${2 * Math.PI * 36}`}
                    strokeDashoffset={`${2 * Math.PI * 36 * (1 - uploadProgress / 100)}`}
                    className="text-amber-400 transition-all duration-300"
                    strokeLinecap="round"
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-lg font-medium text-amber-400">
                  {uploadProgress}%
                </span>
              </div>
              <p className="text-zinc-400">Uploading {uploadedFile?.name}...</p>
            </>
          ) : (
            <>
              <div className={`
                w-20 h-20 rounded-2xl flex items-center justify-center mb-6
                transition-all duration-300
                ${isDragging ? 'bg-amber-500/20' : 'bg-zinc-800'}
              `}>
                {isDragging ? (
                  <FileAudio className="w-10 h-10 text-amber-400" />
                ) : (
                  <Upload className="w-10 h-10 text-zinc-500" />
                )}
              </div>
              
              <h3 className="text-xl font-semibold text-zinc-200 mb-2">
                {isDragging ? 'Drop your audio file' : 'Upload audio file'}
              </h3>
              <p className="text-zinc-500 mb-4">
                Drag and drop or click to browse
              </p>
              <p className="text-sm text-zinc-600">
                Supports MP3, WAV, M4A, FLAC, OGG, AAC • Max 500MB
              </p>
            </>
          )}
        </div>
      </div>

      {displayError && (
        <div className="mt-4 p-4 bg-red-950/50 border border-red-800/50 rounded-xl flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-red-300 text-sm">{displayError}</p>
        </div>
      )}
    </div>
  );
}
