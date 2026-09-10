import React from 'react'
import { Header } from '@/components/Header'
import { ModelSelector } from '@/components/ModelSelector'
import { VoicePicker } from '@/components/VoicePicker'
import { TextPromptEditor } from '@/components/TextPromptEditor'
import { SynthesisController } from '@/components/SynthesisController'
import { WaveformPlayer } from '@/components/WaveformPlayer'
import { OutputGallery } from '@/components/OutputGallery'

export const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-studio-900 text-slate-100 flex flex-col">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* Model Selection Header Section */}
        <ModelSelector />

        {/* Studio Workspace Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Voice Picker & History (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            <VoicePicker />
            <OutputGallery />
          </div>

          {/* Right Column: Text Prompt, Synthesis Action & Audio Player (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            <TextPromptEditor />
            <SynthesisController />
            <WaveformPlayer />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-studio-900/60 py-3 text-center text-xs text-slate-500 font-mono">
        TTS Studio Desktop App • 100% Local Neural Zero-Shot Speech Engines • Offline Ready
      </footer>
    </div>
  )
}

export default App
