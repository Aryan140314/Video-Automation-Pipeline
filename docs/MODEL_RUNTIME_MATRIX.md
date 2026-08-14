# Model Runtime Matrix & Integration Specification

## 1. Overview
This matrix provides a detailed evaluation of all 7 target zero-shot TTS models for TTS Studio.
It establishes official repositories, Python/PyTorch requirements, CUDA/CPU support, model weights storage sizes, and runtime isolation policies.

---

## 2. Comprehensive Model Matrix

| Model ID | Official Model Name | Official Repository / Library | Python | PyTorch | CUDA / CPU Support | Weight Size | Main / Isolated Environment | Adapter Baseline Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **f5tts** | F5-TTS | `SWAVE-LAB/F5-TTS` (`f5-tts`) | 3.10 | $\ge$2.0 (2.4.1+cu121) | CUDA + CPU | ~1.28 GB | Main `.venv` | **READY** ✓ |
| **chatterbox** | Chatterbox Turbo | `Resemble AI / chatterbox-tts` | 3.10 | $\ge$2.0 (2.4.1+cu121) | CUDA + CPU | ~1.10 GB | Main `.venv` | **READY** ✓ |
| **fishspeech** | Fish Speech S2 | `fishaudio/fish-speech` | 3.10 | 2.2+ / 2.4+ | CUDA (CPU slow) | ~2.50 GB | Isolated (`.venv_fishspeech`) | DEPENDENCY_MISSING |
| **omnivoice** | OmniVoice | `k2-fsa/omnivoice` | 3.10 | 2.1+ / 2.4+ | CUDA + CPU | ~1.50 GB | Isolated (`.venv_omnivoice`) | DEPENDENCY_MISSING |
| **cosyvoice** | CosyVoice 3 | `FunAudioLLM/CosyVoice` | 3.10 | 2.1+ / 2.3+ | CUDA + CPU | ~2.20 GB | Isolated (`.venv_cosyvoice`) | DEPENDENCY_MISSING |
| **xttsv2** | XTTS-v2 | `coqui-ai/TTS` | 3.10 | 2.1.2 / 2.2.0 | CUDA + CPU | ~1.80 GB | Isolated (`.venv_xtts`) | Subprocess Runner Ready |
| **indextts2** | IndexTTS2 | `IndexTTS/IndexTTS2` | 3.10 | 2.1+ / 2.4+ | CUDA + CPU | ~2.00 GB | Isolated (`.venv_indextts`) | DEPENDENCY_MISSING |

---

## 3. Real Model Rule & Verification Standard
A model is marked **READY** if and only if:
1. Official library is installed.
2. Required dependencies compile and import cleanly without version collision.
3. Weights are present in local storage (`%LOCALAPPDATA%\TTS-Studio\models\<model_id>\`).
4. Actual model class initializes on target device (`cuda` or `cpu`).
5. Real inference succeeds using an original reference voice WAV from `voices/`.
6. Valid WAV output is written and verified.

> [!IMPORTANT]
> A model MUST NOT be marked READY simply because its package is pip installed or a dummy wrapper returns successful metadata. If dependencies or weights are missing, the adapter explicitly returns `DEPENDENCY_MISSING` or `MODEL_NOT_DOWNLOADED`. Silent fallbacks (e.g. executing F5-TTS when Chatterbox was requested) are strictly prohibited.

---

## 4. Storage Locations (Production Standard)
Models weights are downloaded on demand to user-local storage:
- Root: `%LOCALAPPDATA%\TTS-Studio\models\`
- Folders:
  - `%LOCALAPPDATA%\TTS-Studio\models\f5tts\`
  - `%LOCALAPPDATA%\TTS-Studio\models\chatterbox\`
  - `%LOCALAPPDATA%\TTS-Studio\models\fishspeech\`
  - `%LOCALAPPDATA%\TTS-Studio\models\omnivoice\`
  - `%LOCALAPPDATA%\TTS-Studio\models\cosyvoice\`
  - `%LOCALAPPDATA%\TTS-Studio\models\xttsv2\`
  - `%LOCALAPPDATA%\TTS-Studio\models\indextts2\`
