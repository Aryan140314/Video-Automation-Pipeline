import React from 'react'
import { motion } from 'framer-motion'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Clock, Cpu, FileAudio, Gauge, Loader2, PlayCircle, Sparkles, Zap } from 'lucide-react'
import { synthesizeSpeech } from '@/api/ttsApi'
import { useStudioStore } from '@/store/useStudioStore'

export const SynthesisController: React.FC = () => {
  const queryClient = useQueryClient()
  const {
    selectedModel,
    selectedVoice,
    textPrompt,
    isSynthesizing,
    setIsSynthesizing,
    currentResult,
    setCurrentResult,
    addToHistory
  } = useStudioStore()

  const mutation = useMutation({
    mutationFn: synthesizeSpeech,
    onMutate: () => {
      setIsSynthesizing(true)
    },
    onSuccess: (data) => {
      setIsSynthesizing(false)
      setCurrentResult(data)
      addToHistory({
        filename: data.filename,
        fullPath: data.output_path,
        createdAt: new Date().toLocaleTimeString(),
        fileSizeKb: data.file_size_kb,
        duration: data.duration,
        audioUrl: data.audioUrl
      })
      queryClient.invalidateQueries({ queryKey: ['outputs'] })
    },
    onError: (err: Error) => {
      setIsSynthesizing(false)
      alert(`Synthesis Error: ${err.message}`)
    }
  })

  const handleGenerate = () => {
    if (!textPrompt.trim()) {
      alert('Please enter a text prompt.')
      return
    }
    mutation.mutate({
      model_id: selectedModel,
      text: textPrompt,
      reference_voice: selectedVoice?.fullPath || null
    })
  }

  return (
    <div className="space-y-4">
      {/* Generate Action Button */}
      <motion.button
        whileHover={{ scale: isSynthesizing ? 1 : 1.01 }}
        whileTap={{ scale: isSynthesizing ? 1 : 0.99 }}
        onClick={handleGenerate}
        disabled={isSynthesizing || !textPrompt.trim()}
        className={`w-full py-4 px-6 rounded-2xl font-bold text-base flex items-center justify-center gap-3 transition-all duration-300 shadow-xl ${
          isSynthesizing
            ? 'bg-slate-800 text-slate-400 border border-slate-700 cursor-wait'
            : 'bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-500 hover:from-indigo-600 hover:via-purple-700 hover:to-pink-600 text-white shadow-indigo-500/25 border border-indigo-400/30'
        }`}
      >
        {isSynthesizing ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
            <span>Synthesizing Voice Waveform on GPU...</span>
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5 animate-pulse" />
            <span>Generate Neural Voice Audio</span>
          </>
        )}
      </motion.button>

      {/* Generation Metric Stats Bar */}
      {currentResult && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-2 sm:grid-cols-5 gap-3"
        >
          {/* 1. Gen Time */}
          <div className="glass-card p-3 rounded-xl text-center border-slate-800">
            <div className="flex items-center justify-center gap-1 text-slate-400 text-[11px] mb-1">
              <Clock className="w-3.5 h-3.5 text-indigo-400" />
              <span>Gen Time</span>
            </div>
            <div className="text-base font-bold text-slate-100 font-mono">
              {currentResult.gen_time}s
            </div>
          </div>

          {/* 2. Audio Duration */}
          <div className="glass-card p-3 rounded-xl text-center border-slate-800">
            <div className="flex items-center justify-center gap-1 text-slate-400 text-[11px] mb-1">
              <PlayCircle className="w-3.5 h-3.5 text-purple-400" />
              <span>Duration</span>
            </div>
            <div className="text-base font-bold text-slate-100 font-mono">
              {currentResult.duration}s
            </div>
          </div>

          {/* 3. Real-Time Factor (RTF) */}
          <div className="glass-card p-3 rounded-xl text-center border-slate-800">
            <div className="flex items-center justify-center gap-1 text-slate-400 text-[11px] mb-1">
              <Gauge className="w-3.5 h-3.5 text-cyan-400" />
              <span>RTF Speed</span>
            </div>
            <div className="text-base font-bold text-slate-100 font-mono">
              {currentResult.rtf}x
            </div>
          </div>

          {/* 4. File Size */}
          <div className="glass-card p-3 rounded-xl text-center border-slate-800">
            <div className="flex items-center justify-center gap-1 text-slate-400 text-[11px] mb-1">
              <FileAudio className="w-3.5 h-3.5 text-emerald-400" />
              <span>Size</span>
            </div>
            <div className="text-base font-bold text-slate-100 font-mono">
              {currentResult.file_size_kb} KB
            </div>
          </div>

          {/* 5. Device */}
          <div className="glass-card p-3 rounded-xl text-center border-slate-800 col-span-2 sm:col-span-1">
            <div className="flex items-center justify-center gap-1 text-slate-400 text-[11px] mb-1">
              <Cpu className="w-3.5 h-3.5 text-pink-400" />
              <span>Device</span>
            </div>
            <div className="text-base font-bold text-slate-100 font-mono">
              {currentResult.device || 'CUDA'}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
