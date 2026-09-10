import React from 'react'
import { Activity, Cpu, Sparkles, WifiOff } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { fetchHardwareInfo } from '@/api/ttsApi'

export const Header: React.FC = () => {
  const { data: hw, isError } = useQuery({
    queryKey: ['hardware'],
    queryFn: fetchHardwareInfo,
    refetchInterval: 10000,
  })

  return (
    <header className="border-b border-slate-800 bg-studio-900/80 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between shadow-lg">
      <div className="flex items-center gap-3.5">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/25">
          <Sparkles className="w-5 h-5 text-white animate-pulse" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
              TTS Studio
            </h1>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Desktop Pro
            </span>
          </div>
          <p className="text-xs text-slate-400">Zero-Shot Neural Voice Cloning & Synthesis</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Offline Badge */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
          <WifiOff className="w-3.5 h-3.5" />
          <span>100% Offline Local</span>
        </div>

        {/* Hardware / CUDA Badge */}
        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-200">
          <Cpu className="w-4 h-4 text-indigo-400" />
          {hw ? (
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-100">{hw.device_name}</span>
              {hw.cuda_available && (
                <span className="px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 text-[10px] font-mono font-bold">
                  CUDA {hw.vram_total_gb}GB
                </span>
              )}
            </div>
          ) : isError ? (
            <span className="text-amber-400">Local Engine Booting...</span>
          ) : (
            <span className="flex items-center gap-1.5 text-slate-400">
              <Activity className="w-3 h-3 animate-spin text-indigo-400" /> Detecting GPU...
            </span>
          )}
        </div>
      </div>
    </header>
  )
}
