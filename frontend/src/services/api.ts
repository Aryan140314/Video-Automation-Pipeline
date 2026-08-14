const API_BASE = 'http://127.0.0.1:8000/api';

export interface HardwareReport {
  gpu_present: boolean;
  cuda_available: boolean;
  device_name: string;
  recommended_device: string;
  vram_total_gb: number;
  vram_allocated_gb: number;
  vram_reserved_gb: number;
  vram_free_gb: number;
  sys_ram_total_gb: number;
  sys_ram_available_gb: number;
  nvidia_driver_version: string;
  cpu_count: number;
  status_message: string;
}

export interface ModelCardData {
  id: string;
  name: string;
  status: string;
  device: string;
  weights_size_gb: number;
  gpu_supported: boolean;
  cpu_supported: boolean;
  runtime: string;
  description: string;
}

export interface VoiceCardData {
  category: string;
  filename: string;
  relative_path: string;
  duration_sec: number;
  sample_rate: number;
  channels: number;
  bit_depth: number;
  file_size_bytes: number;
  file_size_mb: number;
  format: string;
}

export interface GenerationResult {
  status: string;
  model: string;
  model_name: string;
  backend: string;
  cloning_active: boolean;
  gen_time: number;
  duration: number;
  rtf: number;
  file_size_kb: number;
  output_path: string;
  device: string;
  error?: string;
}

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },

  async getHardware(): Promise<HardwareReport> {
    const res = await fetch(`${API_BASE}/hardware`);
    return res.json();
  },

  async getModels(): Promise<{ count: number; models: ModelCardData[] }> {
    const res = await fetch(`${API_BASE}/models`);
    return res.json();
  },

  async getVoices(): Promise<{ count: number; voices: VoiceCardData[] }> {
    const res = await fetch(`${API_BASE}/voices`);
    return res.json();
  },

  async getCategories(): Promise<{ count: number; categories: string[] }> {
    const res = await fetch(`${API_BASE}/voices/categories`);
    return res.json();
  },

  async generate(payload: {
    text: string;
    model_id: string;
    voice_category?: string;
    pitch?: number;
    speed?: number;
    trim_sec?: number;
  }): Promise<GenerationResult> {
    const res = await fetch(`${API_BASE}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return res.json();
  },

  async getDiagnostics() {
    const res = await fetch(`${API_BASE}/diagnostics`);
    return res.json();
  },

  async verifyModel(modelId: string) {
    const res = await fetch(`${API_BASE}/models/${modelId}/verify`, { method: 'POST' });
    return res.json();
  },

  async testModel(modelId: string, voiceCategory?: string) {
    const res = await fetch(`${API_BASE}/models/${modelId}/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ voice_category: voiceCategory })
    });
    return res.json();
  },

  async unloadModel(modelId: string) {
    const res = await fetch(`${API_BASE}/models/${modelId}/unload`, { method: 'POST' });
    return res.json();
  },

  async deleteModel(modelId: string) {
    const res = await fetch(`${API_BASE}/models/${modelId}`, { method: 'DELETE' });
    return res.json();
  },

  async downloadModel(modelId: string) {
    const res = await fetch(`${API_BASE}/models/${modelId}/download`, { method: 'POST' });
    return res.json();
  },

  async getDownloadProgress(modelId: string) {
    const res = await fetch(`${API_BASE}/models/${modelId}/download/progress`);
    return res.json();
  }
};
