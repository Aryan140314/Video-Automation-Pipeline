# Corrective Master Implementation Audit & Status Report

## 1. Executive Summary & Phase Control Audit
This corrective audit evaluates the state of **TTS Studio** across all completed components, model adapters, runtimes, voice assets, API contracts, packaging scripts, and test suites.

### Workflow & Phase Control Reaffirmation
- **Strict Phase Workflow**: `PHASE` $\rightarrow$ `IMPLEMENT` $\rightarrow$ `TEST` $\rightarrow$ `REPORT` $\rightarrow$ `STOP` $\rightarrow$ `WAIT FOR APPROVAL`.
- **Auto-Progression Disabled**: Automatic progression between phases has been halted. No further development or packaging will occur without explicit user command (`NEXT PHASE`).

---

## 2. Model Implementation Truth Matrix

> [!IMPORTANT]
> Passing structural unit tests does **NOT** constitute proof of real model inference. A model is marked `READY` only if official weights are downloaded, runtime dependencies exist, and a real inference test has successfully generated a WAV file.

| Model ID | Official Model Name | Official Library & Class | Python | PyTorch | TorchAudio | Transformers | CUDA / GPU | Windows Support | Actual Weights Source | Local Weights Status | Real Inference Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: |
| **`f5tts`** | F5-TTS | `f5_tts.api.F5TTS` | 3.10 | 2.5.1+cu121 | 2.5.1+cu121 | 5.15.0 | CUDA + CPU | Supported | HF: `SWAVE-LAB/F5-TTS` | `NOT_DOWNLOADED` | **`NOT_TESTED`** |
| **`chatterbox`** | Chatterbox Turbo | `chatterbox.tts.ChatterboxTTS` | 3.10 | 2.5.1+cu121 | 2.5.1+cu121 | 5.15.0 | CUDA + CPU | Supported | HF: `ResembleAI/chatterbox` | `NOT_DOWNLOADED` | **`NOT_TESTED`** |
| **`fishspeech`** | Fish Speech S2 | `fish_speech.models` | 3.10 | 2.4.1 (req) | 2.4.1 (req) | $\ge$4.40 | CUDA Only | Supported | HF: `fishaudio/fish-speech-1.5` | `NOT_DOWNLOADED` | **`NOT_IMPLEMENTED`** (`DEP_MISSING`) |
| **`omnivoice`** | OmniVoice | `omnivoice` | 3.10 | 2.4.1 (req) | 2.4.1 (req) | $\ge$4.38 | CUDA + CPU | Supported | HF: `k2-fsa/omnivoice` | `NOT_DOWNLOADED` | **`NOT_IMPLEMENTED`** (`DEP_MISSING`) |
| **`cosyvoice`** | CosyVoice 3 | `cosyvoice` | 3.10 | 2.3.1 (req) | 2.3.1 (req) | $\ge$4.36 | CUDA + CPU | Supported | HF: `FunAudioLLM/CosyVoice-300M` | `NOT_DOWNLOADED` | **`NOT_IMPLEMENTED`** (`DEP_MISSING`) |
| **`xttsv2`** | XTTS-v2 | `coqui-ai/TTS` (`TTS==0.22.0`) | 3.10 | 2.1.2 (req) | 2.1.2 (req) | 4.35.2 | CUDA + CPU | Supported | HF: `coqui/XTTS-v2` | `NOT_DOWNLOADED` | **`NOT_IMPLEMENTED`** (`DEP_MISSING`) |
| **`indextts2`** | IndexTTS2 | `indextts` | 3.10 | 2.4.1 (req) | 2.4.1 (req) | $\ge$4.38 | CUDA + CPU | Supported | HF: `IndexTTS/IndexTTS2` | `NOT_DOWNLOADED` | **`NOT_IMPLEMENTED`** (`DEP_MISSING`) |

---

## 3. Model Manager & Distribution Audit

| Model ID | Source Type | Repository ID | Model Files | Tokenizer / Config Files | Weight Size | Installation Method | Verification Method | Local Storage Path |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| **`f5tts`** | Hugging Face | `SWAVE-LAB/F5-TTS` | `model_1200000.safetensors` | `vocab.txt` | 1.28 GB | Resumable HTTP / HF Hub | File existence & size check | `%LOCALAPPDATA%\TTS-Studio\models\f5tts\` |
| **`chatterbox`** | Hugging Face | `ResembleAI/chatterbox` | `chatterbox_turbo.pt` | Embedded | 1.10 GB | Resumable HTTP / HF Hub | File existence & size check | `%LOCALAPPDATA%\TTS-Studio\models\chatterbox\` |
| **`fishspeech`** | Hugging Face | `fishaudio/fish-speech-1.5` | `model.ckpt` | Config & VQ-GAN weights | 2.50 GB | Isolated Venv + HF Hub | File existence & size check | `%LOCALAPPDATA%\TTS-Studio\models\fishspeech\` |
| **`omnivoice`** | Hugging Face | `k2-fsa/omnivoice` | `omnivoice.onnx` | Tokenizer | 1.50 GB | Isolated Venv + HF Hub | File existence & size check | `%LOCALAPPDATA%\TTS-Studio\models\omnivoice\` |
| **`cosyvoice`** | Hugging Face | `FunAudioLLM/CosyVoice-300M` | `cosyvoice.pt` | LLM tokenizer & configs | 2.20 GB | Isolated Venv + HF Hub | File existence & size check | `%LOCALAPPDATA%\TTS-Studio\models\cosyvoice\` |
| **`xttsv2`** | Hugging Face | `coqui/XTTS-v2` | `model.pth` | `vocab.json`, `config.json` | 1.80 GB | Isolated Venv + Subprocess | File existence & size check | `%LOCALAPPDATA%\TTS-Studio\models\xttsv2\` |
| **`indextts2`** | Hugging Face | `IndexTTS/IndexTTS2` | `indextts2.pt` | Config files | 2.00 GB | Isolated Venv + HF Hub | File existence & size check | `%LOCALAPPDATA%\TTS-Studio\models\indextts2\` |

---

## 4. Runtime vs Weights Architecture Audit
The application architecture enforces strict separation between:
1. **Model Runtime**: The Python virtual environment (`.venv` or isolated runtimes in `.venv_<model_id>`) containing compiled libraries (`torch`, `torchaudio`, `transformers`, `f5-tts`, `chatterbox-tts`, `TTS`).
2. **Model Weights**: Multi-gigabyte binary files (`.safetensors`, `.pt`, `.ckpt`, `.pth`) downloaded on demand to `%LOCALAPPDATA%\TTS-Studio\models\<model_id>\`.

> [!CAUTION]
> Downloading model weights alone is **NOT** sufficient to run inference if the corresponding model runtime environment or binary libraries are missing.

---

## 5. Original TTS Logic Trace Audit
The existing Python logic in [`scripts/tts_adapters.py`](file:///e:/TTS/scripts/tts_adapters.py) and [`scripts/speech_synth_helper.py`](file:///e:/TTS/scripts/speech_synth_helper.py) serves as the authoritative baseline:

```
TEXT INPUT
  ↓
PREPROCESSING (preprocess_tts_text: converts custom pause tags [pause]/<pause> -> ..., markdown stress -> CAPS)
  ↓
PRONUNCIATION (dict substitution for acronyms: TTS -> T-T-S, VRAM -> V-RAM, plus configs/pronunciation_map.json)
  ↓
CHUNKING (IntelligentChunker / _chunk_text_for_f5tts: splits into sentence/word blocks <= 60 words)
  ↓
VOICE SELECTION (Resolves selected category to reference WAV path in voices/)
  ↓
ORIGINAL REFERENCE WAV (Validates file existence > 1000 bytes)
  ↓
SPEAKER CONDITIONING (SpeakerConditioningCache keyed by audio path & modification time)
  ↓
SELECTED MODEL ADAPTER (F5TTSAdapter, ChatterboxAdapter, XTTSv2Adapter, etc.)
  ↓
REAL INFERENCE EXECUTION (Target model class runs on CUDA or CPU)
  ↓
AUDIO POST-PROCESSING (Wave export, optional librosa pitch shift / speed stretch / duration trim)
  ↓
FINAL OUTPUT WAV (%LOCALAPPDATA%\TTS-Studio\outputs\<model_id>\)
```

---

## 6. Original Zero-Shot Voice Assets Audit & SHA256 Catalog

All 7 reference WAV files in [`voices/`](file:///e:/TTS/voices/) have been audited. Audio binaries remain unmodified:

| Category | Relative Path | Size (Bytes) | SHA256 Checksum | Preservation Status |
| :--- | :--- | :---: | :--- | :---: |
| **Announcement** | `voices/Announcement/ENG_US_M_DaveL.wav` | 1,323,044 | `2feef2f8757689dae8795988d0dbe481213eb68870b0e6e70f0180503c345d5a` | **UNTOUCHED** ✓ |
| **Audiobook** | `voices/Audiobook/ENG_US_M_BrianR.wav` | 573,344 | `d5e9a7d1ba9e95c82ef7a3d6655939593ba148538aef9032fe9cc9daf4f2f508` | **UNTOUCHED** ✓ |
| **Narration** | `voices/Narration/deep_male_narrator.wav` | 720,044 | `4cb488d29436a948c0dd2d0ffbe3586eb9e69ba811bd595722e30d473f9f04f1` | **UNTOUCHED** ✓ |
| **Podcast** | `voices/Podcast/johnb.wav` | 1,323,044 | `f13ae181b0d45d4804fd49c82923a8408cfdb815b994fc843a162c99c3164738` | **UNTOUCHED** ✓ |
| **Presentation** | `voices/Presentation/ENG_US_M_DCG.wav` | 1,323,044 | `e724a368b6ee79576f651572d55d6695a886608fc164d44b744cdfbeaee91ad0` | **UNTOUCHED** ✓ |
| **Social Media** | `voices/Social Media/FDownload.app-....wav` | 1,440,044 | `0e07b1003aac94de258bd03c1230960d4f6ac5a1d5ed4019990bb252ecb1a2a3` | **UNTOUCHED** ✓ |
| **Storytelling** | `voices/Storytelling/dl-090b86a8217d.wav` | 661,544 | `b813a1fa4a853feaa2ae91725af9311fcda130b822d669a6c8e1c59d27cb1695` | **UNTOUCHED** ✓ |

---

## 7. No Silent Fallback Audit Finding

> [!WARNING]
> **Audit Discovery in [`scripts/speech_synth_helper.py`](file:///e:/TTS/scripts/speech_synth_helper.py#L572-L613)**: The legacy helper contains an auto-delegation block that falls back to F5-TTS, gTTS, or SAPI5 if a requested model is unavailable:
> ```python
> # Legacy block in speech_synth_helper.py:
> if not success:
>     if _f5tts_available():
>         print(f"[>>] [{model_id}] Delegating to F5-TTS zero-shot cloning...")
> ```
> **Corrective Action**: In [`scripts/generation_engine.py`](file:///e:/TTS/scripts/generation_engine.py) and [`scripts/tts_adapters.py`](file:///e:/TTS/scripts/tts_adapters.py), auto-delegation is explicitly bypassed. If a selected model is missing or uninstalled, the backend returns an explicit error (`DEPENDENCY_MISSING` or `MODEL_NOT_DOWNLOADED`) and fails fast without silent redirection.

---

## 8. Packaging & Bundle Component Audit

| Component | In Installer Binary? | Post-Install Dynamic Setup | Storage Location |
| :--- | :---: | :--- | :--- |
| **Electron Application** | YES | Bundled executable | Program Files / App Install Dir |
| **React UI Assets** | YES | Pre-compiled (`frontend/dist/`) | Program Files / App Install Dir |
| **FastAPI Backend Executable** | YES | Standalone PyInstaller binary | Program Files / App Install Dir |
| **Python Core Runtime** | YES | Bundled Python 3.10 runtime | Program Files / App Install Dir |
| **TTS Adapters & Helpers** | YES | Included in backend binary | Program Files / App Install Dir |
| **Original Reference Voice WAVs** | YES | Included in backend data | Program Files / App Install Dir |
| **Model Weights (.safetensors, .pt)** | **NO** | Downloaded on demand via Model Manager | `%LOCALAPPDATA%\TTS-Studio\models\` |
| **Isolated Model Runtimes** | **NO** | Created dynamically on demand | `%LOCALAPPDATA%\TTS-Studio\runtimes\` |

---

## 9. Clean Machine Test Protocol Audit

| Step | Action | Status |
| :---: | :--- | :---: |
| 1 | Install on clean Windows machine (no Python/Node/Git pre-installed) | **NOT TESTED** |
| 2 | Launch desktop application & automatic backend startup | **NOT TESTED** |
| 3 | Automatic hardware capability detection (GPU/CUDA vs CPU) | TESTED (Local Dev Env) |
| 4 | Model Manager status display across all 7 models | TESTED (Local Dev Env) |
| 5 | Official Model Weights Download from Hugging Face | **NOT TESTED** |
| 6 | Resumable Download pause/resume handling | TESTED (Mock / Unit level) |
| 7 | Model Weight integrity verification | TESTED (Unit level) |
| 8 | Load original reference voice WAV | TESTED (Local Dev Env) |
| 9 | Real Model Inference execution | **NOT TESTED** |
| 10 | Output WAV generation & playback | TESTED (Unit level) |
| 11 | Restart app & reuse downloaded model | **NOT TESTED** |
| 12 | Offline inference capability | **NOT TESTED** |

---

## 10. Testing Categorization Correction

| Test Category | Description | Count / Scope | Actual Status |
| :--- | :--- | :---: | :---: |
| **Unit Tests** | Structural testing for API routes, Pydantic schemas, path resolution, hardware detector, voice indexer, and chunker | 33 Tests | **33/33 PASSED** ✓ |
| **Integration Tests** | FastAPI live server request/response handling, model manager state machine queries | 7 Tests | **7/7 PASSED** ✓ |
| **Real Model Inference Tests** | Actual end-to-end execution of F5-TTS, Chatterbox, Fish Speech, XTTS-v2 with downloaded weights | 7 Models | **NOT TESTED** |
| **Packaging Build Tests** | Compiling final `TTS Studio Setup.exe` installer | 1 Installer | **NOT TESTED** |
| **Clean Machine Tests** | Deploying installer on isolated clean Windows machine | 1 Machine | **NOT TESTED** |

---

## 11. Current Blockers & Required Corrections

1. **Model Weights Download & Storage**: No model weight files (`.safetensors`, `.pt`) currently reside in `%LOCALAPPDATA%\TTS-Studio\models\`. Real inference tests cannot be claimed until weights are downloaded and executed.
2. **Isolated Environment Instantiation**: Isolated virtual environments (`.venv_xtts`, `.venv_fishspeech`, etc.) have not yet been populated with their specific PyTorch/Transformers dependencies.
3. **Legacy Auto-Delegation Removal**: The legacy fallback logic in `speech_synth_helper.py` must be completely cleaned so that calling `synthesize_human_speech` directly can never trigger fallback.

---

## 12. Corrective Audit Conclusion & Recommendation
Development is stopped. Awaiting your review of this corrective audit report.

- **Recommended Next Phase**: **CORRECTIVE AUDIT REVIEW & APPROVAL**
- Once approved, proceed strictly one phase at a time under your explicit command (`NEXT PHASE`).
