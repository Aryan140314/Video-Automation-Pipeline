# System Requirements Specification

## 1. Operating System
- **Supported OS**: Windows 10 (64-bit) / Windows 11 (64-bit)
- **Architecture**: x86_64 (amd64)

## 2. Hardware Tiering Specifications

### Minimum Requirements (CPU Mode)
- **CPU**: Intel Core i5 (8th Gen+) or AMD Ryzen 5 (2000 Series+)
- **System RAM**: 16 GB DDR4
- **Graphics / Display**: Integrated GPU or basic display card
- **Storage Space**: 15 GB free NVMe / SATA SSD space
- **Device Support**: Standard SAPI5, gTTS, CPU-mode neural inference for supported models (F5-TTS, Chatterbox, XTTS-v2).

### Recommended Requirements (GPU Acceleration)
- **CPU**: Intel Core i7 / i9 (10th Gen+) or AMD Ryzen 7 / 9 (3000 Series+)
- **System RAM**: 32 GB DDR4 / DDR5
- **NVIDIA GPU**: NVIDIA GeForce RTX 3060 (6 GB VRAM) or higher (RTX 3080/4070/4090 recommended)
- **Dedicated VRAM**: Minimum 6 GB VRAM (8 GB+ recommended for large models like Fish Speech S2 / CosyVoice 3)
- **NVIDIA Driver**: Driver version **470.82+** or **535.xx+** / **595.xx+** (CUDA 12.x driver runtime compatible)
- **Storage Space**: 35 GB free NVMe SSD space (for all 7 model weights & isolated runtimes)

---

## 3. Dependency-Free Packaging Guarantee
The end-user application installer (`TTS Studio Setup.exe`) is self-contained. The user does **NOT** need to pre-install:
- Global Python
- `pip` or virtual environments
- Node.js or `npm`
- Visual Studio or C++ Build Tools
- Git
- CUDA Toolkit SDK (nvcc)
- cuDNN libraries manually
