import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Play, Sparkles, Sliders, Volume2, Mic, Layers, Clock, Zap, Download } from 'lucide-react';
import { api, GenerationResult } from '../services/api';

export const GeneratePage: React.FC = () => {
  const { models, voices, addHistory, setGenerating, generating } = useAppStore();

  const [text, setText] = useState<string>(
    'Welcome to TTS Studio. This production desktop application runs local zero-shot voice cloning with hardware acceleration.'
  );
  const [selectedModel, setSelectedModel] = useState<string>('f5tts');
  const [selectedVoice, setSelectedVoice] = useState<string>('Narration');
  const [pitch, setPitch] = useState<number>(0);
  const [speed, setSpeed] = useState<number>(1.0);
  const [result, setResult] = useState<GenerationResult | null>(null);

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;

  const handleGenerate = async () => {
    if (!text.trim()) return;
    setGenerating(true);
    setResult(null);

    try {
      const res = await api.generate({
        text,
        model_id: selectedModel,
        voice_category: selectedVoice,
        pitch,
        speed
      });

      setResult(res);
      addHistory(res);
      setGenerating(false);
    } catch (e: any) {
      setResult({
        status: 'error',
        model: selectedModel,
        model_name: selectedModel,
        backend: 'none',
        cloning_active: false,
        gen_time: 0,
        duration: 0,
        rtf: 0,
        file_size_kb: 0,
        output_path: '',
        device: 'cpu',
        error: e.message || 'Generation failed'
      });
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-heading text-white flex items-center space-x-2">
          <Sparkles className="w-6 h-6 text-indigo-400" />
          <span>Synthesize Speech</span>
        </h1>
        <p className="text-gray-400 text-sm">
          Select target neural model, zero-shot reference voice, text up to 2,000 words, and voice tuning parameters.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Text & Controls */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass-card rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-semibold text-white">Input Text</label>
              <span className="text-xs text-gray-400">{wordCount} / 2000 words</span>
            </div>

            <textarea
              rows={6}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enter text to synthesize into high-quality human speech..."
              className="w-full bg-surface/80 border border-surface-border rounded-xl p-4 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-all resize-none"
            />

            {/* Controls Bar */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-gray-400 mb-1.5 block">Target Model Architecture</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full bg-surface border border-surface-border rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  {models.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.status})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-400 mb-1.5 block">Zero-Shot Reference Voice</label>
                <select
                  value={selectedVoice}
                  onChange={(e) => setSelectedVoice(e.target.value)}
                  className="w-full bg-surface border border-surface-border rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  {voices.map((v) => (
                    <option key={v.category} value={v.category}>
                      {v.category} ({v.filename})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Voice Tuning Sliders */}
            <div className="pt-2 border-t border-surface-border grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>Speed Stretch</span>
                  <span className="text-white font-medium">{speed}x</span>
                </div>
                <input
                  type="range"
                  min={0.5}
                  max={2.0}
                  step={0.1}
                  value={speed}
                  onChange={(e) => setSpeed(parseFloat(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>Pitch Shift (Semitones)</span>
                  <span className="text-white font-medium">{pitch > 0 ? `+${pitch}` : pitch}</span>
                </div>
                <input
                  type="range"
                  min={-12}
                  max={12}
                  step={1}
                  value={pitch}
                  onChange={(e) => setPitch(parseInt(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>
            </div>

            <button
              onClick={handleGenerate}
              disabled={generating || !text.trim()}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-sm rounded-xl shadow-lg shadow-indigo-600/30 flex items-center justify-center space-x-2 transition-all"
            >
              {generating ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Synthesizing Audio...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Generate Speech</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: Output & Telemetry */}
        <div className="space-y-4">
          <div className="glass-card rounded-2xl p-5 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <Volume2 className="w-4 h-4 text-emerald-400" />
              <span>Audio Output & Telemetry</span>
            </h3>

            {result ? (
              <div className="space-y-4">
                {result.status === 'success' ? (
                  <div className="space-y-3">
                    <div className="p-3 bg-emerald-950/40 border border-emerald-500/30 rounded-xl text-emerald-400 text-xs font-medium flex items-center justify-between">
                      <span>Synthesis Succeeded!</span>
                      <span className="font-mono text-[10px] bg-emerald-500/20 px-2 py-0.5 rounded">{result.backend}</span>
                    </div>

                    <audio
                      controls
                      className="w-full"
                      src={`http://127.0.0.1:8000/api/outputs/audio/${result.output_path.split(/[/\\]/).pop()}`}
                      autoPlay
                    />

                    <div className="space-y-2 text-xs text-gray-300 bg-surface/80 p-3 rounded-xl border border-surface-border">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Generation Time:</span>
                        <span className="font-semibold text-white">{result.gen_time}s</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Audio Duration:</span>
                        <span className="font-semibold text-white">{result.duration}s</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Real-Time Factor (RTF):</span>
                        <span className="font-semibold text-emerald-400">{result.rtf}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Execution Device:</span>
                        <span className="font-semibold text-indigo-400 uppercase">{result.device}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">File Size:</span>
                        <span className="font-semibold text-white">{result.file_size_kb} KB</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 bg-rose-950/40 border border-rose-500/30 rounded-xl text-rose-300 text-xs space-y-2">
                    <div className="font-bold flex items-center space-x-1 text-rose-400">
                      <span>Generation Error</span>
                    </div>
                    <p className="text-gray-300">{result.error}</p>
                    <p className="text-[11px] text-gray-400 pt-1">
                      No Silent Fallback Rule: Selected model must be installed.
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-8 text-center text-gray-500 text-xs space-y-2">
                <Clock className="w-8 h-8 mx-auto text-gray-600" />
                <p>Click "Generate Speech" to synthesize audio.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
