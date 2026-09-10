import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, FileAudio, FolderOpen, History, Music, Pause, Play } from 'lucide-react'
import { fetchOutputHistory, getAudioStreamUrl } from '@/api/ttsApi'
import { OutputHistoryItem } from '@/types'

export const OutputGallery: React.FC = () => {
  const [playingItem, setPlayingItem] = useState<string | null>(null)
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['outputs'],
    queryFn: fetchOutputHistory,
  })

  const handlePlayToggle = (item: OutputHistoryItem) => {
    if (playingItem === item.filename) {
      currentAudio?.pause()
      setPlayingItem(null)
    } else {
      if (currentAudio) {
        currentAudio.pause()
      }
      const streamUrl = getAudioStreamUrl(item.fullPath)
      const audio = new Audio(streamUrl)
      setCurrentAudio(audio)
      setPlayingItem(item.filename)
      audio.play().catch(() => {})
      audio.onended = () => setPlayingItem(null)
    }
  }

  const handleDownload = (item: OutputHistoryItem) => {
    const streamUrl = getAudioStreamUrl(item.fullPath)
    const a = document.createElement('a')
    a.href = streamUrl
    a.download = item.filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  const items = data?.outputs || []

  return (
    <div className="glass-panel p-5 rounded-2xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
            <History className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white">Recent Generated Outputs</h2>
            <p className="text-[11px] text-slate-400">Library of local audio generations</p>
          </div>
        </div>

        <span className="text-xs font-mono text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700/60">
          {items.length} files
        </span>
      </div>

      {isLoading ? (
        <div className="h-28 flex items-center justify-center text-slate-500 text-xs">
          Loading history...
        </div>
      ) : items.length === 0 ? (
        <div className="h-28 flex flex-col items-center justify-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
          <Music className="w-6 h-6 mb-1.5 opacity-40 text-slate-400" />
          <span>No generated speech outputs yet.</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 max-h-60 overflow-y-auto pr-1">
          {items.map((item) => {
            const isPlaying = playingItem === item.filename

            return (
              <div
                key={item.filename}
                className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 flex items-center justify-between gap-3 transition-all"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <button
                    onClick={() => handlePlayToggle(item)}
                    className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-all ${
                      isPlaying
                        ? 'bg-indigo-500 text-white animate-pulse shadow-md'
                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
                    }`}
                  >
                    {isPlaying ? <Pause className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current ml-0.5" />}
                  </button>

                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-slate-200 truncate" title={item.filename}>
                      {item.filename}
                    </p>
                    <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono">
                      <span>{item.createdAt}</span>
                      {item.duration > 0 && <span>• {item.duration}s</span>}
                      <span>• {item.fileSizeKb} KB</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => handleDownload(item)}
                  title="Download WAV"
                  className="p-1.5 rounded-lg bg-slate-800/80 text-slate-400 hover:text-indigo-300 hover:bg-slate-800 transition-colors flex-shrink-0"
                >
                  <Download className="w-3.5 h-3.5" />
                </button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
