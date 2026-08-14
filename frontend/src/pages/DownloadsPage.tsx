import React, { useState, useEffect } from 'react';
import { Download, CheckCircle2, Trash2, AlertCircle } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

interface DownloadState {
  status: string;
  percent: number;
  speed_mbps: number;
  downloaded_mb?: number;
  total_mb?: number;
  error?: string;
}

export const DownloadsPage: React.FC = () => {
  const { models, fetchModels } = useAppStore();
  const [downloadStates, setDownloadStates] = useState<Record<string, DownloadState>>({});

  useEffect(() => {
    fetchModels();

    const interval = setInterval(async () => {
      for (const m of models) {
        try {
          const prog = await api.getDownloadProgress(m.id);
          if (prog && prog.status && prog.status !== 'idle') {
            setDownloadStates((prev) => ({ ...prev, [m.id]: prog }));
            if (prog.status === 'completed') {
              fetchModels();
            }
          }
        } catch (e) {
          // Silent ignore polling network lag during startup
        }
      }
    }, 1200);

    return () => clearInterval(interval);
  }, [models]);

  const handleDownload = async (modelId: string) => {
    try {
      setDownloadStates((prev) => ({
        ...prev,
        [modelId]: { status: 'downloading', percent: 0, speed_mbps: 0, error: undefined }
      }));
      await api.downloadModel(modelId);
    } catch (e: any) {
      setDownloadStates((prev) => ({
        ...prev,
        [modelId]: { status: 'failed', percent: 0, speed_mbps: 0, error: e.message || 'Download failed' }
      }));
    }
  };

  const handleDelete = async (modelId: string) => {
    if (confirm(`Are you sure you want to delete weights for model '${modelId}'?`)) {
      try {
        await api.deleteModel(modelId);
        setDownloadStates((prev) => ({
          ...prev,
          [modelId]: { status: 'idle', percent: 0, speed_mbps: 0, error: undefined }
        }));
        await fetchModels();
      } catch (e: any) {
        alert(`Failed to delete model weights: ${e.message}`);
      }
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-heading text-white flex items-center space-x-2">
          <Download className="w-6 h-6 text-cyan-400" />
          <span>Resumable Model Downloads Manager</span>
        </h1>
        <p className="text-gray-400 text-sm">
          Download, pause, resume, re-download, and manage large neural model weight binaries from official sources to %LOCALAPPDATA%\TTS-Studio\models\.
        </p>
      </div>

      <div className="space-y-4">
        {models.map((m) => {
          const dl = downloadStates[m.id];
          const isDownloading = dl?.status === 'downloading';
          const isReady = m.status === 'READY';

          return (
            <div key={m.id} className="glass-card rounded-2xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>{m.name}</span>
                    <span className="text-xs text-gray-400 font-mono">({m.id})</span>
                  </h3>
                  <p className="text-xs text-gray-400">{m.description}</p>
                </div>
                <span
                  className={`text-xs font-bold px-3 py-1 rounded-full ${
                    isReady ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                  }`}
                >
                  {isReady ? 'READY ✓' : 'NOT INSTALLED'}
                </span>
              </div>

              {/* Progress Bar if downloading */}
              {isDownloading && (
                <div className="space-y-1.5 pt-1">
                  <div className="flex justify-between text-xs text-gray-300">
                    <span>Downloading weights... ({dl?.percent || 0}%)</span>
                    <span>{dl?.speed_mbps || 0} MB/s</span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-indigo-500 h-full transition-all duration-300"
                      style={{ width: `${dl?.percent || 0}%` }}
                    />
                  </div>
                </div>
              )}

              {dl?.status === 'failed' && dl?.error && (
                <div className="text-xs text-rose-400 flex items-center space-x-1.5 bg-rose-500/10 p-2 rounded-lg">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>Download error: {dl.error}</span>
                </div>
              )}

              <div className="flex items-center justify-between text-xs text-gray-400 pt-2 border-t border-surface-border">
                <span>Expected Size: {m.weights_size_gb} GB</span>

                <div className="flex items-center space-x-2">
                  {isReady && (
                    <button
                      onClick={() => handleDelete(m.id)}
                      className="px-3 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-400 text-xs font-medium rounded-lg transition-colors flex items-center space-x-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>Delete Weights</span>
                    </button>
                  )}

                  <button
                    onClick={() => handleDownload(m.id)}
                    disabled={isDownloading}
                    className={`px-4 py-1.5 text-xs font-medium rounded-lg transition-all flex items-center space-x-1.5 ${
                      isDownloading
                        ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                        : isReady
                        ? 'bg-surface hover:bg-surface-border text-gray-300 border border-surface-border'
                        : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30'
                    }`}
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>{isDownloading ? 'Downloading...' : isReady ? 'Re-Download' : 'Download Weights'}</span>
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
