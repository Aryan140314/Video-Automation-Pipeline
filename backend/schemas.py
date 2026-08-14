"""
Pydantic API Schemas for TTS Studio Backend
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "TTS Studio Local Backend"
    version: str = "1.0.0"

class HardwareReport(BaseModel):
    gpu_present: bool
    cuda_available: bool
    device_name: str
    recommended_device: str
    vram_total_gb: float
    vram_allocated_gb: float
    vram_reserved_gb: float
    vram_free_gb: float
    sys_ram_total_gb: float
    sys_ram_available_gb: float
    nvidia_driver_version: str
    cpu_count: int
    status_message: str

class ModelCard(BaseModel):
    id: str
    name: str
    status: str  # READY, DEPENDENCY_MISSING, NOT_INSTALLED, MODEL_LOAD_FAILED, DOWNLOADING
    device: str
    weights_size_gb: float
    gpu_supported: bool
    cpu_supported: bool
    runtime: str
    description: str

class ModelsListResponse(BaseModel):
    count: int
    models: List[ModelCard]

class VoiceCard(BaseModel):
    category: str
    filename: str
    relative_path: str
    duration_sec: float = 0.0
    sample_rate: int = 0
    channels: int = 0
    bit_depth: int = 16
    file_size_bytes: int
    file_size_mb: float = 0.0
    format: str = "WAV (PCM)"

class VoicesListResponse(BaseModel):
    count: int
    voices: List[VoiceCard]

class CategoriesListResponse(BaseModel):
    count: int
    categories: List[str]

class GenerationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Input text to synthesize")
    model_id: str = Field(default="f5tts", description="Target model slot ID")
    voice_category: Optional[str] = Field(default=None, description="Voice category from voices/ (e.g. Announcement, Narration)")
    output_path: Optional[str] = Field(default=None, description="Custom output WAV filepath")
    pitch: Optional[float] = Field(default=0.0, description="Pitch shift in semitones (-12 to +12)")
    speed: Optional[float] = Field(default=1.0, description="Speech speed multiplier (0.5 to 2.0)")
    trim_sec: Optional[float] = Field(default=None, description="Maximum duration trim in seconds")

class GenerationResponse(BaseModel):
    status: str = "success"
    model: str
    model_name: str
    backend: str
    cloning_active: bool
    gen_time: float
    duration: float
    rtf: float
    file_size_kb: float
    output_path: str
    device: str
    error: Optional[str] = None

class DiagnosticsResponse(BaseModel):
    hardware: HardwareReport
    models: List[ModelCard]
    voice_count: int
    base_dir: str
    outputs_dir: str
    python_version: str
    torch_version: str

class ModelVerificationResponse(BaseModel):
    model_id: str
    valid: bool
    reason: str

class SmokeTestRequest(BaseModel):
    voice_category: Optional[str] = None

class SmokeTestResponse(BaseModel):
    model_id: str
    success: bool
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ModelUnloadResponse(BaseModel):
    model_id: str
    status: str = "unloaded"
    vram_freed: bool = True

class ModelDeleteResponse(BaseModel):
    model_id: str
    status: str = "deleted"
