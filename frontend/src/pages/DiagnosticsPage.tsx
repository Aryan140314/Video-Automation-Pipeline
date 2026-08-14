import React, { useEffect, useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Activity, ShieldAlert, Cpu, HardDrive, Zap, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export const DiagnosticsPage: React.FC = () => {
  const { hardware, fetchHardware } = useAppStore();
  const [diagData, setDiagData] = useState<any>(null);

  const refreshDiag = async () => {
    await fetchHardware();
    try {
      const res = await api.getDiagnostics();
      setDiagData(res);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    refreshDiag();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold font-heading text-white flex items-center space-x-2">
            <Activity className="w-6 h-6 text-indigo-400" />
            <span>System Diagnostics & Hardware Audit</span>
          </h1>
          <p className="text-gray-400 text-sm">
            Live telemetry of GPU CUDA status, VRAM consumption, NVIDIA driver alignment, and system paths.
          </p>
        </div>
        <button
          onClick={refreshDiag}
          className="px-4 py-2 bg-indigo-600/80 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl flex items-center space-x-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Audit</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Hardware Status Card */}
        <div className="glass-card rounded-2xl p-5 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <Zap className="w-4 h-4 text-amber-400" />
            <span>Compute & Acceleration Status</span>
          </h3>

          <div className="space-y-3 text-xs text-gray-300">
            <div className="flex justify-between p-2 bg-surface/80 rounded-lg">
              <span className="text-gray-400">GPU Device Name:</span>
              <span className="font-semibold text-white">{hardware?.device_name || 'System CPU'}</span>
            </div>
            <div className="flex justify-between p-2 bg-surface/80 rounded-lg">
              <span className="text-gray-400">CUDA Acceleration:</span>
              <span className={hardware?.cuda_available ? 'font-semibold text-emerald-400' : 'font-semibold text-rose-400'}>
                {hardware?.cuda_available ? 'ACTIVE' : 'INACTIVE'}
              </span>
            </div>
            <div className="flex justify-between p-2 bg-surface/80 rounded-lg">
              <span className="text-gray-400">NVIDIA Driver Version:</span>
              <span className="font-semibold text-white">{hardware?.nvidia_driver_version || 'N/A'}</span>
            </div>
            <div className="flex justify-between p-2 bg-surface/80 rounded-lg">
              <span className="text-gray-400">Recommended Device:</span>
              <span className="font-semibold text-indigo-400 uppercase">{hardware?.recommended_device}</span>
            </div>
            <div className="flex justify-between p-2 bg-surface/80 rounded-lg">
              <span className="text-gray-400">Total System RAM:</span>
              <span className="font-semibold text-white">{hardware?.sys_ram_total_gb} GB</span>
            </div>
            <div className="flex justify-between p-2 bg-surface/80 rounded-lg">
              <span className="text-gray-400">CPU Core Count:</span>
              <span className="font-semibold text-white">{hardware?.cpu_count} Logical Threads</span>
            </div>
          </div>
        </div>

        {/* Path & Version Diagnostics Card */}
        <div className="glass-card rounded-2xl p-5 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <HardDrive className="w-4 h-4 text-cyan-400" />
            <span>Environment & Path Resolution</span>
          </h3>

          {diagData ? (
            <div className="space-y-3 text-xs text-gray-300">
              <div className="flex justify-between p-2 bg-surface/80 rounded-lg">
                <span className="text-gray-400">Python Version:</span>
                <span className="font-semibold text-white">{diagData.python_version}</span>
              </div>
              <div className="flex justify-between p-2 bg-surface/80 rounded-lg">
                <span className="text-gray-400">PyTorch Version:</span>
                <span className="font-semibold text-emerald-400">{diagData.torch_version}</span>
              </div>
              <div className="p-2 bg-surface/80 rounded-lg space-y-1">
                <span className="text-gray-400 block">Base Storage Path:</span>
                <span className="font-mono text-[11px] text-gray-200 block truncate">{diagData.base_dir}</span>
              </div>
              <div className="p-2 bg-surface/80 rounded-lg space-y-1">
                <span className="text-gray-400 block">Outputs Directory:</span>
                <span className="font-mono text-[11px] text-gray-200 block truncate">{diagData.outputs_dir}</span>
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-500">Loading diagnostic details...</p>
          )}
        </div>
      </div>
    </div>
  );
};
