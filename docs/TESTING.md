# Master Testing Documentation & 10-Point Model Evaluation Matrix

## 1. Overview
This document records the empirical testing results for **TTS Studio**. Every model architecture is evaluated against the 10-point testing matrix required by Section 38 of the master specification.

---

## 2. 10-Point Model Evaluation Matrix

| Criterion | `f5tts` | `chatterbox` | `fishspeech` | `omnivoice` | `cosyvoice` | `xttsv2` | `indextts2` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Import Check** | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **2. Dependency Check** | PASS | PASS | ISOLATED | ISOLATED | ISOLATED | ISOLATED | ISOLATED |
| **3. Weight Check** | PASS | PASS | ON-DEMAND | ON-DEMAND | ON-DEMAND | ON-DEMAND | ON-DEMAND |
| **4. Model Init** | PASS | PASS | STUB | STUB | STUB | SUBPROCESS | STUB |
| **5. Device Detection** | CUDA | CUDA | CUDA | CUDA | CUDA | CUDA | CUDA |
| **6. Ref Voice Load** | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **7. Real Inference** | PASS | PASS | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| **8. WAV Generation** | PASS | PASS | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| **9. Audio Validation** | PASS | PASS | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| **10. Runtime Cleanup** | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **MODEL STATUS** | **READY** | **READY** | `DEP_MISSING` | `DEP_MISSING` | `DEP_MISSING` | `SUBPROCESS` | `DEP_MISSING` |

---

## 3. Golden Regression Verification Summary
As mandated by Master Specification Section 39:
- **Pipeline Equivalence**: Preprocessing (`preprocess_tts_text`) converts custom pause tags, bolding stress capitalization, and pronunciation dictionary entries (`TTS` $\rightarrow$ `T-T-S`) identically to the original logic.
- **Voice Asset Equivalence**: Selected voice categories in the app resolve to the original reference WAV files in `voices/` without modifying audio data.
- **Model Identity**: Executing F5-TTS or Chatterbox targets the exact underlying model adapter without silent redirection.
- **No Silent Fallback**: Selecting an uninstalled model (`fishspeech`, `omnivoice`, `cosyvoice`, `indextts2`) explicitly returns `DEPENDENCY_MISSING` status without silently executing F5-TTS or SAPI5.

---

## 4. Automated Test Suite Execution Output

```powershell
PS E:\TTS> .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
........................................
----------------------------------------------------------------------
Ran 40 tests in 1.450s

OK
```
