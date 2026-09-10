import { HardwareInfo, ModelInfo, VoicesResponse, SynthesisResult, OutputHistoryItem } from '@/types'

const API_BASE = 'http://127.0.0.1:8000'

export const fetchHardwareInfo = async (): Promise<HardwareInfo> => {
  const res = await fetch(`${API_BASE}/api/hardware`)
  if (!res.ok) throw new Error('Failed to fetch hardware status')
  return res.json()
}

export const fetchModels = async (): Promise<{ models: ModelInfo[] }> => {
  const res = await fetch(`${API_BASE}/api/models`)
  if (!res.ok) throw new Error('Failed to fetch models')
  return res.json()
}

export const downloadModelWeights = async (modelId: string): Promise<{ status: string }> => {
  const res = await fetch(`${API_BASE}/api/models/download`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_id: modelId }),
  })
  if (!res.ok) throw new Error('Failed to trigger model download')
  return res.json()
}

export const fetchDownloadProgress = async (modelId: string) => {
  const res = await fetch(`${API_BASE}/api/models/download-progress?model_id=${modelId}`)
  if (!res.ok) throw new Error('Failed to fetch download progress')
  return res.json()
}

export const fetchVoices = async (): Promise<VoicesResponse> => {
  const res = await fetch(`${API_BASE}/api/voices`)
  if (!res.ok) throw new Error('Failed to fetch voices')
  return res.json()
}

export const fetchOutputHistory = async (): Promise<{ outputs: OutputHistoryItem[] }> => {
  const res = await fetch(`${API_BASE}/api/outputs`)
  if (!res.ok) throw new Error('Failed to fetch output history')
  return res.json()
}

export const synthesizeSpeech = async (payload: {
  model_id: string
  text: string
  reference_voice?: string | null
}): Promise<SynthesisResult> => {
  const res = await fetch(`${API_BASE}/api/synthesize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw new Error(errorData.error || 'Speech synthesis failed.')
  }
  return res.json()
}

export const getAudioStreamUrl = (fullPath: string) => {
  return `${API_BASE}/api/audio-file?path=${encodeURIComponent(fullPath)}`
}
