"""
TTS Studio Voice Manager Module
===============================
Indexes zero-shot reference voice assets in voices/, extracts audio metadata
using python's wave standard library, and maps voice categories to exact WAV files
without altering or modifying any source audio data.
"""

import os
import sys
import glob
import wave

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from path_resolver import get_voices_dir

class VoiceManager:
    def __init__(self):
        self._index_cache = None

    def get_voices_dir(self) -> str:
        return get_voices_dir()

    def inspect_wav_file(self, file_path: str) -> dict:
        """
        Reads WAV file headers without loading full audio buffers.
        Returns duration, sample_rate, channels, bit_depth, and size.
        """
        file_size = os.path.getsize(file_path)
        duration = 0.0
        sample_rate = 0
        channels = 0
        bit_depth = 16

        try:
            with wave.open(file_path, "rb") as wf:
                channels = wf.getnchannels()
                sample_rate = wf.getframerate()
                sample_width = wf.getsampwidth()
                n_frames = wf.getnframes()
                bit_depth = sample_width * 8
                if sample_rate > 0:
                    duration = round(n_frames / float(sample_rate), 2)
        except Exception:
            duration = round(file_size / (44100 * 2), 2)

        return {
            "duration": duration,
            "sample_rate": sample_rate,
            "channels": channels,
            "bit_depth": bit_depth,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2)
        }

    def index_voices(self, force_refresh: bool = False) -> list[dict]:
        """
        Indexes all WAV files in voices/ and subdirectories.
        """
        if self._index_cache is not None and not force_refresh:
            return self._index_cache

        voices_root = self.get_voices_dir()
        indexed = []

        if os.path.exists(voices_root):
            for root, _, files in os.walk(voices_root):
                for file in files:
                    if file.lower().endswith(".wav"):
                        full_path = os.path.join(root, file)
                        rel_dir = os.path.relpath(root, voices_root)
                        category = "General" if rel_dir == "." else rel_dir
                        
                        meta = self.inspect_wav_file(full_path)
                        indexed.append({
                            "category": category,
                            "filename": file,
                            "full_path": full_path,
                            "relative_path": os.path.relpath(full_path, WORKSPACE_ROOT),
                            "duration_sec": meta["duration"],
                            "sample_rate": meta["sample_rate"],
                            "channels": meta["channels"],
                            "bit_depth": meta["bit_depth"],
                            "file_size_bytes": meta["file_size_bytes"],
                            "file_size_mb": meta["file_size_mb"],
                            "format": "WAV (PCM)"
                        })

        self._index_cache = indexed
        return indexed

    def get_categories(self) -> list[str]:
        indexed = self.index_voices()
        categories = sorted(list(set(item["category"] for item in indexed)))
        return categories

    def resolve_category_wav(self, category_name: str) -> str | None:
        """
        Resolves a category name to the exact reference WAV path.
        """
        if not category_name:
            return None

        # Check direct path
        if os.path.isabs(category_name) and os.path.exists(category_name):
            return category_name

        indexed = self.index_voices()
        
        # 1. Exact category match
        for item in indexed:
            if item["category"].lower() == category_name.lower():
                return item["full_path"]

        # 2. Filename match
        for item in indexed:
            if item["filename"].lower() == category_name.lower():
                return item["full_path"]

        return None

_VOICE_MANAGER_SINGLETON = None

def get_voice_manager() -> VoiceManager:
    global _VOICE_MANAGER_SINGLETON
    if _VOICE_MANAGER_SINGLETON is None:
        _VOICE_MANAGER_SINGLETON = VoiceManager()
    return _VOICE_MANAGER_SINGLETON
