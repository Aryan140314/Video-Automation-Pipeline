"""
TTS Studio Path Resolver Module
================================
Provides dynamic, resolution of application paths across development environments
and production packaged installations (%LOCALAPPDATA%\\TTS-Studio).
"""

import os
import sys

def get_base_dir() -> str:
    """
    Returns the root base directory for user data (%LOCALAPPDATA%\TTS-Studio).
    """
    local_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    base_path = os.path.join(local_appdata, "TTS-Studio")
    os.makedirs(base_path, exist_ok=True)
    return base_path

def get_app_dir() -> str:
    """Returns the bundled application directory containing static assets (voices, configs)."""
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(scripts_dir)

def get_models_dir() -> str:
    path = os.path.join(get_base_dir(), "models")
    os.makedirs(path, exist_ok=True)
    return path

def get_model_dir(model_id: str) -> str:
    clean_id = model_id.lower().replace("-", "").replace("_", "")
    # Check if app-bundled local model dir exists
    app_model_dir = os.path.join(get_app_dir(), "models", clean_id)
    if os.path.exists(app_model_dir) and len(os.listdir(app_model_dir)) > 0:
        return app_model_dir

    path = os.path.join(get_models_dir(), clean_id)
    os.makedirs(path, exist_ok=True)
    return path

def get_voices_dir() -> str:
    # Look in app dir first for static bundled reference voices
    path = os.path.join(get_app_dir(), "voices")
    if not os.path.exists(path):
        path = os.path.join(get_base_dir(), "voices")
    os.makedirs(path, exist_ok=True)
    return path

def get_outputs_dir() -> str:
    path = os.path.join(get_base_dir(), "outputs")
    os.makedirs(path, exist_ok=True)
    return path

def get_logs_dir() -> str:
    path = os.path.join(get_base_dir(), "logs")
    os.makedirs(path, exist_ok=True)
    return path

def get_cache_dir() -> str:
    path = os.path.join(get_base_dir(), "cache")
    os.makedirs(path, exist_ok=True)
    return path

def get_config_dir() -> str:
    # Look in app dir first for bundled configs
    path = os.path.join(get_app_dir(), "configs")
    if not os.path.exists(path):
        path = os.path.join(get_base_dir(), "configs")
    os.makedirs(path, exist_ok=True)
    return path

def get_runtimes_dir() -> str:
    path = os.path.join(get_base_dir(), "runtimes")
    os.makedirs(path, exist_ok=True)
    return path

def get_isolated_venv_python(model_id: str) -> str:
    clean_id = model_id.lower().replace("-", "").replace("_", "")
    venv_name = f".venv_{clean_id}"
    return os.path.join(get_base_dir(), venv_name, "Scripts", "python.exe")
