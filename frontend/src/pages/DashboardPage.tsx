import React from 'react';
import { useAppStore } from '../store/useAppStore';
import { Cpu, HardDrive, Zap, Mic, Sparkles, Activity, Layers, Play } from 'lucide-react';
import { motion } from 'framer-motion';

export const DashboardPage: React.FC = () => {
  const { hardware, models, voices, setActivePage } = useAppStore();

  const activeModelsCount = models.filter((m) => m.status === 'READY').length;

  return (
    <div className="space-y-6">
      {/* Hero Welcome Banner */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card rounded-2xl p-6 relative overflow-hidden bg-gradient-to-r from-indigo-900/40 via-purple-900/30 to-surface border border-indigo-500/20"
      >
        <div className="relative z-10 space-y-2">
          <div className="flex items-center space-x-2 text-indigo-400 font-semibold text-sm">
            <Sparkles className="w-4 h-4 animate-pulse" />
            <span>TTS STUDIO — PRODUCTION SUITE</span>
          </div>
          <h1 className="text-3xl font-bold font-heading text-white">
            High-Performance Neural Text-to-Speech
          </h1>
          <p className="text-gray-400 max-w-2xl text-sm">
            Standalone zero-shot voice cloning app running on local hardware acceleration (NVIDIA CUDA & CPU). No cloud dependencies required.
          </p>
          <div className="pt-2 flex items-center space-x-3">
            <button
              onClick={() => setActivePage('generate')}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm rounded-xl shadow-lg shadow-indigo-600/30 flex items-center space-x-2 transition-all"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Start Synthesizing</span>
            </button>
            <button
              onClick={() => setActivePage('models')}
              className="px-5 py-2.5 bg-surface border border-surface-border hover:bg-gray-800 text-gray-300 font-medium text-sm rounded-xl transition-all"
            >
              <span>Manage Models</span>
            </button>
          </div>
        </div>
      </motion.div>

      {/* Quick Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-4 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-gray-400">
            <span className="text-xs uppercase font-semibold">Active Device</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-xl font-bold text-white">
            {hardware ? hardware.recommended_device : 'CUDA / CPU'}
          </div>
          <div className="text-xs text-gray-400 truncate">
            {hardware ? hardware.device_name : 'Detecting hardware...'}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="glass-card p-4 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-gray-400">
            <span className="text-xs uppercase font-semibold">Available VRAM</span>
            <HardDrive className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-xl font-bold text-white">
            {hardware ? `${hardware.vram_free_gb} GB / ${hardware.vram_total_gb} GB` : '0 GB'}
          </div>
          <div className="text-xs text-gray-400">
            {hardware?.gpu_present ? 'NVIDIA RTX Acceleration' : 'System CPU Mode'}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-4 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-gray-400">
            <span className="text-xs uppercase font-semibold">Models Ready</span>
            <Layers className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-xl font-bold text-white">
            {activeModelsCount} / {models.length || 7}
          </div>
          <div className="text-xs text-emerald-400">
            F5-TTS & Chatterbox Installed
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="glass-card p-4 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-gray-400">
            <span className="text-xs uppercase font-semibold">Voice Assets</span>
            <Mic className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-white">
            {voices.length || 7} Reference WAVs
          </div>
          <div className="text-xs text-gray-400">
            7 Original Voice Categories
          </div>
        </motion.div>
      </div>

      {/* Models Status Summary */}
      <div className="glass-card rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold font-heading text-white flex items-center space-x-2">
            <Activity className="w-5 h-5 text-indigo-400" />
            <span>Target Neural Models Overview</span>
          </h2>
          <button
            onClick={() => setActivePage('models')}
            className="text-xs text-indigo-400 hover:underline font-medium"
          >
            View All Models $\rightarrow$
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {models.slice(0, 6).map((m) => (
            <div key={m.id} className="glass-card p-4 rounded-xl space-y-2 border border-surface-border">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-white">{m.name}</span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                    m.status === 'READY'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  }`}
                >
                  {m.status}
                </span>
              </div>
              <p className="text-xs text-gray-400 line-clamp-2">{m.description}</p>
              <div className="text-[11px] text-gray-500 flex justify-between pt-1">
                <span>Weights: {m.weights_size_gb} GB</span>
                <span>{m.runtime}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
