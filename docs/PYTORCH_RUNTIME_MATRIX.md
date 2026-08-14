# PyTorch Runtime Matrix & Dependency Isolation Plan

## 1. Overview
PyTorch and CUDA version alignment across 7 distinct neural TTS architectures requires a strict runtime isolation model. Forcing all models into a single global set of dependencies causes breaking version conflicts (e.g. `coqui-ai/TTS` for XTTS-v2 requiring legacy `transformers` and `torchaudio` versions vs `F5-TTS` requiring `transformers>=4.36.0` and modern PyTorch 2.4/2.5).

---

## 2. Matrix Table

| Model Name | Model ID | Python | PyTorch Version | TorchAudio Version | Transformers | CUDA Runtime | GPU Support | CPU Support | Isolation Required |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **F5-TTS** | `f5tts` | 3.10 | 2.4.1+cu121 / 2.5.1 | 2.4.1 / 2.5.1 | $\ge$4.36.0 | CUDA 12.1 | YES | YES | NO (Main Runtime) |
| **Chatterbox Turbo** | `chatterbox` | 3.10 | 2.4.1+cu121 / 2.5.1 | 2.4.1 / 2.5.1 | $\ge$4.36.0 | CUDA 12.1 | YES | YES | NO (Main Runtime) |
| **Fish Speech S2** | `fishspeech` | 3.10 | 2.4.1+cu121 | 2.4.1 | $\ge$4.40.0 | CUDA 12.1 | YES | LIMITED | YES (`.venv_fishspeech`) |
| **OmniVoice** | `omnivoice` | 3.10 | 2.4.1+cu121 | 2.4.1 | $\ge$4.38.0 | CUDA 12.1 | YES | YES | YES (`.venv_omnivoice`) |
| **CosyVoice 3** | `cosyvoice` | 3.10 | 2.3.1+cu121 | 2.3.1 | $\ge$4.36.0 | CUDA 12.1 | YES | YES | YES (`.venv_cosyvoice`) |
| **XTTS-v2** | `xttsv2` | 3.10 | 2.1.2+cu118 / 2.2.0 | 2.1.2 / 2.2.0 | 4.35.2 | CUDA 11.8 / 12.1 | YES | YES | YES (`.venv_xtts`) |
| **IndexTTS2** | `indextts2` | 3.10 | 2.4.1+cu121 | 2.4.1 | $\ge$4.38.0 | CUDA 12.1 | YES | YES | YES (`.venv_indextts`) |

---

## 3. Isolation Architecture & Subprocess Communication
- Main Runtime Environment: `.venv` handles F5-TTS, Chatterbox Turbo, backend API, diagnostics, audio post-processing, and UI IPC.
- Isolated Environments: Managed dynamically in `runtimes/<model_id>/` (or `%LOCALAPPDATA%\TTS-Studio\runtimes\<model_id>\`).
- Execution Bridge: The main runtime spawns isolated subprocess calls (e.g. `isolated_xtts_runner.py`), passing arguments via JSON/CLI and capturing JSON stdout for performance telemetry.
- Zero Pollution: Updating or changing dependencies for one model will never break the primary backend runtime.
