import React, { useRef, useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Download, Pause, Play, RotateCcw, Volume2, VolumeX } from 'lucide-react'
import { useStudioStore } from '@/store/useStudioStore'
import { getAudioStreamUrl } from '@/api/ttsApi'

export const WaveformPlayer: React.FC = () => {
  const { currentResult } = useStudioStore()
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [isPlaying, setIsPlaying] = useState<boolean>(false)
  const [currentTime, setCurrentTime] = useState<number>(0)
  const [duration, setDuration] = useState<number>(0)
  const [isMuted, setIsMuted] = useState<boolean>(false)

  const audioUrl = currentResult ? getAudioStreamUrl(currentResult.output_path) : ''

  useEffect(() => {
    if (audioRef.current && audioUrl) {
      audioRef.current.load()
      setIsPlaying(false)
      setCurrentTime(0)
    }
  }, [audioUrl])

  if (!currentResult || !audioUrl) return null

  const togglePlay = () => {
    if (!audioRef.current) return
    if (isPlaying) {
      audioRef.current.pause()
      setIsPlaying(false)
    } else {
      audioRef.current.play()
      setIsPlaying(true)
    }
  }

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime)
    }
  }

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration)
    }
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value)
    setCurrentTime(time)
    if (audioRef.current) {
      audioRef.current.currentTime = time
    }
  }

  const handleDownload = () => {
    const a = document.createElement('a')
    a.href = audioUrl
    a.download = currentResult.filename || 'synthesized_speech.wav'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60)
    const s = Math.floor(secs % 60)
    return `${m}:${s < 10 ? '0' : ''}${s}`
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-panel p-5 rounded-2xl space-y-4 border-indigo-500/30 bg-gradient-to-b from-slate-900/90 to-indigo-950/20"
    >
      <audio
        ref={audioRef}
        src={audioUrl}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={() => setIsPlaying(false)}
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <Volume2 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Rendered Voice Audio</h3>
            <p className="text-[11px] text-slate-400 font-mono">{currentResult.filename}</p>
          </div>
        </div>

        <button
          onClick={handleDownload}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/30 hover:bg-indigo-600 text-indigo-200 hover:text-white border border-indigo-500/40 text-xs font-semibold transition-all shadow-md"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Download WAV</span>
        </button>
      </div>

      {/* Animated Sound Wave Bars */}
      <div className="h-12 bg-slate-950/80 rounded-xl p-3 flex items-center justify-between gap-1 border border-slate-800/80 overflow-hidden">
        {Array.from({ length: 48 }).map((_, i) => {
          const height = isPlaying
            ? Math.max(15, Math.sin(i * 0.4 + currentTime * 5) * 80 + 20)
            : 20 + (i % 5) * 6

          return (
            <motion.div
              key={i}
              style={{ height: `${height}%` }}
              className={`w-full rounded-full transition-all duration-75 ${
                isPlaying
                  ? 'bg-gradient-to-t from-indigo-500 to-pink-500'
                  : 'bg-slate-700/60'
              }`}
            />
          )
        })}
      </div>

      {/* Playback Controls & Scrubber */}
      <div className="flex items-center gap-3">
        <button
          onClick={togglePlay}
          className="w-10 h-10 rounded-xl bg-indigo-500 text-white flex items-center justify-center shadow-lg shadow-indigo-500/30 hover:bg-indigo-600 transition-all flex-shrink-0"
        >
          {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
        </button>

        <span className="text-xs font-mono text-slate-400 w-9 text-right">
          {formatTime(currentTime)}
        </span>

        <input
          type="range"
          min={0}
          max={duration || 100}
          step={0.01}
          value={currentTime}
          onChange={handleSeek}
          className="w-full accent-indigo-500 bg-slate-850 h-1.5 rounded-lg cursor-pointer"
        />

        <span className="text-xs font-mono text-slate-400 w-9">
          {formatTime(duration || currentResult.duration)}
        </span>

        <button
          onClick={() => {
            if (audioRef.current) {
              audioRef.current.muted = !isMuted
              setIsMuted(!isMuted)
            }
          }}
          className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg transition-colors"
        >
          {isMuted ? <VolumeX className="w-4 h-4 text-rose-400" /> : <Volume2 className="w-4 h-4" />}
        </button>
      </div>
    </motion.div>
  )
}
