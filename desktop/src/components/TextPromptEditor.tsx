import React from 'react'
import { FileText, Sparkles, Trash2 } from 'lucide-react'
import { useStudioStore } from '@/store/useStudioStore'

const PRESETS = [
  "Hello world! Welcome to TTS Studio. All neural voice cloning models are running locally with CUDA GPU acceleration.",
  "In a world powered by artificial intelligence, real-time voice cloning brings narratives and stories vividly to life.",
  "Attention passengers, the express train to the central terminal is now boarding on platform four.",
  "Welcome back to the podcast. Today, we dive deep into the next generation of local machine learning models."
]

export const TextPromptEditor: React.FC = () => {
  const { textPrompt, setTextPrompt, isSynthesizing } = useStudioStore()

  const wordCount = textPrompt.trim() ? textPrompt.trim().split(/\s+/).length : 0
  const charCount = textPrompt.length

  return (
    <div className="glass-panel p-5 rounded-2xl space-y-3.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white">Input Text Prompt</h2>
            <p className="text-[11px] text-slate-400">Type or paste text to synthesize into spoken audio</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700/60">
            {wordCount} words
          </span>
          <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700/60">
            {charCount} chars
          </span>
        </div>
      </div>

      <div className="relative">
        <textarea
          rows={5}
          value={textPrompt}
          onChange={(e) => setTextPrompt(e.target.value)}
          disabled={isSynthesizing}
          placeholder="Enter text to synthesize into speech..."
          className="w-full bg-slate-950/70 border border-slate-800 rounded-xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 transition-all resize-none font-sans leading-relaxed disabled:opacity-50"
        />

        {textPrompt && !isSynthesizing && (
          <button
            onClick={() => setTextPrompt('')}
            title="Clear prompt"
            className="absolute bottom-3 right-3 p-1.5 rounded-lg bg-slate-800/80 text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Preset Quick Buttons */}
      <div className="space-y-1.5">
        <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
          <Sparkles className="w-3 h-3 text-indigo-400" />
          <span>Quick Inspiration Presets:</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {PRESETS.map((preset, idx) => (
            <button
              key={idx}
              disabled={isSynthesizing}
              onClick={() => setTextPrompt(preset)}
              className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-all text-left truncate max-w-[280px]"
            >
              "{preset.slice(0, 38)}..."
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
