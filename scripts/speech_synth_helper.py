"""
Speech Synthesis Engine — Zero-Shot Voice Cloning + Neural TTS
=================================================================
Two operating modes depending on whether a reference voice is provided:

  CLONING MODE  (reference_voice provided)
  ─────────────────────────────────────────
  1. Chatterbox TTS  — diffusion-based zero-shot cloner (pip install chatterbox-tts)
  2. F5-TTS          — flow-matching zero-shot cloner    (pip install f5-tts)

  4. gTTS            — online Google TTS fallback
  5. SAPI5           — last resort

  PRESET MODE  (no reference_voice)
  ─────────────────────────────────────────

  2. gTTS            — online Google TTS
  3. SAPI5           — last resort

Handles Windows COM thread init (CoInitialize) for Streamlit threads.
"""

import os
# Redirect HuggingFace cache to local virtual environment folder (.venv/hf_cache)
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
_workspace_root = os.path.dirname(_scripts_dir)
os.environ["HF_HOME"] = os.path.abspath(os.path.join(_workspace_root, ".venv", "hf_cache"))

import wave
import time
import warnings
import logging
import json
import re
import glob


# ─────────────────────────────────────────────────────────────────────────────
# Text utilities — chunking for models with context-length limits
# ─────────────────────────────────────────────────────────────────────────────

def _chunk_text_for_f5tts(text: str, max_words: int = 300) -> list[str]:
    """
    Split text into chunks of at most `max_words` words each.
    F5-TTS has an 8,192-token context window; ~300 words is a safe margin.
    Handles punctuated and unpunctuated long text safely.
    Prefers sentence boundaries, falls back to commas/clauses, then word limits.
    """
    import re as _re
    text = text.strip()
    if not text:
        return []

    words = text.split()
    if len(words) <= max_words:
        return [text]

    # Split into units by sentence punctuation or commas/pauses
    units = _re.split(r'(?<=[.!?,;])\s+', text)

    # If no punctuation at all, split into raw word blocks
    if len(units) == 1 and len(units[0].split()) > max_words:
        all_w = units[0].split()
        return [' '.join(all_w[i:i + max_words]) for i in range(0, len(all_w), max_words)]

    chunks, current, current_wc = [], [], 0
    for u in units:
        u_words = u.split()
        if not u_words:
            continue
        # If a single unit is longer than max_words itself
        if len(u_words) > max_words:
            if current:
                chunks.append(' '.join(current))
                current, current_wc = [], 0
            for i in range(0, len(u_words), max_words):
                chunks.append(' '.join(u_words[i:i + max_words]))
            continue

        if current_wc + len(u_words) > max_words and current:
            chunks.append(' '.join(current))
            current, current_wc = [], 0
        current.append(u)
        current_wc += len(u_words)

    if current:
        chunks.append(' '.join(current))

    return chunks if chunks else [text]


def _clear_hf_model_cache(keyword: str) -> int:
    """
    Delete all files matching `keyword` inside the HuggingFace cache directory.
    Used to auto-heal corrupted model/tokenizer files.
    Returns the number of files deleted.
    """
    hf_home = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
    deleted = 0
    for fpath in glob.glob(os.path.join(hf_home, "**", f"*{keyword}*"), recursive=True):
        try:
            os.remove(fpath)
            print(f"[cache-clear] Deleted corrupted cache file: {fpath}")
            deleted += 1
        except Exception as e:
            print(f"[cache-clear] Could not delete {fpath}: {e}")
    return deleted

# Suppress non-critical warning messages and HTTP check outputs
warnings.filterwarnings("ignore")
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

# ---------------------------------------------------------------------------
# Configure pydub and system environment to use bundled ffmpeg (imageio-ffmpeg)
# ---------------------------------------------------------------------------
try:
    import imageio_ffmpeg
    import shutil

    _FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()
    _FFMPEG_DIR = os.path.dirname(_FFMPEG_BIN)
    _FFMPEG_EXE = os.path.join(_FFMPEG_DIR, "ffmpeg.exe")

    if not os.path.exists(_FFMPEG_EXE):
        try:
            shutil.copy(_FFMPEG_BIN, _FFMPEG_EXE)
        except Exception:
            pass

    # Add to system PATH first so pydub and transformers can find it
    if _FFMPEG_DIR not in os.environ["PATH"]:
        os.environ["PATH"] = _FFMPEG_DIR + os.pathsep + os.environ["PATH"]

    # Configure pydub
    from pydub import AudioSegment
    AudioSegment.converter = _FFMPEG_BIN
    AudioSegment.ffprobe = _FFMPEG_BIN
except Exception:
    _FFMPEG_BIN = "ffmpeg"

# ─────────────────────────────────────────────────────────────────────────────
# Backend availability checks
# ─────────────────────────────────────────────────────────────────────────────


def _chatterbox_available() -> bool:
    try:
        import chatterbox  # noqa: F401

        return True
    except ImportError:
        return False


def _f5tts_available() -> bool:
    try:
        import f5_tts  # noqa: F401

        return True
    except ImportError:
        try:
            # pyrefly: ignore [missing-import]
            from f5tts.infer.utils_infer import infer_process  # noqa: F401

            return True
        except ImportError:
            return False


def _kokoro_available() -> bool:
    try:
        import kokoro  # noqa: F401
        import soundfile  # noqa: F401

        return True
    except ImportError:
        return False


def _gtts_available() -> bool:
    try:
        from gtts import gTTS  # noqa: F401

        return True
    except ImportError:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Kokoro voice presets — one distinct character per model slot
# ─────────────────────────────────────────────────────────────────────────────

_KOKORO_VOICE_MAP = {
    "chatterbox": "am_adam",  # Authoritative American male
    "fishspeech": "am_michael",  # Deep clear American male
    "omnivoice": "bm_george",  # Distinguished British male
    "cosyvoice": "bm_lewis",  # Clear British male
    "xttsv2": "am_adam",  # Authoritative American male
    "f5tts": "am_fenrir",  # Strong crisp American male
    "indextts2": "bm_george",  # Distinguished British male
    "kokoro": "am_puck",  # Bright friendly American male
    "elevenlabs": "am_michael",  # Deep clear American male
}

# ─────────────────────────────────────────────────────────────────────────────
# Cached model instances (avoid reloading on every call)
# ─────────────────────────────────────────────────────────────────────────────

_chatterbox_model = None
_chatterbox_lock = None

_kokoro_pipelines: dict = {}  # lang_code -> KPipeline instance (cached per language)
_kokoro_lock = None


# ─────────────────────────────────────────────────────────────────────────────
# Backend 1 (Cloning): Chatterbox TTS — diffusion zero-shot cloner
# ─────────────────────────────────────────────────────────────────────────────


def _ensure_chatterbox():
    global _chatterbox_model, _chatterbox_lock
    if _chatterbox_lock is None:
        import threading

        _chatterbox_lock = threading.Lock()
    with _chatterbox_lock:
        if _chatterbox_model is None:
            import torch
            try:
                import perth
                if not hasattr(perth, "PerthImplicitWatermarker") and hasattr(perth, "Perth"):
                    perth.PerthImplicitWatermarker = perth.Perth
                if hasattr(perth, "Perth") and not hasattr(perth.Perth, "apply_watermark"):
                    perth.Perth.apply_watermark = lambda self, wav, sample_rate=24000: wav
            except Exception:
                pass
            from chatterbox.tts import ChatterboxTTS

            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"[>>] Loading Chatterbox TTS on {device}...")
            _chatterbox_model = ChatterboxTTS.from_pretrained(device=device)
    return _chatterbox_model


def _synthesize_chatterbox_clone(
    text: str, reference_wav: str, output_path: str, _max_words: int = 60
) -> bool:
    """Zero-shot voice cloning with Chatterbox TTS with smart text chunking."""
    try:
        import torch
        import torchaudio

        model = _ensure_chatterbox()
        chunks = _chunk_text_for_f5tts(text, max_words=_max_words)

        if len(chunks) > 1:
            print(f"[>>] Chatterbox: text split into {len(chunks)} chunks (max {_max_words} words each)")
        else:
            print(f"[>>] Chatterbox cloning with reference: {os.path.basename(reference_wav)}")

        all_wavs = []
        for idx, chunk in enumerate(chunks):
            if len(chunks) > 1:
                print(f"[>>] Chatterbox chunk {idx + 1}/{len(chunks)} ({len(chunk.split())} words)...")
            wav = model.generate(chunk, audio_prompt_path=reference_wav)
            if isinstance(wav, torch.Tensor):
                wav = wav.cpu()
            all_wavs.append(wav)

        if not all_wavs:
            return False

        combined_wav = torch.cat(all_wavs, dim=-1) if len(all_wavs) > 1 else all_wavs[0]
        torchaudio.save(output_path, combined_wav, model.sr)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except Exception as e:
        print(f"[!] Chatterbox cloning failed: {e}")
        return False


def _synthesize_chatterbox_preset(text: str, output_path: str) -> bool:
    """Chatterbox TTS without a reference voice (default voice)."""
    try:
        import torch
        import torchaudio

        model = _ensure_chatterbox()
        wav = model.generate(text)
        torchaudio.save(output_path, wav, model.sr)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except Exception as e:
        print(f"[!] Chatterbox preset failed: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Backend 2 (Cloning): F5-TTS — flow-matching zero-shot cloner
# ─────────────────────────────────────────────────────────────────────────────

_f5tts_model = None
_f5tts_lock = None


def _ensure_f5tts_model():
    global _f5tts_model, _f5tts_lock
    if _f5tts_lock is None:
        import threading

        _f5tts_lock = threading.Lock()
    with _f5tts_lock:
        if _f5tts_model is None:
            from f5_tts.api import F5TTS
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"[>>] Loading F5-TTS model on {device}...")
            _f5tts_model = F5TTS(device=device)
    return _f5tts_model


def _synthesize_f5tts_clone(text: str, reference_wav: str, output_path: str,
                             _max_words: int = 60) -> bool:
    """
    Zero-shot voice cloning with F5-TTS Python API.
    Automatically chunks long text into <=`_max_words`-word segments to avoid
    the 8,192-token context limit. Each chunk is synthesised separately then
    concatenated into a single output file.
    """
    try:
        import numpy as np
        import soundfile as sf

        model = _ensure_f5tts_model()
        chunks = _chunk_text_for_f5tts(text, max_words=_max_words)

        if len(chunks) > 1:
            print(f"[>>] F5-TTS: text split into {len(chunks)} chunks "
                  f"(max {_max_words} words each) to fit 8K context window")
        else:
            print(f"[>>] F5-TTS cloning reference: {os.path.basename(reference_wav)}")

        all_audio = []
        sample_rate = 24000  # F5-TTS default

        for idx, chunk in enumerate(chunks):
            if len(chunks) > 1:
                print(f"[>>] F5-TTS chunk {idx + 1}/{len(chunks)} "
                      f"({len(chunk.split())} words)...")
            try:
                wav, sr, _ = model.infer(
                    ref_file=reference_wav,
                    ref_text="",  # auto-transcribe reference
                    gen_text=chunk,
                    show_info=lambda x: None,
                )
                sample_rate = sr
                if isinstance(wav, list):
                    wav = np.concatenate(wav)
                all_audio.append(wav)
            except RuntimeError as chunk_err:
                err_msg = str(chunk_err)
                if "size of tensor" in err_msg or "must match" in err_msg:
                    # Chunk still too long — retry with half the word budget
                    if _max_words > 100:
                        print(f"[!] F5-TTS chunk {idx+1} still too long "
                              f"— retrying with {_max_words // 2} word limit")
                        return _synthesize_f5tts_clone(
                            text, reference_wav, output_path,
                            _max_words=_max_words // 2
                        )
                raise  # re-raise if not a size error

        if not all_audio:
            return False

        combined = np.concatenate(all_audio) if len(all_audio) > 1 else all_audio[0]
        sf.write(output_path, combined, sample_rate)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000

    except Exception as e:
        print(f"[!] F5-TTS cloning failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Backend 3: gTTS — Google online TTS (natural, no cloning)
# ─────────────────────────────────────────────────────────────────────────────


def _synthesize_gtts(text: str, output_path: str) -> bool:
    """gTTS online synthesis with guaranteed temp file cleanup."""
    mp3_path = output_path.replace(".wav", "_tmp.mp3")
    try:
        from gtts import gTTS
        from pydub import AudioSegment

        gTTS(text=text, lang="en", slow=False).save(mp3_path)
        AudioSegment.converter = _FFMPEG_BIN
        AudioSegment.from_mp3(mp3_path).export(output_path, format="wav")
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except Exception as e:
        print(f"[!] gTTS failed: {e}")
        return False
    finally:
        # Always remove temp mp3 regardless of success or failure (prevents disk leak)
        if os.path.exists(mp3_path):
            try:
                os.remove(mp3_path)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# Backend 5: Windows SAPI5 — robotic last-resort emergency fallback
# ─────────────────────────────────────────────────────────────────────────────


def _synthesize_sapi(text: str, output_path: str) -> bool:
    try:
        import win32com.client

        co_initialized = False
        try:
            import pythoncom

            pythoncom.CoInitialize()
            co_initialized = True
        except Exception:
            pass
        try:
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            stream = win32com.client.Dispatch("SAPI.SpFileStream")
            stream.Open(output_path, 3, False)
            speaker.AudioOutputStream = stream
            speaker.Speak(text)
            stream.Close()
        finally:
            if co_initialized:
                try:
                    import pythoncom

                    pythoncom.CoUninitialize()
                except Exception:
                    pass
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except Exception as e:
        print(f"[!] SAPI5 failed: {e}")
        return False


def preprocess_tts_text(text: str) -> str:
    """
    Preprocess text to improve neural TTS pronunciation, pauses, and emphasis.
    """
    if not text:
        return text

    # 1. Custom pause tags: convert [pause], [break], <pause>, <break> to ellipses
    text = text.replace("[pause]", "...").replace("[break]", "...")
    text = text.replace("<pause>", "...").replace("<break>", "...")

    # 2. Convert markdown bolding (**word**) and italics (*word*) to capitalized (WORD) for neural stress
    def make_caps(match):
        return match.group(1).upper()
    text = re.sub(r"\*\*([^*]+)\*\*", make_caps, text)
    text = re.sub(r"\*([^*]+)\*", make_caps, text)

    # 3. Custom Pronunciation Dictionary for technical acronyms (prevents incorrect pronunciation)
    pronunciation_dict = {
        "TTS": "T-T-S",
        "VRAM": "V-RAM",
        "RTF": "R-T-F",
        "CPU": "C-P-U",
        "GPU": "G-P-U",
    }

    # Load user-customized pronunciation map from configs/pronunciation_map.json
    try:
        _scripts_dir = os.path.dirname(os.path.abspath(__file__))
        _workspace_root = os.path.dirname(_scripts_dir)
        map_path = os.path.join(_workspace_root, "configs", "pronunciation_map.json")
        if os.path.exists(map_path):
            with open(map_path, "r", encoding="utf-8") as f:
                user_map = json.load(f)
                pronunciation_dict.update(user_map)
    except Exception as e:
        print(f"[!] Warning: Failed to load user pronunciation map: {e}")
    
    # Replace whole words only (case-insensitive boundary checks)
    for word, phonetic in pronunciation_dict.items():
        pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
        text = pattern.sub(phonetic, text)

    return text


def synthesize_human_speech(
    text: str, model_id: str, reference_voice: str = None, output_path: str = None
) -> dict:
    """
    Generate natural, human-quality speech with optional zero-shot voice cloning.

    CLONING MODE  — when reference_voice is a valid .wav file:
        1. Chatterbox TTS  (diffusion zero-shot cloner)
        2. F5-TTS          (flow-matching zero-shot cloner)
        3. Kokoro-82M      (preset fallback — no cloning)
        4. gTTS            (online fallback)
        5. SAPI5           (last resort)

    PRESET MODE  — when no reference_voice:
        1. Kokoro-82M      (best quality preset neural voice)
        2. gTTS            (online Google TTS)
        3. SAPI5           (last resort)

    Args:
        text:            Text to synthesize
        model_id:        TTS model slot ID (maps to Kokoro voice character)
        reference_voice: Path to reference .wav for zero-shot cloning
        output_path:     Where to write the output .wav file

    Returns:
        dict: model, backend, cloning_active, gen_time, duration, file_size_kb, output_path
    """
    text = preprocess_tts_text(text)
    start_t = time.time()

    # Use absolute path to avoid CWD-dependent resolution errors
    if output_path is None:
        output_path = os.path.join(
            _workspace_root, "outputs", model_id, f"{model_id}_output.wav"
        )

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Male-only default fallback: am_michael instead of af_heart
    voice_id = _KOKORO_VOICE_MAP.get(model_id, "am_michael")

    # Validate reference voice
    has_reference = (
        reference_voice is not None
        and os.path.exists(reference_voice)
        and os.path.getsize(reference_voice) > 1000
    )

    cloning_active = False
    backend_used = "none"
    success = False

    if has_reference:
        # ── CLONING MODE — model-ID-driven dispatch with auto-delegation ─────
        print(f"[>>] CLONING MODE — model: {model_id}, reference: {os.path.basename(reference_voice)}")

        # Step 1: Try requested model cloner first if installed
        if model_id == "f5tts":
            if _f5tts_available():
                print("[>>] Trying F5-TTS zero-shot cloning...")
                success = _synthesize_f5tts_clone(text, reference_voice, output_path)
                if success:
                    backend_used = "f5tts-clone"
                    cloning_active = True
                    print("[OK] F5-TTS cloning succeeded — speaking in YOUR voice")
            else:
                print("[!!] F5-TTS not installed — delegating to available zero-shot cloner...")

        elif model_id == "chatterbox":
            if _chatterbox_available():
                print("[>>] Trying Chatterbox TTS zero-shot cloning...")
                success = _synthesize_chatterbox_clone(text, reference_voice, output_path)
                if success:
                    backend_used = "chatterbox-clone"
                    cloning_active = True
                    print("[OK] Chatterbox cloning succeeded — speaking in YOUR voice")
            else:
                print("[!!] Chatterbox not installed — delegating to available zero-shot cloner...")

        # Step 2: Auto-delegate to any available cloner (F5-TTS > Chatterbox)
        if not success:
            if _f5tts_available():
                print(f"[>>] [{model_id}] Delegating to F5-TTS zero-shot cloning...")
                success = _synthesize_f5tts_clone(text, reference_voice, output_path)
                if success:
                    backend_used = "f5tts-clone"
                    cloning_active = True
                    print(f"[OK] F5-TTS cloning succeeded for '{model_id}' — speaking in YOUR voice")

            if not success and _chatterbox_available():
                print(f"[>>] [{model_id}] Delegating to Chatterbox zero-shot cloning...")
                success = _synthesize_chatterbox_clone(text, reference_voice, output_path)
                if success:
                    backend_used = "chatterbox-clone"
                    cloning_active = True
                    print(f"[OK] Chatterbox cloning succeeded for '{model_id}' — speaking in YOUR voice")

    else:
        # ── PRESET MODE — model-ID-driven dispatch ────────────────────────
        print(f"[>>] PRESET MODE — model: {model_id}")

        if model_id == "chatterbox":
            if _chatterbox_available():
                print("[>>] Trying Chatterbox preset (default voice)...")
                success = _synthesize_chatterbox_preset(text, output_path)
                if success:
                    backend_used = "chatterbox-preset"
                    print("[OK] Chatterbox preset succeeded")

    # ── Universal fallbacks ────────────────────────────────────────────────
    if not success and _gtts_available():
        print("[>>] Falling back to gTTS (online Google TTS)...")
        success = _synthesize_gtts(text, output_path)
        if success:
            backend_used = "gtts"

    if not success:
        print("[>>] All backends failed — emergency SAPI5 fallback")
        success = _synthesize_sapi(text, output_path)
        if success:
            backend_used = "sapi5"

    gen_time = round(time.time() - start_t, 4)

    # Audio stats
    duration = 0.0
    file_size_kb = 0.0
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        file_size_kb = round(os.path.getsize(output_path) / 1024, 2)
        try:
            with wave.open(output_path, "r") as wf:
                duration = round(wf.getnframes() / float(wf.getframerate()), 2)
        except Exception:
            duration = round(len(text.split()) * 0.35, 2)

    mode = "CLONING" if cloning_active else "PRESET"
    print(f"[+] [{mode}] Speech Generated: {output_path}")
    print(
        f"    Backend: {backend_used} | Model: {model_id} | Gen: {gen_time}s | Duration: {duration}s | Size: {file_size_kb} KB"
    )

    return {
        "model": model_id,
        "backend": backend_used,
        "cloning_active": cloning_active,
        "gen_time": gen_time,
        "duration": duration,
        "file_size_kb": file_size_kb,
        "output_path": output_path,
    }

def apply_voice_tuning(input_wav: str, output_wav: str, speed: float = 1.0, pitch: float = 0.0, trim_sec: float | None = None) -> dict:
    """
    Applies pitch shift, speed stretching, and duration trimming to a WAV file using librosa.
    Saves the output to output_wav. Returns dict with updated duration and file size.
    """
    import os
    import librosa
    import soundfile as sf
    
    if not os.path.exists(input_wav):
        raise FileNotFoundError(f"Input file not found: {input_wav}")
        
    # Load audio
    y, sr = librosa.load(input_wav, sr=None)
    
    # 1. Apply pitch shift (in semitones)
    if pitch != 0.0:
        y = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch)
        
    # 2. Apply speed stretch
    if speed != 1.0:
        y = librosa.effects.time_stretch(y, rate=speed)
        
    # 3. Apply trim (in seconds)
    if trim_sec is not None:
        max_samples = int(trim_sec * sr)
        if len(y) > max_samples:
            y = y[:max_samples]
            
    # Save output
    sf.write(output_wav, y, sr)
    
    # Calculate new stats
    file_size_kb = round(os.path.getsize(output_wav) / 1024, 2)
    duration = round(len(y) / float(sr), 2)
    
    return {
        "duration": duration,
        "file_size_kb": file_size_kb,
        "output_path": output_wav
    }
