import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Mic, Play, Pause, Music, Info, FileAudio } from 'lucide-react';

export const VoicesPage: React.FC = () => {
  const { voices, setActivePage } = useAppStore();
  const [playingCategory, setPlayingCategory] = useState<string | null>(null);
  const [audioObj, setAudioObj] = useState<HTMLAudioElement | null>(null);

  const handlePlayPreview = (category: string) => {
    if (playingCategory === category && audioObj) {
      audioObj.pause();
      setPlayingCategory(null);
      return;
    }

    if (audioObj) {
      audioObj.pause();
    }

    const newAudio = new Audio(`http://127.0.0.1:8000/api/voices/audio/${encodeURIComponent(category)}`);
    newAudio.play();
    setAudioObj(newAudio);
    setPlayingCategory(category);

    newAudio.onended = () => {
      setPlayingCategory(null);
    };
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-heading text-white flex items-center space-x-2">
          <Mic className="w-6 h-6 text-emerald-400" />
          <span>Zero-Shot Reference Voices Catalog</span>
        </h1>
        <p className="text-gray-400 text-sm">
          Source-of-truth zero-shot reference voice recordings in <code className="text-emerald-400 bg-surface px-1.5 py-0.5 rounded text-xs">voices/</code>. Original PCM WAV files preserved without alteration.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {voices.map((v) => (
          <div key={v.category} className="glass-card glass-card-hover rounded-2xl p-5 space-y-4">
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  {v.category}
                </span>
                <h3 className="text-base font-bold text-white pt-1">{v.filename}</h3>
              </div>
              <button
                onClick={() => handlePlayPreview(v.category)}
                className={`p-3 rounded-full transition-all ${
                  playingCategory === v.category
                    ? 'bg-emerald-500 text-black shadow-lg shadow-emerald-500/40'
                    : 'bg-indigo-600/80 hover:bg-indigo-500 text-white shadow-md'
                }`}
              >
                {playingCategory === v.category ? (
                  <Pause className="w-5 h-5 fill-current" />
                ) : (
                  <Play className="w-5 h-5 fill-current ml-0.5" />
                )}
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs text-gray-400 bg-surface/60 p-3 rounded-xl border border-surface-border">
              <div>
                <span className="text-gray-500">Duration:</span>{' '}
                <span className="text-white font-medium">{v.duration_sec}s</span>
              </div>
              <div>
                <span className="text-gray-500">Sample Rate:</span>{' '}
                <span className="text-white font-medium">{v.sample_rate} Hz</span>
              </div>
              <div>
                <span className="text-gray-500">Channels:</span>{' '}
                <span className="text-white font-medium">{v.channels === 1 ? 'Mono' : 'Stereo'}</span>
              </div>
              <div>
                <span className="text-gray-500">File Size:</span>{' '}
                <span className="text-white font-medium">{v.file_size_mb} MB</span>
              </div>
            </div>

            <div className="pt-1 flex items-center justify-between text-xs">
              <span className="text-gray-500 font-mono text-[11px] truncate max-w-[180px]">{v.relative_path}</span>
              <button
                onClick={() => setActivePage('generate')}
                className="text-indigo-400 hover:text-indigo-300 font-semibold"
              >
                Use Voice $\rightarrow$
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
