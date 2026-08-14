
# Zero-Shot Reference Voice Asset Inventory & Source-of-Truth Catalog

## 1. Overview
This document registers the exact, un-altered zero-shot reference voice assets stored in `voices/`.
These files serve as the absolute **SOURCE OF TRUTH** for speaker conditioning and zero-shot voice cloning across all TTS model adapters (`F5-TTS`, `Chatterbox Turbo`, `XTTS-v2`, `Fish Speech S2`, `OmniVoice`, `CosyVoice 3`, `IndexTTS2`).

---

## 2. Absolute Asset Preservation Rules
As mandated by the project architectural specification:
- **NO Renaming**: Files retain their original filenames.
- **NO Resampling**: Original sample rates are maintained without conversion.
- **NO Normalization**: Peak and RMS amplitudes are unmodified.
- **NO Recompression**: No transcoding or compression alterations.
- **NO Audio Cleaning**: No background noise reduction or spectral editing applied to source files.
- **NO File Replacements**: Assets are immutable binaries.

---

## 3. Reference Voice Catalog

| Category | Relative File Path | Exact Filename | Size (Bytes) | Size (MB) | Format | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Announcement** | `voices/Announcement/ENG_US_M_DaveL.wav` | `ENG_US_M_DaveL.wav` | 1,323,044 | 1.26 MB | WAV (PCM) | ACTIVE ✓ |
| **Audiobook** | `voices/Audiobook/ENG_US_M_BrianR.wav` | `ENG_US_M_BrianR.wav` | 573,344 | 0.55 MB | WAV (PCM) | ACTIVE ✓ |
| **Narration** | `voices/Narration/deep_male_narrator.wav` | `deep_male_narrator.wav` | 720,044 | 0.69 MB | WAV (PCM) | ACTIVE ✓ |
| **Podcast** | `voices/Podcast/johnb.wav` | `johnb.wav` | 1,323,044 | 1.26 MB | WAV (PCM) | ACTIVE ✓ |
| **Presentation** | `voices/Presentation/ENG_US_M_DCG.wav` | `ENG_US_M_DCG.wav` | 1,323,044 | 1.26 MB | WAV (PCM) | ACTIVE ✓ |
| **Social Media** | `voices/Social Media/FDownload.app-1063976359819594-(320kbps).wav` | `FDownload.app-1063976359819594-(320kbps).wav` | 1,440,044 | 1.37 MB | WAV (PCM) | ACTIVE ✓ |
| **Storytelling** | `voices/Storytelling/dl-090b86a8217d.wav` | `dl-090b86a8217d.wav` | 661,544 | 0.63 MB | WAV (PCM) | ACTIVE ✓ |

---

## 4. UI Mapping Specification
When a user selects a voice category in the TTS Studio desktop application UI, the backend map directly resolves to the corresponding relative file path:

```python
VOICE_CATEGORY_MAP = {
    "Announcement": "voices/Announcement/ENG_US_M_DaveL.wav",
    "Audiobook": "voices/Audiobook/ENG_US_M_BrianR.wav",
    "Narration": "voices/Narration/deep_male_narrator.wav",
    "Podcast": "voices/Podcast/johnb.wav",
    "Presentation": "voices/Presentation/ENG_US_M_DCG.wav",
    "Social Media": "voices/Social Media/FDownload.app-1063976359819594-(320kbps).wav",
    "Storytelling": "voices/Storytelling/dl-090b86a8217d.wav",
}
```

---

## 5. Verification Hash & Audit Baseline
- Total Voice Categories: 7
- Total Indexed Audio Files: 7 WAV files
- Total Raw Audio Binary Size: 7,364,108 bytes (~7.02 MB)
