"""
TTS Studio Path Resolver Module — v1.2.0
=========================================
SINGLE SOURCE OF TRUTH for all application storage paths.
All paths resolve to %LOCALAPPDATA%\\TTS-Studio\\ in both development
and packaged production installs.

Storage layout:
    %LOCALAPPDATA%\\TTS-Studio\\
        models\\
            f5tts\\              — F5-TTS model weights & vocoder
            chatterbox\\         — Chatterbox Turbo weights
            xttsv2\\             — XTTS-v2 checkpoints & vocab
        cache\\
            huggingface\\        — HuggingFace library cache
        outputs\\                — Generated audio files (.wav)
        voices\\                 — User custom speaker reference voices
        logs\\                   — Application execution logs
        runtimes\\               — Isolated Python virtual environments
"""

import os
import sys


# ---------------------------------------------------------------------------
# Base user-data directory — always %LOCALAPPDATA%\TTS-Studio\
# ---------------------------------------------------------------------------

def get_base_dir() -> str:
    """
    Returns the root base directory for all TTS Studio user data:
    C:\\Users\\<username>\\AppData\\Local\\TTS-Studio
    """
    local_appdata = os.environ.get(
        "LOCALAPPDATA",
        os.path.join(os.path.expanduser("~"), "AppData", "Local")
    )
    base_path = os.path.join(local_appdata, "TTS-Studio")
    os.makedirs(base_path, exist_ok=True)
    return base_path


def get_app_dir() -> str:
    """
    Returns the application root directory containing bundled resources.
    In dev: E:\\TTS
    In production: resources directory of packaged app.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(scripts_dir)


# ---------------------------------------------------------------------------
# Models Directory: %LOCALAPPDATA%\TTS-Studio\models
# ---------------------------------------------------------------------------

def get_models_dir() -> str:
    """
    Returns: C:\\Users\\<username>\\AppData\\Local\\TTS-Studio\\models
    """
    path = os.path.join(get_base_dir(), "models")
    os.makedirs(path, exist_ok=True)
    return path


def get_model_dir(model_id: str) -> str:
    """
    Returns specific model directory:
    Example: get_model_dir("f5tts") -> %LOCALAPPDATA%\\TTS-Studio\\models\\f5tts
             get_model_dir("chatterbox") -> %LOCALAPPDATA%\\TTS-Studio\\models\\chatterbox
             get_model_dir("xttsv2") -> %LOCALAPPDATA%\\TTS-Studio\\models\\xttsv2
    """
    clean_id = model_id.lower().replace("-", "").replace("_", "")
    if "f5" in clean_id:
        canonical = "f5tts"
    elif "chatter" in clean_id:
        canonical = "chatterbox"
    elif "xtts" in clean_id:
        canonical = "xttsv2"
    else:
        canonical = clean_id

    path = os.path.join(get_models_dir(), canonical)
    os.makedirs(path, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Outputs Directory: %LOCALAPPDATA%\TTS-Studio\outputs
# ---------------------------------------------------------------------------

def get_outputs_dir() -> str:
    """
    Returns: C:\\Users\\<username>\\AppData\\Local\\TTS-Studio\\outputs
    """
    path = os.path.join(get_base_dir(), "outputs")
    os.makedirs(path, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# HuggingFace Cache Directory: %LOCALAPPDATA%\TTS-Studio\cache\huggingface
# ---------------------------------------------------------------------------

def get_hf_cache_dir() -> str:
    """
    Returns: C:\\Users\\<username>\\AppData\\Local\\TTS-Studio\\cache\\huggingface
    """
    path = os.path.join(get_base_dir(), "cache", "huggingface")
    os.makedirs(path, exist_ok=True)
    return path


def configure_hf_environment() -> None:
    """
    Configures HuggingFace environment variables to route exclusively to:
    %LOCALAPPDATA%\\TTS-Studio\\cache\\huggingface
    """
    hf_cache = get_hf_cache_dir()
    os.environ["HF_HOME"] = hf_cache
    os.environ["HUGGINGFACE_HUB_CACHE"] = os.path.join(hf_cache, "hub")
    os.environ["TRANSFORMERS_CACHE"] = os.path.join(hf_cache, "hub")
    os.environ["HF_DATASETS_CACHE"] = os.path.join(hf_cache, "datasets")


# ---------------------------------------------------------------------------
# Voices Directory (Bundled & User Custom)
# ---------------------------------------------------------------------------

def get_voices_dir() -> str:
    """
    Returns primary voices directory.
    Prefers app bundled voices/ directory, fallback to user AppData.
    """
    app_voices = os.path.join(get_app_dir(), "voices")
    if os.path.isdir(app_voices) and os.listdir(app_voices):
        return app_voices
    path = os.path.join(get_base_dir(), "voices")
    os.makedirs(path, exist_ok=True)
    return path


def get_default_voice_path() -> str | None:
    """Returns fallback reference voice path."""
    voices_dir = get_voices_dir()
    candidates = [
        os.path.join(voices_dir, "Narration", "deep_male_narrator.wav"),
        os.path.join(voices_dir, "Podcast", "johnb.wav"),
        os.path.join(voices_dir, "Audiobook", "ENG_US_M_BrianR.wav"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    for root, _, files in os.walk(voices_dir):
        for f in files:
            if f.lower().endswith(".wav"):
                return os.path.join(root, f)
    return None


def get_logs_dir() -> str:
    """Returns: C:\\Users\\<username>\\AppData\\Local\\TTS-Studio\\logs"""
    path = os.path.join(get_base_dir(), "logs")
    os.makedirs(path, exist_ok=True)
    return path


def get_runtimes_dir() -> str:
    """Returns: C:\\Users\\<username>\\AppData\\Local\\TTS-Studio\\runtimes"""
    path = os.path.join(get_base_dir(), "runtimes")
    os.makedirs(path, exist_ok=True)
    return path
