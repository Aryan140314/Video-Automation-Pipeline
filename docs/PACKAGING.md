# Production Packaging Architecture & Clean Machine Deployment Protocol

## 1. Overview
This document specifies the official production packaging architecture, standalone binary generation, installer build instructions, and clean machine testing protocols for **TTS Studio**.

The production application compiles into a single installer: `TTS Studio Setup.exe`.

The end user does **NOT** need to pre-install Python, Node.js, Git, PyTorch, CUDA SDK, cuDNN, or C++ Build Tools.

---

## 2. Packaging Architecture Breakdown

```mermaid
graph TD
    subgraph Development Environment (e:\TTS)
        DevVenv[.venv Python 3.10]
        DevSrc[scripts / backend / voices / configs]
        DevFrontend[frontend/ UI Source]
    end

    subgraph Step 1: PyInstaller Compilation
        PyInstaller[pyinstaller.spec]
        BackendDist[dist / backend_dist / tts_studio_backend.exe]
    end

    subgraph Step 2: Vite Production Build
        ViteBuild[npm run build in frontend/]
        FrontendDist[frontend / dist /]
    end

    subgraph Step 3: Electron Builder Packaging
        ElectronBuilder[electron-builder.json]
        Installer[dist / installer / TTS Studio Setup.exe]
    end

    subgraph User Target Machine (%LOCALAPPDATA%\TTS-Studio\)
        UserStorage[models / runtimes / outputs / cache / logs]
    end

    DevSrc --> PyInstaller
    PyInstaller --> BackendDist
    DevFrontend --> ViteBuild
    ViteBuild --> FrontendDist
    BackendDist --> ElectronBuilder
    FrontendDist --> ElectronBuilder
    ElectronBuilder --> Installer
    Installer -->|On Demand Model Downloads| UserStorage
```

---

## 3. Exclusion Rules (Zero Pollution Policy)
The installer binary explicitly excludes:
- Developer virtual environment (`.venv`).
- Pip download cache and temporary files.
- HuggingFace local model download cache (`.venv/hf_cache`).
- Multi-gigabyte model weights binaries (`.safetensors`, `.pt`, `.ckpt`, `.pth`).

> [!IMPORTANT]
> Model weights are downloaded strictly on demand by the application's Model Manager to `%LOCALAPPDATA%\TTS-Studio\models\`.

---

## 4. Build Instructions

### Method A: Modern React + Vite Desktop Suite (`desktop/`)
```powershell
# 1. Install dependencies
cd e:\TTS\desktop
npm install

# 2. Build React assets & Electron bundle
npm run build

# 3. Build Production Windows Installer
npm run electron:build
```
Output Installer Path: `e:\TTS\desktop\release\TTS Studio Setup 1.0.0.exe`

---

### Method B: Classic Packaging Workflow (`frontend/` + PyInstaller)
```powershell
# 1. Build Front-End React Assets
cd e:\TTS\frontend
npm run build

# 2. Package Standalone Backend Executable
cd e:\TTS
.\.venv\Scripts\python.exe -m PyInstaller pyinstaller.spec

# 3. Package Windows Desktop Installer
cd e:\TTS
npx electron-builder --config electron-builder.json
```
Output Installer Path: `e:\TTS\dist\installer\TTS Studio Setup.exe`

---

## 5. 15-Point Clean Machine Verification Protocol (Master Specification Section 34)

When testing `TTS Studio Setup.exe` on a clean Windows machine without Python, Node, Git, or PyTorch installed:

1. **Installer Execution**: `TTS Studio Setup.exe` launches without administrative privilege prompts.
2. **Application Startup**: Electron desktop UI opens to the Dashboard in dark mode glassmorphism theme.
3. **Hardware Discovery**: Automatically probes hardware, detecting NVIDIA GPU (RTX 3060 / CUDA) or defaulting to CPU.
4. **FastAPI Backend Probe**: Backend process starts automatically in background on port `8000`.
5. **Model Manager Display**: Displays all 7 target model cards with correct statuses (`READY`, `NOT_INSTALLED`, `DEPENDENCY_MISSING`).
6. **Model Verification**: Clicking "Verify" on F5-TTS / Chatterbox checks file integrity.
7. **Official Model Download**: Triggering model download pulls weights from official HuggingFace repository to `%LOCALAPPDATA%\TTS-Studio\models\`.
8. **Resumable Download**: Network interruption pauses download without restarting multi-GB transfer from zero.
9. **Smoke Test**: Running mini smoke test validates model initialization.
10. **Voice Catalog Display**: Displays all 7 original zero-shot voice categories (`Announcement`, `Audiobook`, `Narration`, `Podcast`, `Presentation`, `Social Media`, `Storytelling`).
11. **Voice Preview Streaming**: Clicking Play on a reference voice streams the WAV audio file cleanly.
12. **Speech Synthesis**: Inputting text up to 2000 words and clicking "Generate Speech" produces high-quality WAV speech.
13. **GPU / CPU Acceleration**: Generation executes on CUDA (GPU) when present, or CPU fallback without crashing.
14. **Audio Telemetry**: Reports accurate generation time, duration, Real-Time Factor (RTF), file size, and device.
15. **Uninstallation Safety**: Uninstalling `TTS Studio` removes application binaries but preserves downloaded multi-GB model weights under `%LOCALAPPDATA%\TTS-Studio\models\` unless explicitly selected for removal.
