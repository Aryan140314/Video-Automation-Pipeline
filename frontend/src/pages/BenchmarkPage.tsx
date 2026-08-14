import React from 'react';
import { useAppStore } from '../store/useAppStore';
import { BarChart3, Zap, HardDrive, Cpu, Activity } from 'lucide-react';

export const BenchmarkPage: React.FC = () => {
  const { hardware, models } = useAppStore();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-heading text-white flex items-center space-x-2">
          <BarChart3 className="w-6 h-6 text-purple-400" />
          <span>Performance & RTF Benchmarks</span>
        </h1>
        <p className="text-gray-400 text-sm">
          Real-Time Factor (RTF), generation latency, and VRAM memory benchmark profiles.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="glass-card rounded-2xl p-5 space-y-2">
          <div className="flex justify-between text-xs text-gray-400">
            <span>Target Acceleration</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white">{hardware?.recommended_device || 'CUDA'}</div>
          <div className="text-xs text-gray-400">{hardware?.device_name}</div>
        </div>

        <div className="glass-card rounded-2xl p-5 space-y-2">
          <div className="flex justify-between text-xs text-gray-400">
            <span>Total VRAM Allocated</span>
            <HardDrive className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-white">{hardware?.vram_allocated_gb || 0} GB</div>
          <div className="text-xs text-gray-400">Of {hardware?.vram_total_gb || 6} GB Total</div>
        </div>

        <div className="glass-card rounded-2xl p-5 space-y-2">
          <div className="flex justify-between text-xs text-gray-400">
            <span>CPU Cores Available</span>
            <Cpu className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-white">{hardware?.cpu_count || 16} Cores</div>
          <div className="text-xs text-gray-400">{hardware?.sys_ram_total_gb} GB RAM</div>
        </div>
      </div>

      <div className="glass-card rounded-2xl p-6 space-y-4">
        <h3 className="text-base font-bold text-white">Estimated Architecture RTF Profiles</h3>

        <div className="space-y-4 text-xs">
          <div>
            <div className="flex justify-between text-gray-300 mb-1">
              <span>F5-TTS (Flow-Matching DiT on CUDA)</span>
              <span className="font-semibold text-emerald-400">~0.25 - 0.35 RTF</span>
            </div>
            <div className="w-full bg-surface-border rounded-full h-2">
              <div className="bg-emerald-500 h-2 rounded-full" style={{ width: '30%' }}></div>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-gray-300 mb-1">
              <span>Chatterbox Turbo (Diffusion on CUDA)</span>
              <span className="font-semibold text-emerald-400">~0.30 - 0.45 RTF</span>
            </div>
            <div className="w-full bg-surface-border rounded-full h-2">
              <div className="bg-emerald-400 h-2 rounded-full" style={{ width: '40%' }}></div>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-gray-300 mb-1">
              <span>XTTS-v2 (Isolated GPT-2 on CUDA)</span>
              <span className="font-semibold text-amber-400">~0.60 - 0.80 RTF</span>
            </div>
            <div className="w-full bg-surface-border rounded-full h-2">
              <div className="bg-amber-400 h-2 rounded-full" style={{ width: '70%' }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
