import React, { useEffect } from 'react';
import { useAppStore, PageId } from './store/useAppStore';
import {
  LayoutDashboard,
  Layers,
  Mic,
  Sparkles,
  History,
  BarChart3,
  Activity,
  Settings,
  Download,
  Info,
  Zap,
  HardDrive
} from 'lucide-react';

import { DashboardPage } from './pages/DashboardPage';
import { ModelsPage } from './pages/ModelsPage';
import { VoicesPage } from './pages/VoicesPage';
import { GeneratePage } from './pages/GeneratePage';
import { HistoryPage } from './pages/HistoryPage';
import { BenchmarkPage } from './pages/BenchmarkPage';
import { DiagnosticsPage } from './pages/DiagnosticsPage';
import { SettingsPage } from './pages/SettingsPage';
import { DownloadsPage } from './pages/DownloadsPage';
import { AboutPage } from './pages/AboutPage';

export const App: React.FC = () => {
  const {
    activePage,
    setActivePage,
    hardware,
    fetchHardware,
    fetchModels,
    fetchVoices,
    fetchCategories
  } = useAppStore();

  useEffect(() => {
    fetchHardware();
    fetchModels();
    fetchVoices();
    fetchCategories();
  }, []);

  const navItems: { id: PageId; label: string; icon: React.ReactNode }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'generate', label: 'Generate', icon: <Sparkles className="w-4 h-4" /> },
    { id: 'models', label: 'Models', icon: <Layers className="w-4 h-4" /> },
    { id: 'voices', label: 'Voices', icon: <Mic className="w-4 h-4" /> },
    { id: 'history', label: 'History', icon: <History className="w-4 h-4" /> },
    { id: 'benchmark', label: 'Benchmark', icon: <BarChart3 className="w-4 h-4" /> },
    { id: 'diagnostics', label: 'Diagnostics', icon: <Activity className="w-4 h-4" /> },
    { id: 'downloads', label: 'Downloads', icon: <Download className="w-4 h-4" /> },
    { id: 'settings', label: 'Settings', icon: <Settings className="w-4 h-4" /> },
    { id: 'about', label: 'About', icon: <Info className="w-4 h-4" /> },
  ];

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard': return <DashboardPage />;
      case 'models': return <ModelsPage />;
      case 'voices': return <VoicesPage />;
      case 'generate': return <GeneratePage />;
      case 'history': return <HistoryPage />;
      case 'benchmark': return <BenchmarkPage />;
      case 'diagnostics': return <DiagnosticsPage />;
      case 'settings': return <SettingsPage />;
      case 'downloads': return <DownloadsPage />;
      case 'about': return <AboutPage />;
      default: return <DashboardPage />;
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-gray-100 font-sans">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-surface border-r border-surface-border flex flex-col justify-between p-4 shrink-0">
        <div className="space-y-6">
          {/* Brand Header */}
          <div className="flex items-center space-x-3 px-2 py-1">
            <div className="p-2 bg-indigo-600 rounded-xl shadow-lg shadow-indigo-600/30 text-white">
              <Sparkles className="w-5 h-5 fill-current" />
            </div>
            <div>
              <h1 className="font-heading font-extrabold text-base tracking-wide text-white">TTS STUDIO</h1>
              <span className="text-[10px] text-indigo-400 font-medium tracking-wider uppercase block">Windows Desktop</span>
            </div>
          </div>

          {/* Navigation Menu */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const active = activePage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActivePage(item.id)}
                  className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                    active
                      ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
                  }`}
                >
                  <span className={active ? 'text-white' : 'text-gray-400'}>{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Hardware Status Pill */}
        <div className="bg-surface-border/50 p-3 rounded-xl border border-surface-border text-xs space-y-1">
          <div className="flex items-center justify-between text-gray-400">
            <span className="text-[10px] font-bold uppercase">Device Status</span>
            <Zap className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="font-bold text-white text-xs truncate">
            {hardware ? hardware.recommended_device : 'CUDA'}
          </div>
          <div className="text-[10px] text-gray-400 truncate">
            {hardware ? hardware.device_name : 'Loading hardware...'}
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-14 border-b border-surface-border bg-surface/40 backdrop-blur px-6 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-2 text-xs text-gray-400">
            <span className="capitalize font-semibold text-white">{activePage}</span>
          </div>

          <div className="flex items-center space-x-4 text-xs">
            <div className="flex items-center space-x-1.5 text-gray-400 bg-surface px-3 py-1 rounded-lg border border-surface-border">
              <HardDrive className="w-3.5 h-3.5 text-cyan-400" />
              <span>VRAM: <strong className="text-white">{hardware ? `${hardware.vram_free_gb} GB Free` : '6.0 GB'}</strong></span>
            </div>
          </div>
        </header>

        {/* Dynamic Page Container */}
        <div className="flex-1 overflow-y-auto p-6">
          {renderPage()}
        </div>
      </main>
    </div>
  );
};
