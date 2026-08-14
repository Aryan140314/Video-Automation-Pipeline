import React, { useState } from 'react';
import { Settings, Save, Check } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [apiPort, setApiPort] = useState<string>('8000');
  const [autoUnload, setAutoUnload] = useState<boolean>(true);
  const [saved, setSaved] = useState<boolean>(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold font-heading text-white flex items-center space-x-2">
          <Settings className="w-6 h-6 text-gray-400" />
          <span>Application Settings</span>
        </h1>
        <p className="text-gray-400 text-sm">
          Configure backend API server port, VRAM management policies, and theme preferences.
        </p>
      </div>

      <div className="glass-card rounded-2xl p-6 space-y-6">
        <div className="space-y-2">
          <label className="text-sm font-semibold text-white">Local Backend API Port</label>
          <input
            type="text"
            value={apiPort}
            onChange={(e) => setApiPort(e.target.value)}
            className="w-full bg-surface border border-surface-border rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500"
          />
          <p className="text-[11px] text-gray-500">FastAPI backend server runs locally on 127.0.0.1:{apiPort}.</p>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-surface-border">
          <div>
            <span className="text-sm font-semibold text-white block">Auto VRAM Cache Clear</span>
            <span className="text-xs text-gray-400">Automatically unloads previous model weights when switching models.</span>
          </div>
          <input
            type="checkbox"
            checked={autoUnload}
            onChange={(e) => setAutoUnload(e.target.checked)}
            className="w-5 h-5 accent-indigo-600 rounded"
          />
        </div>

        <div className="pt-4 flex items-center space-x-3">
          <button
            onClick={handleSave}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs rounded-xl shadow-lg flex items-center space-x-2"
          >
            {saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            <span>{saved ? 'Saved Preferences' : 'Save Settings'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
