import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Layers, Download, CheckCircle, AlertTriangle, ShieldCheck, Play, Trash2, Cpu, HardDrive } from 'lucide-react';
import { api } from '../services/api';

export const ModelsPage: React.FC = () => {
  const { models, fetchModels } = useAppStore();
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const handleVerify = async (id: string) => {
    setActionMessage(`Verifying ${id}...`);
    try {
      const res = await api.verifyModel(id);
      setActionMessage(res.reason);
      fetchModels();
    } catch (e: any) {
      setActionMessage(`Verification error: ${e.message}`);
    }
  };

  const handleTest = async (id: string) => {
    setActionMessage(`Running mini smoke test for ${id}...`);
    try {
      const res = await api.testModel(id);
      if (res.success) {
        setActionMessage(`Smoke test passed for ${id}!`);
      } else {
        setActionMessage(`Smoke test failed: ${res.error}`);
      }
    } catch (e: any) {
      setActionMessage(`Test error: ${e.message}`);
    }
  };

  const handleUnload = async (id: string) => {
    try {
      await api.unloadModel(id);
      setActionMessage(`VRAM memory freed for ${id}.`);
    } catch (e: any) {
      setActionMessage(`Unload error: ${e.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-heading text-white flex items-center space-x-2">
          <Layers className="w-6 h-6 text-indigo-400" />
          <span>Neural TTS Models Manager</span>
        </h1>
        <p className="text-gray-400 text-sm">
          Overview of all 7 target zero-shot model architectures, weight statuses, runtimes, and isolated execution policies.
        </p>
      </div>

      {actionMessage && (
        <div className="p-3 bg-indigo-950/60 border border-indigo-500/30 rounded-xl text-indigo-300 text-xs flex items-center justify-between">
          <span>{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="text-indigo-400 hover:text-white font-bold">×</button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {models.map((m) => (
          <div key={m.id} className="glass-card rounded-2xl p-5 space-y-4 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white">{m.name}</h3>
                  <span className="text-xs text-indigo-400 font-mono">ID: {m.id}</span>
                </div>
                <span
                  className={`text-xs font-bold px-3 py-1 rounded-full uppercase ${
                    m.status === 'READY'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : m.status === 'DEPENDENCY_MISSING'
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      : 'bg-gray-800 text-gray-400 border border-gray-700'
                  }`}
                >
                  {m.status}
                </span>
              </div>

              <p className="text-xs text-gray-300 leading-relaxed">{m.description}</p>

              <div className="grid grid-cols-2 gap-2 text-xs text-gray-400 bg-surface/60 p-3 rounded-xl border border-surface-border">
                <div>
                  <span className="text-gray-500">Weight Size:</span> <span className="text-white font-medium">{m.weights_size_gb} GB</span>
                </div>
                <div>
                  <span className="text-gray-500">Device:</span> <span className="text-white font-medium">{m.device}</span>
                </div>
                <div>
                  <span className="text-gray-500">GPU Acceleration:</span>{' '}
                  <span className={m.gpu_supported ? 'text-emerald-400 font-medium' : 'text-rose-400 font-medium'}>
                    {m.gpu_supported ? 'Supported' : 'No'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Runtime Target:</span> <span className="text-white font-medium">{m.runtime}</span>
                </div>
              </div>
            </div>

            <div className="pt-2 flex items-center gap-2 flex-wrap">
              <button
                onClick={() => handleVerify(m.id)}
                className="px-3 py-1.5 bg-surface border border-surface-border hover:bg-gray-800 text-gray-300 text-xs rounded-lg flex items-center space-x-1"
              >
                <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
                <span>Verify</span>
              </button>

              <button
                onClick={() => handleTest(m.id)}
                className="px-3 py-1.5 bg-surface border border-surface-border hover:bg-gray-800 text-gray-300 text-xs rounded-lg flex items-center space-x-1"
              >
                <Play className="w-3.5 h-3.5 text-emerald-400" />
                <span>Smoke Test</span>
              </button>

              <button
                onClick={() => handleUnload(m.id)}
                className="px-3 py-1.5 bg-surface border border-surface-border hover:bg-gray-800 text-gray-300 text-xs rounded-lg flex items-center space-x-1"
              >
                <HardDrive className="w-3.5 h-3.5 text-amber-400" />
                <span>Free VRAM</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
