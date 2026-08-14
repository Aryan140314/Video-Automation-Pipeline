# Comprehensive Dependency Matrix & Environment Audit

## 1. Baseline Requirements Overview
The desktop application consists of a Core Main Environment (`.venv`) and optional Isolated Model Runtimes.
This document details all Python package dependencies, version bounds, purpose, and installation targets.

---

## 2. Core Main Runtime Requirements (`requirements/core.txt` & `.venv`)

| Package | Version Specifier | Category | Purpose | Installed in `.venv` |
| :--- | :--- | :--- | :--- | :---: |
| `torch` | `>=2.0.0` (2.5.1+cu121) | ML Framework | PyTorch tensor computations & CUDA acceleration | Target Baseline |
| `torchaudio` | `>=2.0.0` (2.5.1+cu121) | Audio ML | Audio signal processing & tensor I/O | Target Baseline |
| `transformers` | `>=4.36.0` | ML Framework | HuggingFace model architectures & tokenizers | Target Baseline |
| `accelerate` | `>=0.25.0` | ML Utilities | Distributed & multi-device PyTorch execution | Target Baseline |
| `huggingface_hub` | `>=0.20.0` | Model Download | Downloads model checkpoints & weights from HF | Target Baseline |
| `soundfile` | `>=0.12.1` | Audio Processing | Audio WAV file export and reading | Target Baseline |
| `librosa` | `>=0.10.1` | Audio Processing | Voice tuning, pitch shifting & speed stretch | Target Baseline |
| `noisereduce` | `>=2.0.0` | Audio Processing | Noise suppression utilities | Target Baseline |
| `DeepFilterNet` | `>=0.5.6` | Audio Processing | Deep learning audio enhancement | Target Baseline |
| `pydub` | `>=0.25.1` | Audio Processing | MP3/WAV conversions & audio manipulation | Target Baseline |
| `scipy` | `>=1.10.0` | Math / Sci | Signal processing math utilities | Target Baseline |
| `numpy` | `>=1.24.0` | Math / Sci | Array math operations | Target Baseline |
| `f5-tts` | `>=0.3.5` | Neural Backend | F5-TTS flow-matching model library | Baseline Model |
| `chatterbox-tts` | `>=0.1.0` | Neural Backend | Chatterbox diffusion model library | Baseline Model |
| `imageio-ffmpeg` | `>=0.4.9` | Media Binaries | Bundled static FFmpeg executable | Dependency |
| `ffmpeg-python` | `>=0.2.0` | Media Utilities | Python wrapper for FFmpeg commands | Dependency |
| `gtts` | `>=2.3.0` | Fallback TTS | Online Google Text-to-Speech fallback | Fallback |
| `pywin32` | `>=306` | Win OS | Windows COM SAPI5 robotic voice fallback | Fallback |
| `fastapi` | `>=0.100.0` | Web Backend | Local REST API server for Electron IPC | Desktop Backend |
| `uvicorn` | `>=0.23.0` | Web Server | ASGI server for FastAPI | Desktop Backend |
| `pydantic-settings` | `>=2.0.0` | Config | Typed application configuration schemas | Backend |
| `httpx` | `>=0.25.0` | Network | Async HTTP client for model download verification | Backend |
| `tqdm` | `>=4.65.0` | Utilities | Progress bars for downloads | Utilities |
| `rich` | `>=13.0.0` | Utilities | Terminal formatting & diagnostics | Utilities |
| `pyyaml` | `>=6.0` | Utilities | YAML configuration parsing | Utilities |
| `psutil` | `>=5.9.0` | Utilities | System RAM, VRAM, and CPU diagnostics | Utilities |

---

## 3. Model Requirements Files Breakdown
To prevent environment pollution, requirements are partitioned in `requirements/`:

```
requirements/
├── core.txt            # Main backend & shared utilities
├── f5tts.txt           # F5-TTS model dependencies
├── chatterbox.txt     # Chatterbox Turbo dependencies
├── fishspeech.txt      # Fish Speech S2 dependencies
├── omnivoice.txt       # OmniVoice dependencies
├── cosyvoice.txt       # CosyVoice 3 dependencies
├── xttsv2.txt          # XTTS-v2 dependencies
└── indextts2.txt       # IndexTTS2 dependencies
```
