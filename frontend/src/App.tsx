import React from 'react';
import { Waves, Github, Sparkles } from 'lucide-react';
import { useStore } from './stores/useStore';
import { FileUpload } from './components/FileUpload';
import { ProcessingStatus } from './components/ProcessingStatus';
import { TrackManager } from './components/TrackManager';
import { AudioPlayer } from './components/AudioPlayer';
import { useAudioAnalysis } from './hooks/useAudioAnalysis';

function App() {
  const { status, result, reset } = useStore();
  const { cancelAnalysis } = useAudioAnalysis();

  const isProcessing = ['processing', 'separating', 'diarizing'].includes(status);
  const isComplete = status === 'complete' && result !== null;

  const handleStartOver = () => {
    cancelAnalysis();
    reset();
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Ambient background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-radial from-amber-500/5 to-transparent" />
        <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-radial from-orange-500/5 to-transparent" />
      </div>

      {/* Header */}
      <header className="relative border-b border-zinc-900">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20">
                <Waves className="w-6 h-6 text-amber-400" />
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight">
                  <span className="text-amber-400">Vox</span>
                  <span className="text-zinc-200">Split</span>
                </h1>
                <p className="text-xs text-zinc-600">Audio Source Separation</p>
              </div>
            </div>

            {isComplete && (
              <button
                onClick={handleStartOver}
                className="px-4 py-2 text-sm text-zinc-400 hover:text-zinc-200 
                  border border-zinc-800 hover:border-zinc-700 rounded-lg transition-all"
              >
                Start Over
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="relative max-w-6xl mx-auto px-6 py-12">
        {/* Hero section - shown before upload */}
        {!isProcessing && !isComplete && (
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500/10 
              border border-amber-500/20 rounded-full text-amber-400 text-sm mb-6">
              <Sparkles className="w-4 h-4" />
              AI-Powered Audio Separation
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight">
              Separate Speakers &<br />
              <span className="text-amber-400">Remove Background Noise</span>
            </h2>
            <p className="text-lg text-zinc-500 max-w-2xl mx-auto">
              Upload your audio file and let AI detect speakers, separate their voices,
              and extract background noise into individual tracks you can mix and export.
            </p>
          </div>
        )}

        {/* Upload section */}
        {!isProcessing && !isComplete && (
          <div className="max-w-2xl mx-auto mb-12">
            <FileUpload />
          </div>
        )}

        {/* Processing status */}
        {isProcessing && (
          <div className="max-w-2xl mx-auto mb-12">
            <ProcessingStatus />
          </div>
        )}

        {/* Results section */}
        {isComplete && (
          <div className="space-y-8">
            <ProcessingStatus />
            <TrackManager />
            <AudioPlayer />
          </div>
        )}

        {/* Features section - shown before upload */}
        {!isProcessing && !isComplete && (
          <div className="mt-20">
            <h3 className="text-center text-sm text-zinc-500 uppercase tracking-wider mb-8">
              How it works
            </h3>
            <div className="grid md:grid-cols-3 gap-6">
              <FeatureCard
                step="1"
                title="Upload Audio"
                description="Upload any audio file with multiple speakers - podcasts, meetings, interviews, or calls."
              />
              <FeatureCard
                step="2"
                title="AI Analysis"
                description="Our AI separates vocals from noise, then identifies and isolates each unique speaker."
              />
              <FeatureCard
                step="3"
                title="Mix & Export"
                description="Mute unwanted speakers, reduce noise, emphasize the main voice, and export your mix."
              />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="relative border-t border-zinc-900 mt-20">
        <div className="max-w-6xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between text-sm text-zinc-600">
            <p>Built with Demucs, pyannote.audio, React & FastAPI</p>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 hover:text-zinc-400 transition-colors"
            >
              <Github className="w-4 h-4" />
              View on GitHub
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ step, title, description }: { step: string; title: string; description: string }) {
  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6 hover:border-zinc-700 transition-all">
      <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 
        flex items-center justify-center text-amber-400 font-bold mb-4">
        {step}
      </div>
      <h4 className="text-lg font-semibold text-zinc-200 mb-2">{title}</h4>
      <p className="text-zinc-500">{description}</p>
    </div>
  );
}

export default App;
