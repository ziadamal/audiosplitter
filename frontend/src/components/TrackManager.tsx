import React from 'react';
import { Users, Radio, SlidersHorizontal, RotateCcw } from 'lucide-react';
import { useStore } from '../stores/useStore';
import { TrackItem } from './TrackItem';

export function TrackManager() {
  const { 
    tracks, 
    result,
    mainSpeakerBoostDb,
    noiseReductionLevel,
    setMainSpeakerBoostDb,
    setNoiseReductionLevel,
    setTracks,
  } = useStore();

  if (!result || tracks.length === 0) {
    return null;
  }

  const speakerTracks = tracks.filter(t => t.type === 'speaker');
  const noiseTracks = tracks.filter(t => t.type === 'noise' || t.type === 'other');

  const resetAllTracks = () => {
    setTracks(tracks.map((track, index) => ({
      ...track,
      muted: false,
      solo: false,
      volume: 1.0,
      isMain: index === 0 && track.type === 'speaker',
    })));
    setMainSpeakerBoostDb(3.0);
    setNoiseReductionLevel(0);
  };

  return (
    <div className="space-y-8">
      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon={<Users className="w-5 h-5 text-blue-400" />}
          label="Speakers"
          value={result.speaker_count.toString()}
        />
        <StatCard
          icon={<Radio className="w-5 h-5 text-amber-400" />}
          label="Total Tracks"
          value={tracks.length.toString()}
        />
        <StatCard
          icon={<SlidersHorizontal className="w-5 h-5 text-emerald-400" />}
          label="Duration"
          value={formatDuration(result.duration_seconds)}
        />
        <button
          onClick={resetAllTracks}
          className="bg-zinc-900/80 backdrop-blur-sm border border-zinc-800 rounded-xl p-4 
            flex items-center gap-3 hover:border-zinc-700 transition-all group"
        >
          <div className="p-2 rounded-lg bg-zinc-800 group-hover:bg-zinc-700 transition-colors">
            <RotateCcw className="w-5 h-5 text-zinc-400 group-hover:text-zinc-300" />
          </div>
          <span className="text-zinc-400 group-hover:text-zinc-300 font-medium">Reset All</span>
        </button>
      </div>

      {/* Global mix settings */}
      <div className="bg-zinc-900/80 backdrop-blur-sm border border-zinc-800 rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-zinc-200 mb-4 flex items-center gap-2">
          <SlidersHorizontal className="w-5 h-5 text-amber-400" />
          Mix Settings
        </h3>
        
        <div className="grid md:grid-cols-2 gap-6">
          {/* Main speaker boost */}
          <div>
            <label className="block text-sm text-zinc-400 mb-2">
              Main Speaker Boost
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="0"
                max="10"
                step="0.5"
                value={mainSpeakerBoostDb}
                onChange={(e) => setMainSpeakerBoostDb(parseFloat(e.target.value))}
                className="flex-1 h-2 bg-zinc-800 rounded-full appearance-none cursor-pointer
                  [&::-webkit-slider-thumb]:appearance-none
                  [&::-webkit-slider-thumb]:w-4
                  [&::-webkit-slider-thumb]:h-4
                  [&::-webkit-slider-thumb]:rounded-full
                  [&::-webkit-slider-thumb]:bg-emerald-400
                  [&::-webkit-slider-thumb]:cursor-pointer
                "
              />
              <span className="text-sm text-zinc-300 font-mono w-16">
                +{mainSpeakerBoostDb.toFixed(1)} dB
              </span>
            </div>
          </div>

          {/* Noise reduction */}
          <div>
            <label className="block text-sm text-zinc-400 mb-2">
              Noise Reduction
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="0"
                max="100"
                value={noiseReductionLevel * 100}
                onChange={(e) => setNoiseReductionLevel(parseInt(e.target.value) / 100)}
                className="flex-1 h-2 bg-zinc-800 rounded-full appearance-none cursor-pointer
                  [&::-webkit-slider-thumb]:appearance-none
                  [&::-webkit-slider-thumb]:w-4
                  [&::-webkit-slider-thumb]:h-4
                  [&::-webkit-slider-thumb]:rounded-full
                  [&::-webkit-slider-thumb]:bg-amber-400
                  [&::-webkit-slider-thumb]:cursor-pointer
                "
              />
              <span className="text-sm text-zinc-300 font-mono w-16">
                {Math.round(noiseReductionLevel * 100)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Speaker tracks */}
      {speakerTracks.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-zinc-200 mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-400" />
            Speakers ({speakerTracks.length})
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            {speakerTracks.map(track => (
              <TrackItem key={track.id} track={track} />
            ))}
          </div>
        </div>
      )}

      {/* Noise tracks */}
      {noiseTracks.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-zinc-200 mb-4 flex items-center gap-2">
            <Radio className="w-5 h-5 text-zinc-400" />
            Background / Noise
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            {noiseTracks.map(track => (
              <TrackItem key={track.id} track={track} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="bg-zinc-900/80 backdrop-blur-sm border border-zinc-800 rounded-xl p-4">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-zinc-800">
          {icon}
        </div>
        <div>
          <p className="text-xs text-zinc-500">{label}</p>
          <p className="text-lg font-semibold text-zinc-200">{value}</p>
        </div>
      </div>
    </div>
  );
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
