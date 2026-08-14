import React from 'react';
import { useAppStore } from '../store/useAppStore';
import { History, Play, FileAudio, Clock, HardDrive } from 'lucide-react';

export const HistoryPage: React.FC = () => {
  const { history } = useAppStore();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-heading text-white flex items-center space-x-2">
          <History className="w-6 h-6 text-indigo-400" />
          <span>Synthesis History Log</span>
        </h1>
        <p className="text-gray-400 text-sm">
          Log of generated audio WAV clips from this session.
        </p>
      </div>

      {history.length === 0 ? (
        <div className="glass-card rounded-2xl p-12 text-center text-gray-500 text-sm space-y-3">
          <FileAudio className="w-10 h-10 mx-auto text-gray-600" />
          <p>No audio generation history yet in this session.</p>
        </div>
      ) : (
        <div className="glass-card rounded-2xl overflow-hidden border border-surface-border">
          <table className="w-full text-left text-xs text-gray-300">
            <thead className="bg-surface text-gray-400 uppercase font-semibold text-[10px] border-b border-surface-border">
              <tr>
                <th className="p-4">Model</th>
                <th className="p-4">Backend</th>
                <th className="p-4">Duration</th>
                <th className="p-4">Gen Time</th>
                <th className="p-4">RTF</th>
                <th className="p-4">Device</th>
                <th className="p-4">File Size</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border">
              {history.map((item, idx) => (
                <tr key={idx} className="hover:bg-gray-800/40 transition-colors">
                  <td className="p-4 font-bold text-white">{item.model_name || item.model}</td>
                  <td className="p-4 font-mono text-[11px] text-emerald-400">{item.backend}</td>
                  <td className="p-4">{item.duration}s</td>
                  <td className="p-4">{item.gen_time}s</td>
                  <td className="p-4 text-emerald-400 font-semibold">{item.rtf}</td>
                  <td className="p-4 uppercase text-indigo-400 font-semibold">{item.device}</td>
                  <td className="p-4">{item.file_size_kb} KB</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
