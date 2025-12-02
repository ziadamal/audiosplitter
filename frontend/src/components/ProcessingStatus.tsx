import React from 'react';
import { Loader2, CheckCircle2, XCircle, Waves, Users, Sparkles } from 'lucide-react';
import { useStore } from '../stores/useStore';
import type { ProcessingStatus } from '../types';

const statusConfig: Record<ProcessingStatus, {
  icon: React.ReactNode;
  label: string;
  color: string;
}> = {
  pending: {
    icon: <Loader2 className="w-5 h-5 animate-spin" />,
    label: 'Preparing',
    color: 'text-zinc-400',
  },
  processing: {
    icon: <Loader2 className="w-5 h-5 animate-spin" />,
    label: 'Processing',
    color: 'text-amber-400',
  },
  separating: {
    icon: <Waves className="w-5 h-5 animate-pulse" />,
    label: 'Separating Audio',
    color: 'text-blue-400',
  },
  diarizing: {
    icon: <Users className="w-5 h-5 animate-pulse" />,
    label: 'Detecting Speakers',
    color: 'text-purple-400',
  },
  complete: {
    icon: <CheckCircle2 className="w-5 h-5" />,
    label: 'Complete',
    color: 'text-emerald-400',
  },
  failed: {
    icon: <XCircle className="w-5 h-5" />,
    label: 'Failed',
    color: 'text-red-400',
  },
};

export function ProcessingStatus() {
  const { status, progress, currentStep, uploadedFile, error } = useStore();
  const config = statusConfig[status];

  if (!uploadedFile || status === 'pending') {
    return null;
  }

  return (
    <div className="w-full">
      <div className="bg-zinc-900/80 backdrop-blur-sm border border-zinc-800 rounded-2xl p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-xl bg-zinc-800 ${config.color}`}>
              {config.icon}
            </div>
            <div>
              <h3 className="font-semibold text-zinc-200">{config.label}</h3>
              <p className="text-sm text-zinc-500">{uploadedFile.name}</p>
            </div>
          </div>
          
          {status !== 'failed' && status !== 'complete' && (
            <span className="text-2xl font-bold text-amber-400">
              {Math.round(progress)}%
            </span>
          )}
        </div>

        {/* Progress bar */}
        {status !== 'complete' && status !== 'failed' && (
          <div className="mb-4">
            <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Current step */}
        {currentStep && status !== 'complete' && status !== 'failed' && (
          <p className="text-sm text-zinc-400 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-400" />
            {currentStep}
          </p>
        )}

        {/* Error message */}
        {error && status === 'failed' && (
          <div className="mt-4 p-4 bg-red-950/30 border border-red-800/30 rounded-xl">
            <p className="text-red-300 text-sm">{error}</p>
          </div>
        )}

        {/* Success message */}
        {status === 'complete' && (
          <div className="mt-4 p-4 bg-emerald-950/30 border border-emerald-800/30 rounded-xl flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <p className="text-emerald-300 text-sm">
              Analysis complete! You can now manage and mix your tracks.
            </p>
          </div>
        )}

        {/* Processing steps visualization */}
        {status !== 'complete' && status !== 'failed' && (
          <div className="mt-6 flex items-center justify-between">
            <ProcessingStep
              label="Upload"
              done={progress > 0}
              active={status === 'processing' && progress < 10}
            />
            <StepConnector active={progress >= 10} />
            <ProcessingStep
              label="Separate"
              done={progress >= 40}
              active={status === 'separating' || (status === 'processing' && progress >= 10 && progress < 40)}
            />
            <StepConnector active={progress >= 40} />
            <ProcessingStep
              label="Diarize"
              done={progress >= 80}
              active={status === 'diarizing' || (status === 'processing' && progress >= 40 && progress < 80)}
            />
            <StepConnector active={progress >= 80} />
            <ProcessingStep
              label="Finalize"
              done={progress === 100}
              active={progress >= 80 && progress < 100}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function ProcessingStep({ label, done, active }: { label: string; done: boolean; active: boolean }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className={`
          w-8 h-8 rounded-full flex items-center justify-center
          transition-all duration-300
          ${done 
            ? 'bg-emerald-500 text-white' 
            : active 
              ? 'bg-amber-500 text-white ring-4 ring-amber-500/20' 
              : 'bg-zinc-800 text-zinc-500'
          }
        `}
      >
        {done ? (
          <CheckCircle2 className="w-4 h-4" />
        ) : active ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <div className="w-2 h-2 rounded-full bg-current" />
        )}
      </div>
      <span className={`text-xs font-medium ${done || active ? 'text-zinc-300' : 'text-zinc-600'}`}>
        {label}
      </span>
    </div>
  );
}

function StepConnector({ active }: { active: boolean }) {
  return (
    <div className="flex-1 h-0.5 mx-2">
      <div
        className={`
          h-full rounded-full transition-all duration-500
          ${active ? 'bg-emerald-500' : 'bg-zinc-800'}
        `}
      />
    </div>
  );
}
