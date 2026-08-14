# GPU / CPU Detection & Hardware Acceleration Architecture

## 1. Overview
TTS Studio features an automated hardware detection engine that discovers system GPUs, evaluates VRAM capacities, inspects NVIDIA driver compatibility, and selects the optimal compute execution device (`CUDA` vs `CPU`).

---

## 2. Hardware Detection Engine
At startup, the backend collects diagnostic metrics:

```python
import torch
import psutil

def detect_hardware_capabilities():
    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else "N/A"
    vram_total = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2) if gpu_available else 0
    vram_allocated = round(torch.cuda.memory_allocated() / (1024**3), 2) if gpu_available else 0
    vram_free = vram_total - vram_allocated if gpu_available else 0
    
    sys_ram_total = round(psutil.virtual_memory().total / (1024**3), 2)
    sys_ram_available = round(psutil.virtual_memory().available / (1024**3), 2)
    
    recommended_device = "CUDA" if (gpu_available and vram_total >= 4.0) else "CPU"
    
    return {
        "gpu_present": gpu_available,
        "gpu_name": gpu_name,
        "vram_total_gb": vram_total,
        "vram_allocated_gb": vram_allocated,
        "vram_free_gb": vram_free,
        "sys_ram_total_gb": sys_ram_total,
        "sys_ram_available_gb": sys_ram_available,
        "recommended_device": recommended_device
    }
```

---

## 3. Execution Device Selection Logic
- **Compatible NVIDIA GPU Present**: Execution automatically uses `cuda`.
- **GPU Incompatible / Driver Outdated**: Displays explicit warning in Diagnostics (`NVIDIA DRIVER UPDATE REQUIRED`) and defaults safely to `cpu`.
- **No NVIDIA GPU**: Executes on `cpu` without crashing or throwing silent errors.

---

## 4. VRAM Management & Sequential Lifecycle
To prevent Out-Of-Memory (OOM) crashes on 6 GB GPUs:
1. **Load**: Model weights loaded into GPU VRAM on demand when requested for inference.
2. **Inference**: Perform zero-shot voice synthesis.
3. **Unload**: When switching active models or when idle, call `torch.cuda.empty_cache()` to free VRAM for subsequent requests.
