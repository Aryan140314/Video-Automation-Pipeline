"""
TTS Studio Hardware Detector Module
====================================
Discovers GPU hardware, evaluates VRAM availability, audits NVIDIA driver compatibility,
and determines recommended execution device (CUDA vs CPU).
"""

import os
import subprocess
import torch
import psutil

def get_nvidia_driver_version() -> str | None:
    """Queries nvidia-smi for installed driver version."""
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=True
        )
        version_str = res.stdout.strip()
        return version_str if version_str else None
    except Exception:
        return None

def inspect_hardware() -> dict:
    """
    Collects full system hardware diagnostics and returns a standardized report.
    """
    gpu_available = torch.cuda.is_available()
    device_name = "System CPU"
    vram_total_gb = 0.0
    vram_allocated_gb = 0.0
    vram_reserved_gb = 0.0
    vram_free_gb = 0.0
    
    if gpu_available:
        try:
            device_name = torch.cuda.get_device_name(0)
            vram_total_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 2)
            vram_allocated_gb = round(torch.cuda.memory_allocated(0) / (1024 ** 3), 2)
            vram_reserved_gb = round(torch.cuda.memory_reserved(0) / (1024 ** 3), 2)
            vram_free_gb = round(vram_total_gb - vram_allocated_gb, 2)
        except Exception:
            gpu_available = False

    driver_version = get_nvidia_driver_version()
    sys_ram = psutil.virtual_memory()
    ram_total_gb = round(sys_ram.total / (1024 ** 3), 2)
    ram_available_gb = round(sys_ram.available / (1024 ** 3), 2)
    
    # Recommendation logic
    if gpu_available and vram_total_gb >= 4.0:
        recommended_device = "CUDA"
        status_message = f"GPU Acceleration Ready ({device_name}, {vram_total_gb} GB VRAM)"
    elif gpu_available:
        recommended_device = "CUDA"
        status_message = f"GPU Accelerated with Low VRAM ({vram_total_gb} GB VRAM)"
    else:
        recommended_device = "CPU"
        status_message = "GPU Not Detected / CPU Mode Active"

    return {
        "gpu_present": gpu_available,
        "cuda_available": gpu_available,
        "device_name": device_name,
        "recommended_device": recommended_device,
        "vram_total_gb": vram_total_gb,
        "vram_allocated_gb": vram_allocated_gb,
        "vram_reserved_gb": vram_reserved_gb,
        "vram_free_gb": vram_free_gb,
        "sys_ram_total_gb": ram_total_gb,
        "sys_ram_available_gb": ram_available_gb,
        "nvidia_driver_version": driver_version or "N/A",
        "cpu_count": psutil.cpu_count(logical=True),
        "status_message": status_message
    }

if __name__ == "__main__":
    import json
    print(json.dumps(inspect_hardware(), indent=2))
