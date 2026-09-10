import React, { useState, useRef, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, Loader2, Mic2, Pause, Play, RefreshCw, UserCheck } from 'lucide-react'
import { fetchVoices, getAudioStreamUrl } from '@/api/ttsApi'
import { useStudioStore } from '@/store/useStudioStore'
import { VoiceItem } from '@/types'

export const VoicePicker: React.FC = () => {
  const queryClient = useQueryClient()
  const { selectedVoice, setSelectedVoice, isSynthesizing } = useStudioStore()
  const [activeCategory, setActiveCategory] = useState<string>('All')
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  // Bug 2.1 fix: use isError + refetchInterval so the component auto-retries
  // every 3s while the backend is still booting, then stops once loaded.
  const { data: voicesData, isLoading, isFetching, isError, refetch } = useQuery({
    queryKey: ['voices'],
    queryFn: fetchVoices,
    // Keep polling every 3s until we have data (backend still booting)
    refetchInterval: (query) => {
      const hasData = query.state.data && query.state.data.voices?.length > 0
      return hasData ? false : 3000
    },
  })

  // Auto-select first voice if none selected
  useEffect(() => {
    if (voicesData?.voices && voicesData.voices.length > 0 && !selectedVoice) {
      setSelectedVoice(voicesData.voices[0])
    }
  }, [voicesData, selectedVoice, setSelectedVoice])

  const categories = voicesData?.categorized ? ['All', ...Object.keys(voicesData.categorized)] : ['All']

  const filteredVoices = voicesData?.voices
    ? activeCategory === 'All'
      ? voicesData.voices
      : voicesData.categorized[activeCategory] || []
    : []

  const handlePlayPreview = (e: React.MouseEvent, voice: VoiceItem) => {
    e.stopPropagation()
    if (playingVoiceId === voice.id) {
      audioRef.current?.pause()
      setPlayingVoiceId(null)
    } else {
      if (audioRef.current) {
        audioRef.current.pause()
      }
      // Bug 2.2/2.3 fix: voice.audioUrl is already properly encoded by the backend.
      // Use it directly for the stream request.
      const streamUrl = `http://127.0.0.1:8000${voice.audioUrl}`
      const audio = new Audio(streamUrl)
      audioRef.current = audio
      audio.play().catch(() => {})
      setPlayingVoiceId(voice.id)
      audio.onended = () => setPlayingVoiceId(null)
    }
  }

  const isBootingUp = (isLoading || isFetching) && !voicesData?.voices?.length

  return (
    <div className="glass-panel p-5 rounded-2xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <Mic2 className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white">Speaker Reference Voice</h2>
            <p className="text-[11px] text-slate-400">Zero-shot voice cloning target sample</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Manual retry button */}
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            title="Refresh voice list"
            className="w-7 h-7 rounded-lg bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700 flex items-center justify-center transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          </button>

          {selectedVoice && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-mono">
              <UserCheck className="w-3.5 h-3.5 text-indigo-400" />
              <span className="truncate max-w-[140px] font-semibold">{selectedVoice.label}</span>
            </div>
          )}
        </div>
      </div>

      {/* Categories Bar */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
              activeCategory === cat
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'bg-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Voice Grid List */}
      {isBootingUp ? (
        /* Bug 2.1 fix: show animated spinner while backend is still booting */
        <div className="h-44 flex flex-col items-center justify-center gap-3 text-slate-500 text-xs">
          <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
          <span>Waiting for backend to start up...</span>
        </div>
      ) : isError && !voicesData ? (
        <div className="h-44 flex flex-col items-center justify-center gap-3 text-slate-500 text-xs">
          <span className="text-amber-400">Could not load voice library</span>
          <button
            onClick={() => refetch()}
            className="px-3 py-1.5 rounded-lg bg-indigo-600/30 border border-indigo-500/30 text-indigo-300 text-xs hover:bg-indigo-600/50 transition-all"
          >
            Retry
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 max-h-56 overflow-y-auto pr-1">
          {filteredVoices.map((voice) => {
            const isSelected = selectedVoice?.id === voice.id
            const isPlaying = playingVoiceId === voice.id

            return (
              <div
                key={voice.id}
                onClick={() => !isSynthesizing && setSelectedVoice(voice)}
                className={`p-2.5 rounded-xl flex items-center justify-between gap-2 border transition-all ${
                  isSelected
                    ? 'border-indigo-500 bg-indigo-950/40 shadow-sm shadow-indigo-500/20'
                    : 'border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-800/60'
                } ${isSynthesizing ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <button
                    onClick={(e) => handlePlayPreview(e, voice)}
                    className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                      isPlaying
                        ? 'bg-indigo-500 text-white shadow-md animate-pulse'
                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
                    }`}
                  >
                    {isPlaying ? <Pause className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current ml-0.5" />}
                  </button>

                  <div className="min-w-0">
                    <p className={`text-xs font-semibold truncate ${isSelected ? 'text-indigo-200' : 'text-slate-200'}`}>
                      {voice.label}
                    </p>
                    <div className="flex items-center gap-1.5 text-[10px] text-slate-400 font-mono">
                      <span>{voice.category}</span>
                      {voice.duration > 0 && <span>• {voice.duration}s</span>}
                    </div>
                  </div>
                </div>

                {isSelected && (
                  <div className="w-4 h-4 rounded-full bg-indigo-500 text-white flex items-center justify-center flex-shrink-0">
                    <Check className="w-2.5 h-2.5 stroke-[3]" />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
