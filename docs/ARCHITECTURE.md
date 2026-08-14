# TTS Studio — Production System Architecture & Design Specification

## 1. Executive Summary
**TTS Studio** is a production-grade Windows desktop application built by combining existing zero-shot TTS logic ([`scripts/tts_adapters.py`](file:///e:/TTS/scripts/tts_adapters.py), [`scripts/speech_synth_helper.py`](file:///e:/TTS/scripts/speech_synth_helper.py)), zero-shot reference voice recordings ([`voices/`](file:///e:/TTS/voices/)), a local FastAPI backend, an Electron + React UI, and a dynamic Model & Runtime Manager with isolated environment support.

The application operates fully standalone without requiring the end-user to manually install Python, Node.js, Git, PyTorch, CUDA, or compiler toolchains.

---

## 2. Master System Architecture Diagram

```mermaid
graph TB
    subgraph Desktop Front-End (Electron / React)
        UI[React + Vite + Tailwind UI]
        Zustand[Zustand State & React Query]
        ElectronMain[Electron Main Process]
    end

    subgraph Local Backend (FastAPI / Python)
        API[FastAPI Server :8000]
        PathResolver[Path Resolver Engine]
        HWDetector[Hardware Detection Engine]
        RuntimeMgr[Runtime Manager Module]
    end

    subgraph TTS Core Logic (Source of Truth)
        Adapters[TTS Model Adapters Registry]
        SynthHelper[Speech Synth Helper]
        VoiceAssets[Original Voice WAV Assets]
    end

    subgraph Environment Runtimes
        MainVenv[Main Runtime Environment .venv]
        XTTSVenv[Isolated Runtime .venv_xtts]
        FishVenv[Isolated Runtime .venv_fishspeech]
    end

    subgraph Production Storage (%LOCALAPPDATA%\TTS-Studio\)
        ModelStore[models / f5tts / chatterbox / ...]
        OutputStore[outputs /]
        CacheStore[cache / logs / config]
    end

    UI -->|HTTP / REST API| API
    ElectronMain -->|Spawns Backend Process| API
    API --> HWDetector
    API --> PathResolver
    API --> RuntimeMgr
    RuntimeMgr --> Adapters
    Adapters --> SynthHelper
    Adapters --> VoiceAssets
    RuntimeMgr -->|Direct Import| MainVenv
    RuntimeMgr -->|Subprocess Runner| XTTSVenv
    RuntimeMgr -->|Subprocess Runner| FishVenv
    Adapters --> ModelStore
    SynthHelper --> OutputStore
```

---

## 3. Dynamic Path Resolution Specification ([`scripts/path_resolver.py`](file:///e:/TTS/scripts/path_resolver.py))

To prevent hardcoded paths (e.g. `e:\TTS`), the application uses dynamic path resolution based on standard Windows environment variables:

- **Development Mode**: Resolves paths relative to the project root (`e:\TTS`).
- **Production Mode**: Resolves paths relative to `%LOCALAPPDATA%\TTS-Studio\`.

```
%LOCALAPPDATA%\TTS-Studio\
├── models\             # Downloaded model weights (F5-TTS, Chatterbox, etc.)
├── runtimes\            # Isolated Python virtual environments
├── voices\             # Zero-shot reference voice assets
├── outputs\            # Generated audio WAV outputs
├── cache\              # HuggingFace & model cache (.venv/hf_cache)
├── logs\               # Application & backend log files
└── config\             # User settings & pronunciation maps
```

---

## 4. Hardware Detection & Acceleration Specification ([`scripts/hardware_detector.py`](file:///e:/TTS/scripts/hardware_detector.py))

At startup, the hardware engine gathers runtime diagnostics:

1. **GPU & CUDA Inspection**:
   - Detects NVIDIA GPU presence via `torch.cuda.is_available()`.
   - Reads GPU model name (`torch.cuda.get_device_name(0)`).
   - Measures allocated, reserved, and total VRAM.
2. **NVIDIA Driver Audit**:
   - Inspects installed driver version (`nvidia-smi` query).
   - If driver version is inadequate for CUDA 12.x execution, flags `NVIDIA DRIVER UPDATE REQUIRED` and defaults safely to `CPU`.
3. **Compute Routing Logic**:
   - **Compatible NVIDIA GPU Present** $\rightarrow$ `DEVICE = CUDA`
   - **GPU Absent or Driver Incompatible** $\rightarrow$ `DEVICE = CPU` (with diagnostic alert)

---

## 5. Local Backend REST API Interface Contracts

The backend exposes a high-performance REST API powered by FastAPI on `http://127.0.0.1:8000`:

| Endpoint | Method | Input Payload | Response Payload | Description |
| :--- | :---: | :--- | :--- | :--- |
| `/api/health` | GET | None | `{"status": "ok", "version": "1.0.0"}` | Backend health probe |
| `/api/hardware` | GET | None | Hardware capability JSON object | Hardware & CUDA diagnostic report |
| `/api/models` | GET | None | List of model status objects | Enumerates all 7 models & installation status |
| `/api/models/{id}/download` | POST | None | Download progress stream / state | Triggers resumable model download |
| `/api/models/{id}/unload` | POST | None | `{"status": "unloaded"}` | Evicts model weights from GPU VRAM |
| `/api/voices` | GET | None | List of voice category objects | Enumerates original reference voice WAVs |
| `/api/generate` | POST | Generation Request JSON | Performance dict + output WAV path | Executes TTS synthesis via target adapter |
| `/api/diagnostics` | GET | None | Comprehensive system state JSON | Full system hardware, VRAM, and logs report |

---

## 6. Runtime Manager & Model Isolation Architecture

The `RuntimeManager` handles the lifecycle of all 7 target TTS models:

1. **Main Environment Models** (`f5tts`, `chatterbox`):
   - Loaded directly inside the primary backend process (`.venv`).
2. **Isolated Environment Models** (`xttsv2`, `fishspeech`, `omnivoice`, `cosyvoice`, `indextts2`):
   - Main process spawns an isolated subprocess using the isolated environment's Python executable (e.g. `runtimes/xtts/Scripts/python.exe`).
   - Invokes an isolated runner script (e.g. [`scripts/isolated_xtts_runner.py`](file:///e:/TTS/scripts/isolated_xtts_runner.py)).
   - Parameters passed via CLI args; performance metrics returned as JSON stdout.

---

## 7. VRAM Lifecycle Strategy (LOAD $\rightarrow$ INFERENCE $\rightarrow$ UNLOAD)

To support GPUs with 6 GB VRAM (such as the RTX 3060 Laptop GPU):
- **Single Active Model**: Only one neural model is retained in GPU VRAM at a time.
- **Auto-Unload**: Switching active models automatically calls `torch.cuda.empty_cache()` and unloads previous model weights from memory.
- **OOM Protection**: If requested generation exceeds available VRAM, the backend returns an `INSUFFICIENT_VRAM` error instead of crashing.
