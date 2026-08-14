import React from 'react';
import { Info, Sparkles, Layers, Shield, Cpu } from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold font-heading text-white flex items-center space-x-2">
          <Info className="w-6 h-6 text-indigo-400" />
          <span>About TTS Studio</span>
        </h1>
        <p className="text-gray-400 text-sm">
          Standalone Windows Desktop Application for zero-shot neural speech synthesis.
        </p>
      </div>

      <div className="glass-card rounded-2xl p-6 space-y-5">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-indigo-600/20 text-indigo-400 rounded-2xl border border-indigo-500/30">
            <Sparkles className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">TTS Studio</h2>
            <p className="text-xs text-gray-400">Version 1.0.0 (Production Build Baseline)</p>
          </div>
        </div>

        <p className="text-xs text-gray-300 leading-relaxed">
          TTS Studio is engineered to deliver zero-shot voice cloning capabilities on local Windows hardware without requiring cloud APIs, python setup, or command-line execution.
        </p>

        <div className="grid grid-cols-2 gap-4 text-xs">
          <div className="p-3 bg-surface/80 rounded-xl border border-surface-border space-y-1">
            <span className="text-gray-400 font-semibold block">UI Stack</span>
            <span className="text-white block">Electron, Vite, React, TypeScript, Tailwind CSS, Framer Motion, Zustand</span>
          </div>

          <div className="p-3 bg-surface/80 rounded-xl border border-surface-border space-y-1">
            <span className="text-gray-400 font-semibold block">Backend & Engines</span>
            <span className="text-white block">FastAPI, Python 3.10, PyTorch 2.5, F5-TTS, Chatterbox Turbo, XTTS-v2</span>
          </div>
        </div>
      </div>
    </div>
  );
};
