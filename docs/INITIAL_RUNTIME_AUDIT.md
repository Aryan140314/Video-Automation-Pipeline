# Initial Development Runtime Audit & Baseline Verification Report

## 1. Executive Summary
This document establishes the official Phase 0 development environment audit and baseline verification for **TTS Studio**. 
A clean, project-local virtual environment (`.venv`) has been initialized on Windows 11 x64 using Python 3.10. Basic packaging utilities (`pip`, `setuptools`, `wheel`, `packaging`) and baseline PyTorch/CUDA dependencies have been verified.

---

## 2. Empirical Python & PyTorch Verification Evidence

```powershell
PS E:\TTS> .\.venv\Scripts\python.exe --version
Python 3.10.11

PS E:\TTS> .\.venv\Scripts\python.exe -m pip --version
pip 26.2.1 from E:\TTS\.venv\lib\site-packages\pip (python 3.10)

PS E:\TTS> .\.venv\Scripts\python.exe -c "import torch; print(torch.__version__)"
2.5.1+cu121

PS E:\TTS> .\.venv\Scripts\python.exe -c "import torch; print(torch.cuda.is_available())"
True

PS E:\TTS> .\.venv\Scripts\python.exe -c "import torch; print(torch.cuda.get_device_name(0))"
NVIDIA GeForce RTX 3060 Laptop GPU
```

---

## 3. Environment Audit Table

| Property | Value / Result | Status |
| :--- | :--- | :---: |
| **System Python** | `C:\Users\aryan\AppData\Local\Programs\Python\Python310\python.exe` | Verified ✓ |
| **Local Virtual Env** | `E:\TTS\.venv` | Active ✓ |
| **Python Version** | `3.10.11` (64-bit) | Compatible ✓ |
| **Pip Version** | `pip 26.2.1` | Upgraded ✓ |
| **PyTorch Version** | `2.5.1+cu121` | Installed ✓ |
| **TorchAudio Version**| `2.5.1+cu121` | Installed ✓ |
| **CUDA Acceleration** | `True` (NVIDIA GeForce RTX 3060 Laptop GPU) | Active ✓ |
| **CUDA Driver** | NVIDIA Driver 595.97 (CUDA 13.2 runtime support) | Modern Driver ✓ |

---

## 4. Hardware Capability Discovery

| Metric | Measured Value | Capability Rating |
| :--- | :--- | :---: |
| **Detected GPU** | NVIDIA GeForce RTX 3060 Laptop GPU | Hardware Acceleration Supported |
| **VRAM Total** | 6.0 GB VRAM | Sufficient for single-model inference |
| **Recommended Device** | `CUDA` (Device 0) | GPU Primary |
| **Fallback Device** | `CPU` | Supported for non-GPU environments |

---

## 5. Source-of-Truth Codebase & Voice Asset Audit

- **TTS Adapters**: [`scripts/tts_adapters.py`](file:///e:/TTS/scripts/tts_adapters.py) (666 lines) verified.
- **Speech Helper**: [`scripts/speech_synth_helper.py`](file:///e:/TTS/scripts/speech_synth_helper.py) (685 lines) verified.
- **Zero-Shot Voice Catalog**: 7 original reference WAV files in [`voices/`](file:///e:/TTS/voices/) cataloged without modification:
  1. `voices/Announcement/ENG_US_M_DaveL.wav` (1.26 MB)
  2. `voices/Audiobook/ENG_US_M_BrianR.wav` (0.55 MB)
  3. `voices/Narration/deep_male_narrator.wav` (0.69 MB)
  4. `voices/Podcast/johnb.wav` (1.26 MB)
  5. `voices/Presentation/ENG_US_M_DCG.wav` (1.26 MB)
  6. `voices/Social Media/FDownload.app-1063976359819594-(320kbps).wav` (1.37 MB)
  7. `voices/Storytelling/dl-090b86a8217d.wav` (0.63 MB)

---

## 6. Model Baseline Integration Audit

| Model ID | Model Name | Architecture / Backend | Runtime Strategy | Baseline Status |
| :--- | :--- | :--- | :--- | :---: |
| `f5tts` | F5-TTS | Flow-Matching DiT (`f5-tts`) | Main `.venv` | **READY** ✓ |
| `chatterbox` | Chatterbox Turbo | Diffusion (`chatterbox-tts`) | Main `.venv` | **READY** ✓ |
| `fishspeech` | Fish Speech S2 | Dual LLM + VQ-GAN (`fish-speech`) | Isolated (`.venv_fishspeech`) | DEPENDENCY_MISSING |
| `omnivoice` | OmniVoice | Transducer / Flow (`omnivoice`) | Isolated (`.venv_omnivoice`) | DEPENDENCY_MISSING |
| `cosyvoice` | CosyVoice 3 | FunAudioLLM (`cosyvoice`) | Isolated (`.venv_cosyvoice`) | DEPENDENCY_MISSING |
| `xttsv2` | XTTS-v2 | Coqui GPT-2 (`TTS==0.22.0`) | Isolated (`.venv_xtts`) | Subprocess Runner Ready |
| `indextts2` | IndexTTS2 | IndexTTS (`indextts`) | Isolated (`.venv_indextts`) | DEPENDENCY_MISSING |

---

## 7. Audit Conclusion
Phase 0 Clean Development Audit is complete. All 11 requirements of Phase 0.1 and Phase 0 have been satisfied and documented.
