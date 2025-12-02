import React, { useState, useRef, useEffect } from 'react';
import { 
  Play, 
  Pause, 
  Download, 
  RefreshCw,
  FileAudio,
  CheckCircle,
  Loader2
} from 'lucide-react';
import { useStore } from '../stores/useStore';
import { useAudioExport, useAudioPreview } from '../hooks/useAudioAnalysis';
import audioApi from '../services/api';

export function AudioPlayer() {
  const { tracks, result, jobId, outputFormat, setOutputFormat, normalize, setNormalize } = useStore();
  const { exportAudio, isExporting } = useAudioExport();
  const { generatePreview, isGenerating } = useAudioPreview();
  
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [hasGeneratedPreview, setHasGeneratedPreview] = useState(false);

  if (!result || tracks.length === 0) {
    return null;
  }

  const handleGeneratePreview = async () => {
    const url = await generatePreview(0, Math.min(60, result.duration_seconds));
    if (url) {
      setPreviewUrl(url);
      setHasGeneratedPreview(true);
    }
  };

  const handlePlayPause = async () => {
    if (!previewUrl) {
      await handleGeneratePreview();
      return;
    }

    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const handleExport = () => {
    exportAudio();
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Reset preview when tracks change
  useEffect(() => {
    setHasGeneratedPreview(false);
    setPreviewUrl(null);
    setIsPlaying(false);
  }, [tracks.map(t => `${t.muted}-${t.solo}-${t.volume}-${t.isMain}`).join('')]);

  return (
    <div className="space-y-6">
      {/* Audio element */}
      {previewUrl && (
        <audio
          ref={audioRef}
          src={previewUrl}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onEnded={() => setIsPlaying(false)}
        />
      )}

      {/* Player controls */}
      <div className="bg-zinc-900/80 backdrop-blur-sm border border-zinc-800 rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-zinc-200 mb-4 flex items-center gap-2">
          <FileAudio className="w-5 h-5 text-amber-400" />
          Preview & Export
        </h3>

        {/* Playback controls */}
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={handlePlayPause}
            disabled={isGenerating}
            className="w-14 h-14 rounded-full bg-amber-500 hover:bg-amber-400 
              flex items-center justify-center transition-all
              disabled:opacity-50 disabled:cursor-not-allowed
              hover:scale-105 active:scale-95"
          >
            {isGenerating ? (
              <Loader2 className="w-6 h-6 text-zinc-900 animate-spin" />
            ) : isPlaying ? (
              <Pause className="w-6 h-6 text-zinc-900" />
            ) : (
              <Play className="w-6 h-6 text-zinc-900 ml-1" />
            )}
          </button>

          {/* Progress bar */}
          <div className="flex-1">
            <input
              type="range"
              min="0"
              max={duration || result.duration_seconds}
              value={currentTime}
              onChange={handleSeek}
              disabled={!previewUrl}
              className="w-full h-2 bg-zinc-800 rounded-full appearance-none cursor-pointer
                [&::-webkit-slider-thumb]:appearance-none
                [&::-webkit-slider-thumb]:w-4
                [&::-webkit-slider-thumb]:h-4
                [&::-webkit-slider-thumb]:rounded-full
                [&::-webkit-slider-thumb]:bg-amber-400
                [&::-webkit-slider-thumb]:cursor-pointer
                disabled:opacity-50
              "
            />
            <div className="flex justify-between text-xs text-zinc-500 mt-1">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration || result.duration_seconds)}</span>
            </div>
          </div>

          {/* Regenerate preview */}
          {hasGeneratedPreview && (
            <button
              onClick={handleGeneratePreview}
              disabled={isGenerating}
              className="p-3 rounded-xl bg-zinc-800 hover:bg-zinc-700 
                text-zinc-400 hover:text-zinc-200 transition-all
                disabled:opacity-50"
              title="Regenerate preview with current settings"
            >
              <RefreshCw className={`w-5 h-5 ${isGenerating ? 'animate-spin' : ''}`} />
            </button>
          )}
        </div>

        {/* Preview status */}
        {!hasGeneratedPreview && (
          <p className="text-sm text-zinc-500 mb-6">
            Click play to generate a preview with your current mix settings
          </p>
        )}
        {hasGeneratedPreview && (
          <p className="text-sm text-emerald-400 mb-6 flex items-center gap-2">
            <CheckCircle className="w-4 h-4" />
            Preview generated. Adjust tracks and click refresh to update.
          </p>
        )}

        {/* Export options */}
        <div className="border-t border-zinc-800 pt-6">
          <div className="flex flex-wrap items-end gap-4">
            {/* Format selection */}
            <div>
              <label className="block text-sm text-zinc-400 mb-2">Format</label>
              <div className="flex gap-2">
                {(['wav', 'mp3', 'flac'] as const).map(format => (
                  <button
                    key={format}
                    onClick={() => setOutputFormat(format)}
                    className={`
                      px-4 py-2 rounded-lg text-sm font-medium uppercase
                      transition-all
                      ${outputFormat === format
                        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50'
                        : 'bg-zinc-800 text-zinc-400 border border-zinc-700 hover:border-zinc-600'
                      }
                    `}
                  >
                    {format}
                  </button>
                ))}
              </div>
            </div>

            {/* Normalize toggle */}
            <div>
              <label className="block text-sm text-zinc-400 mb-2">Normalize</label>
              <button
                onClick={() => setNormalize(!normalize)}
                className={`
                  px-4 py-2 rounded-lg text-sm font-medium
                  transition-all
                  ${normalize
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50'
                    : 'bg-zinc-800 text-zinc-400 border border-zinc-700 hover:border-zinc-600'
                  }
                `}
              >
                {normalize ? 'On' : 'Off'}
              </button>
            </div>

            {/* Export button */}
            <div className="flex-1 flex justify-end">
              <button
                onClick={handleExport}
                disabled={isExporting}
                className="px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 
                  hover:from-amber-400 hover:to-orange-400
                  text-zinc-900 font-semibold rounded-xl
                  flex items-center gap-2 transition-all
                  hover:scale-105 active:scale-95
                  disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                {isExporting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Exporting...
                  </>
                ) : (
                  <>
                    <Download className="w-5 h-5" />
                    Export Audio
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
