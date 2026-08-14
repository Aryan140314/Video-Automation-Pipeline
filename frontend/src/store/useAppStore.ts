import { create } from 'zustand';
import { HardwareReport, ModelCardData, VoiceCardData, GenerationResult, api } from '../services/api';

export type PageId =
  | 'dashboard'
  | 'models'
  | 'voices'
  | 'generate'
  | 'history'
  | 'benchmark'
  | 'diagnostics'
  | 'settings'
  | 'downloads'
  | 'about';

interface AppState {
  activePage: PageId;
  setActivePage: (page: PageId) => void;

  hardware: HardwareReport | null;
  models: ModelCardData[];
  voices: VoiceCardData[];
  categories: string[];
  history: GenerationResult[];
  
  loadingHardware: boolean;
  loadingModels: boolean;
  loadingVoices: boolean;
  generating: boolean;

  fetchHardware: () => Promise<void>;
  fetchModels: () => Promise<void>;
  fetchVoices: () => Promise<void>;
  fetchCategories: () => Promise<void>;
  addHistory: (item: GenerationResult) => void;
  setGenerating: (val: boolean) => void;
}

const DEFAULT_MODELS: ModelCardData[] = [
  { id: 'f5tts', name: 'F5-TTS', status: 'READY', device: 'CUDA', weights_size_gb: 1.28, gpu_supported: true, cpu_supported: true, runtime: 'main', description: 'Flow-matching zero-shot voice cloning model' },
  { id: 'chatterbox', name: 'Chatterbox Turbo', status: 'READY', device: 'CUDA', weights_size_gb: 1.1, gpu_supported: true, cpu_supported: true, runtime: 'main', description: 'Diffusion-based zero-shot voice cloning model' },
  { id: 'fishspeech', name: 'Fish Speech S2', status: 'READY', device: 'CUDA', weights_size_gb: 2.5, gpu_supported: true, cpu_supported: true, runtime: 'isolated', description: 'Dual LLM + VQ-GAN zero-shot voice cloning engine' },
  { id: 'omnivoice', name: 'OmniVoice', status: 'READY', device: 'CUDA', weights_size_gb: 1.5, gpu_supported: true, cpu_supported: true, runtime: 'isolated', description: 'Transducer flow-matching speech synthesis model' },
  { id: 'cosyvoice', name: 'CosyVoice 3', status: 'READY', device: 'CUDA', weights_size_gb: 2.2, gpu_supported: true, cpu_supported: true, runtime: 'isolated', description: 'FunAudioLLM zero-shot multilingual synthesis engine' },
  { id: 'xttsv2', name: 'XTTS-v2', status: 'READY', device: 'CUDA', weights_size_gb: 1.8, gpu_supported: true, cpu_supported: true, runtime: 'isolated', description: 'Coqui GPT-2 zero-shot multi-speaker cloning backend' },
  { id: 'indextts2', name: 'IndexTTS 2.5', status: 'READY', device: 'CUDA', weights_size_gb: 2.0, gpu_supported: true, cpu_supported: true, runtime: 'isolated', description: 'IndexTTS multi-emotion zero-shot synthesis model' }
];

const DEFAULT_VOICES: VoiceCardData[] = [
  { category: 'Narration', filename: 'deep_male_narrator.wav', relative_path: 'Narration/deep_male_narrator.wav', duration_sec: 12.4, sample_rate: 24000, channels: 1, bit_depth: 16, file_size_bytes: 595200, file_size_mb: 0.57, format: 'wav' },
  { category: 'Announcement', filename: 'clear_airport_announcer.wav', relative_path: 'Announcement/clear_airport_announcer.wav', duration_sec: 8.2, sample_rate: 24000, channels: 1, bit_depth: 16, file_size_bytes: 393600, file_size_mb: 0.38, format: 'wav' },
  { category: 'Audiobook', filename: 'warm_storyteller.wav', relative_path: 'Audiobook/warm_storyteller.wav', duration_sec: 15.1, sample_rate: 24000, channels: 1, bit_depth: 16, file_size_bytes: 724800, file_size_mb: 0.69, format: 'wav' },
  { category: 'Podcast', filename: 'conversational_host.wav', relative_path: 'Podcast/conversational_host.wav', duration_sec: 10.5, sample_rate: 24000, channels: 1, bit_depth: 16, file_size_bytes: 504000, file_size_mb: 0.48, format: 'wav' },
  { category: 'Presentation', filename: 'executive_speaker.wav', relative_path: 'Presentation/executive_speaker.wav', duration_sec: 11.8, sample_rate: 24000, channels: 1, bit_depth: 16, file_size_bytes: 566400, file_size_mb: 0.54, format: 'wav' },
  { category: 'Social Media', filename: 'energetic_creator.wav', relative_path: 'Social Media/energetic_creator.wav', duration_sec: 9.3, sample_rate: 24000, channels: 1, bit_depth: 16, file_size_bytes: 446400, file_size_mb: 0.43, format: 'wav' },
  { category: 'Storytelling', filename: 'expressive_narrator.wav', relative_path: 'Storytelling/expressive_narrator.wav', duration_sec: 14.2, sample_rate: 24000, channels: 1, bit_depth: 16, file_size_bytes: 681600, file_size_mb: 0.65, format: 'wav' }
];

export const useAppStore = create<AppState>((set, get) => ({
  activePage: 'dashboard',
  setActivePage: (page) => set({ activePage: page }),

  hardware: null,
  models: DEFAULT_MODELS,
  voices: DEFAULT_VOICES,
  categories: ['Narration', 'Announcement', 'Audiobook', 'Podcast', 'Presentation', 'Social Media', 'Storytelling'],
  history: [],

  loadingHardware: false,
  loadingModels: false,
  loadingVoices: false,
  generating: false,

  fetchHardware: async () => {
    set({ loadingHardware: true });
    try {
      const data = await api.getHardware();
      set({ hardware: data, loadingHardware: false });
    } catch (e) {
      console.error('Failed to fetch hardware:', e);
      set({ loadingHardware: false });
    }
  },

  fetchModels: async () => {
    set({ loadingModels: true });
    try {
      const data = await api.getModels();
      if (data && data.models && data.models.length > 0) {
        set({ models: data.models, loadingModels: false });
      } else {
        set({ loadingModels: false });
      }
    } catch (e) {
      console.error('Failed to fetch models, keeping default catalog:', e);
      set({ loadingModels: false });
    }
  },

  fetchVoices: async () => {
    set({ loadingVoices: true });
    try {
      const data = await api.getVoices();
      if (data && data.voices && data.voices.length > 0) {
        set({ voices: data.voices, loadingVoices: false });
      } else {
        set({ loadingVoices: false });
      }
    } catch (e) {
      console.error('Failed to fetch voices, keeping default catalog:', e);
      set({ loadingVoices: false });
    }
  },

  fetchCategories: async () => {
    try {
      const data = await api.getCategories();
      if (data && data.categories && data.categories.length > 0) {
        set({ categories: data.categories });
      }
    } catch (e) {
      console.error('Failed to fetch categories:', e);
    }
  },

  addHistory: (item) => set((state) => ({ history: [item, ...state.history] })),
  setGenerating: (val) => set({ generating: val })
}));
