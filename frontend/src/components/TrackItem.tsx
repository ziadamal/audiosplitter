import React, { useRef, useEffect } from 'react';
import { 
  Volume2, 
  VolumeX, 
  Headphones, 
  Star,
  User,
  Radio
} from 'lucide-react';
import { useStore } from '../stores/useStore';
import type { TrackUIState } from '../types';

interface TrackItemProps {
  track: TrackUIState;
}

export function TrackItem({ track }: TrackItemProps) {
  const { toggleTrackMute, toggleTrackSolo, setTrackVolume, setMainSpeaker } = useStore();
  const waveformRef = useRef<HTMLCanvasElement>(null);

  // Draw waveform
  useEffect(() => {
    if (!waveformRef.current || !track.waveform_data) return;

    const canvas = waveformRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    // Clear
    ctx.clearRect(0, 0, rect.width, rect.height);

    // Draw waveform
    const data = track.waveform_data;
    const barWidth = rect.width / data.length;
    const maxHeight = rect.height / 2;

    ctx.fillStyle = track.muted ? '#3f3f46' : track.color;
    
    for (let i = 0; i < data.length; i++) {
      const x = i * barWidth;
      const height = data[i] * maxHeight;
      
      // Draw mirrored bars
      ctx.fillRect(x, maxHeight - height, barWidth - 1, height * 2);
    }
  }, [track.waveform_data, track.color, track.muted]);

  const isSpeaker = track.type === 'speaker';
  const isNoise = track.type === 'noise' || track.type === 'other';

  return (
    <div
      className={`
        group relative bg-zinc-900/80 backdrop-blur-sm border rounded-2xl p-5
        transition-all duration-300
        ${track.muted 
          ? 'border-zinc-800 opacity-60' 
          : track.solo 
            ? 'border-amber-500/50 ring-2 ring-amber-500/20' 
            : track.isMain 
              ? 'border-emerald-500/50 ring-2 ring-emerald-500/20' 
              : 'border-zinc-800 hover:border-zinc-700'
        }
      `}
    >
      {/* Track header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          {/* Track icon */}
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: `${track.color}20` }}
          >
            {isSpeaker ? (
              <User className="w-5 h-5" style={{ color: track.color }} />
            ) : (
              <Radio className="w-5 h-5" style={{ color: track.color }} />
            )}
          </div>
          
          {/* Track name and badges */}
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-semibold text-zinc-200">{track.name}</h4>
              {track.isMain && (
                <span className="px-2 py-0.5 text-xs font-medium bg-emerald-500/20 text-emerald-400 rounded-full">
                  Main
                </span>
              )}
            </div>
            <p className="text-xs text-zinc-500 capitalize">
              {isNoise ? 'Background' : track.type}
            </p>
          </div>
        </div>

        {/* Control buttons */}
        <div className="flex items-center gap-2">
          {/* Set as main (only for speakers) */}
          {isSpeaker && (
            <button
              onClick={() => setMainSpeaker(track.id)}
              className={`
                p-2 rounded-lg transition-all duration-200
                ${track.isMain 
                  ? 'bg-emerald-500/20 text-emerald-400' 
                  : 'hover:bg-zinc-800 text-zinc-500 hover:text-emerald-400'
                }
              `}
              title="Set as main speaker"
            >
              <Star className="w-4 h-4" fill={track.isMain ? 'currentColor' : 'none'} />
            </button>
          )}

          {/* Solo */}
          <button
            onClick={() => toggleTrackSolo(track.id)}
            className={`
              p-2 rounded-lg transition-all duration-200
              ${track.solo 
                ? 'bg-amber-500/20 text-amber-400' 
                : 'hover:bg-zinc-800 text-zinc-500 hover:text-amber-400'
              }
            `}
            title="Solo"
          >
            <Headphones className="w-4 h-4" />
          </button>

          {/* Mute */}
          <button
            onClick={() => toggleTrackMute(track.id)}
            className={`
              p-2 rounded-lg transition-all duration-200
              ${track.muted 
                ? 'bg-red-500/20 text-red-400' 
                : 'hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300'
              }
            `}
            title={track.muted ? 'Unmute' : 'Mute'}
          >
            {track.muted ? (
              <VolumeX className="w-4 h-4" />
            ) : (
              <Volume2 className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Waveform */}
      <div className="h-16 mb-4 bg-zinc-800/50 rounded-xl overflow-hidden">
        <canvas
          ref={waveformRef}
          className="w-full h-full"
          style={{ display: 'block' }}
        />
      </div>

      {/* Volume slider */}
      <div className="flex items-center gap-3">
        <Volume2 className="w-4 h-4 text-zinc-500" />
        <input
          type="range"
          min="0"
          max="200"
          value={track.volume * 100}
          onChange={(e) => setTrackVolume(track.id, parseInt(e.target.value) / 100)}
          className="flex-1 h-2 bg-zinc-800 rounded-full appearance-none cursor-pointer
            [&::-webkit-slider-thumb]:appearance-none
            [&::-webkit-slider-thumb]:w-4
            [&::-webkit-slider-thumb]:h-4
            [&::-webkit-slider-thumb]:rounded-full
            [&::-webkit-slider-thumb]:bg-zinc-200
            [&::-webkit-slider-thumb]:cursor-pointer
            [&::-webkit-slider-thumb]:transition-transform
            [&::-webkit-slider-thumb]:hover:scale-110
          "
          style={{
            background: `linear-gradient(to right, ${track.color} 0%, ${track.color} ${track.volume * 50}%, #27272a ${track.volume * 50}%, #27272a 100%)`
          }}
        />
        <span className="text-xs text-zinc-500 w-12 text-right font-mono">
          {Math.round(track.volume * 100)}%
        </span>
      </div>

      {/* Segments indicator (for speakers) */}
      {isSpeaker && track.segments && track.segments.length > 0 && (
        <div className="mt-3 pt-3 border-t border-zinc-800">
          <p className="text-xs text-zinc-500">
            {track.segments.length} segment{track.segments.length !== 1 ? 's' : ''} • 
            {' '}{formatDuration(getTotalDuration(track.segments))}
          </p>
        </div>
      )}
    </div>
  );
}

function getTotalDuration(segments: { start: number; end: number }[]): number {
  return segments.reduce((acc, seg) => acc + (seg.end - seg.start), 0);
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
