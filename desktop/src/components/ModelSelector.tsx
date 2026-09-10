import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Check, Download, Flame, Globe2, Loader2, Radio, Zap } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useStudioStore } from '@/store/useStudioStore'
import { fetchModels, downloadModelWeights, fetchDownloadProgress } from '@/api/ttsApi'
import { ModelInfo } from '@/types'

export const ModelSelector: React.FC = () => {
  const queryClient = useQueryClient()
  const { selectedModel, setSelectedModel, isSynthesizing } = useStudioStore()
  const [downloadingModelId, setDownloadingModelId] = useState<string | null>(null)
  const [downloadPercent, setDownloadPercent] = useState<number>(0)

  const { data: modelsData } = useQuery({
    queryKey: ['models'],
    queryFn: fetchModels,
    refetchInterval: downloadingModelId ? 2000 : 8000,
  })

  // Real download polling loop
  useEffect(() => {
    if (!downloadingModelId) return

    const timer = setInterval(async () => {
      try {
        const prog = await fetchDownloadProgress(downloadingModelId)
        if (prog) {
          setDownloadPercent(prog.percent || 0)
          if (prog.status === 'READY') {
            setDownloadPercent(100)
            setTimeout(() => {
              setDownloadingModelId(null)
              queryClient.invalidateQueries({ queryKey: ['models'] })
            }, 1000)
          } else if (prog.status === 'ERROR') {
            setDownloadingModelId(null)
            alert(`Download Error: ${prog.error || 'Failed to download weights.'}`)
          }
        }
      } catch (err) {
        console.error('Download poll error:', err)
      }
    }, 1200)

    return () => clearInterval(timer)
  }, [downloadingModelId, queryClient])

  const downloadMutation = useMutation({
    mutationFn: downloadModelWeights,
    onMutate: (modelId: string) => {
      setDownloadingModelId(modelId)
      setDownloadPercent(10)
    },
    onError: () => {
      setDownloadingModelId(null)
      alert('Model download request failed. Check server connection.')
    }
  })

  const models: (ModelInfo & { isDownloaded?: boolean })[] = modelsData?.models || [
    {
      id: 'f5tts',
      name: 'F5-TTS',
      architecture: 'DiT Flow Matching',
      description: 'State-of-the-art flow matching zero-shot voice cloning with crisp natural cadence and expressive emotion.',
      maxWords: 60,
      recommended: true,
      tag: 'Highest Fidelity',
      isDownloaded: false
    },
    {
      id: 'chatterbox',
      name: 'Chatterbox Turbo',
      architecture: 'Fast Diffusion',
      description: 'Ultra-fast diffusion zero-shot voice cloning optimized for rapid conversational synthesis.',
      maxWords: 60,
      recommended: false,
      tag: 'Ultra Fast',
      isDownloaded: false
    },
    {
      id: 'xttsv2',
      name: 'XTTS-v2',
      architecture: 'Coqui Multi-Speaker GPT',
      description: 'Robust multi-lingual autoregressive voice cloner with deep expressive pitch and 17+ languages.',
      maxWords: 60,
      recommended: false,
      tag: 'Multilingual',
      isDownloaded: false
    }
  ]

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <Radio className="w-3.5 h-3.5 text-indigo-400" />
          <span>Select Neural TTS Engine</span>
        </label>
        <span className="text-[11px] text-slate-500 font-mono">3 Local Neural Models</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        {models.map((model) => {
          const isSelected = selectedModel === model.id
          const isDownloading = downloadingModelId === model.id
          const isDownloaded = model.isDownloaded !== false

          return (
            <motion.div
              key={model.id}
              whileHover={{ scale: isSynthesizing || isDownloading ? 1 : 1.015 }}
              onClick={() => {
                if (!isSynthesizing && !isDownloading) {
                  setSelectedModel(model.id)
                }
              }}
              className={`text-left p-4 rounded-xl relative overflow-hidden transition-all duration-200 ${
                isSelected
                  ? 'glass-card-active border-indigo-500/80 bg-indigo-950/30'
                  : 'glass-card hover:border-slate-600'
              } ${isSynthesizing || isDownloading ? 'cursor-not-allowed opacity-80' : 'cursor-pointer'}`}
            >
              {/* Active Indicator Glow */}
              {isSelected && (
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500" />
              )}

              <div className="flex items-start justify-between gap-2 mb-2">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-base text-white">{model.name}</h3>
                    {model.id === 'f5tts' && <Flame className="w-4 h-4 text-amber-400" />}
                    {model.id === 'chatterbox' && <Zap className="w-4 h-4 text-cyan-400" />}
                    {model.id === 'xttsv2' && <Globe2 className="w-4 h-4 text-emerald-400" />}
                  </div>
                  <span className="text-[11px] font-mono text-indigo-300/90">{model.architecture}</span>
                </div>

                <div className="flex items-center gap-1.5">
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                    model.id === 'f5tts'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : model.id === 'chatterbox'
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                      : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  }`}>
                    {model.tag}
                  </span>
                  {isSelected && (
                    <div className="w-5 h-5 rounded-full bg-indigo-500 text-white flex items-center justify-center shadow-md">
                      <Check className="w-3 h-3 stroke-[3]" />
                    </div>
                  )}
                </div>
              </div>

              <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed mb-3">
                {model.description}
              </p>

              {/* Download Progress Bar or Status Bar */}
              {isDownloading ? (
                <div className="space-y-1.5 pt-2 border-t border-slate-700/40">
                  <div className="flex items-center justify-between text-[11px] font-mono text-indigo-300">
                    <span className="flex items-center gap-1.5">
                      <Loader2 className="w-3 h-3 animate-spin text-indigo-400" />
                      Downloading weights from HuggingFace...
                    </span>
                    <span>{downloadPercent}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 to-pink-500 transition-all duration-300"
                      style={{ width: `${downloadPercent}%` }}
                    />
                  </div>
                </div>
              ) : !isDownloaded ? (
                <div className="flex items-center justify-between border-t border-slate-700/40 pt-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      downloadMutation.mutate(model.id)
                    }}
                    className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-semibold transition-all shadow-md shadow-indigo-600/30 border border-indigo-400/40"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download Model Weights</span>
                  </button>
                  <span className="text-[11px] text-amber-400 font-mono font-medium">Weights Missing</span>
                </div>
              ) : (
                <div className="flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-700/40 pt-2 font-mono">
                  <span>Safe Chunk: ~{model.maxWords} words</span>
                  <span className="text-emerald-400 flex items-center gap-1 font-semibold">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                    Ready (Offline)
                  </span>
                </div>
              )}
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
