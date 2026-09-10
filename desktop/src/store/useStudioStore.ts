import { create } from 'zustand'
import { VoiceItem, SynthesisResult, OutputHistoryItem } from '@/types'

interface StudioState {
  selectedModel: string
  selectedVoice: VoiceItem | null
  textPrompt: string
  isSynthesizing: boolean
  progressStep: string
  currentResult: SynthesisResult | null
  history: OutputHistoryItem[]

  setSelectedModel: (modelId: string) => void
  setSelectedVoice: (voice: VoiceItem | null) => void
  setTextPrompt: (prompt: string) => void
  setIsSynthesizing: (status: boolean) => void
  setProgressStep: (step: string) => void
  setCurrentResult: (result: SynthesisResult | null) => void
  setHistory: (history: OutputHistoryItem[]) => void
  addToHistory: (item: OutputHistoryItem) => void
}

export const useStudioStore = create<StudioState>((set) => ({
  selectedModel: 'f5tts',
  selectedVoice: null,
  textPrompt: 'Hello world! Welcome to TTS Studio. All neural zero-shot voice cloning models are running locally with CUDA GPU acceleration.',
  isSynthesizing: false,
  progressStep: '',
  currentResult: null,
  history: [],

  setSelectedModel: (modelId) => set({ selectedModel: modelId }),
  setSelectedVoice: (voice) => set({ selectedVoice: voice }),
  setTextPrompt: (prompt) => set({ textPrompt: prompt }),
  setIsSynthesizing: (status) => set({ isSynthesizing: status }),
  setProgressStep: (step) => set({ progressStep: step }),
  setCurrentResult: (result) => set({ currentResult: result }),
  setHistory: (history) => set({ history }),
  addToHistory: (item) => set((state) => ({ history: [item, ...state.history.slice(0, 19)] })),
}))
