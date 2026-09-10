export interface ModelInfo {
  id: string
  name: string
  architecture: string
  description: string
  maxWords: number
  recommended: boolean
  tag: string
}

export interface VoiceItem {
  id: string
  label: string
  category: string
  filename: string
  duration: number
  fullPath: string
  audioUrl: string
}

export interface VoicesResponse {
  categorized: Record<string, VoiceItem[]>
  voices: VoiceItem[]
  total: number
}

export interface HardwareInfo {
  recommended_device: string
  device_name: string
  vram_total_gb: number
  vram_allocated_gb: number
  vram_free_gb: number
  platform: string
  python_version: string
  torch_version: string
  cuda_available: boolean
}

export interface SynthesisResult {
  model: string
  model_name: string
  backend: string
  cloning_active: boolean
  gen_time: number
  duration: number
  rtf: number
  file_size_kb: number
  output_path: string
  device: string
  audioUrl: string
  filename: string
}

export interface OutputHistoryItem {
  filename: string
  fullPath: string
  createdAt: string
  fileSizeKb: number
  duration: number
  audioUrl: string
}
