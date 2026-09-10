"""
TTS Studio Model Lifecycle & Manager Module — v1.1.0
=====================================================
Manages model installation states, manifest parsing, download triggers,
verification routines, VRAM unloads, and smoke tests across all 7 TTS architectures.

FIXED v1.1.0:
  - get_model_status() now checks required_files from manifest (was always returning READY)
  - download_model() uses file-by-file downloads from manifest (no snapshot_download)
  - HF_HOME configured to production path before any HF imports
  - Concurrent download protection (no re-entry on same model)
"""

import os
import sys
import json
import shutil
import time

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

# Configure HF environment before importing anything HF-related
from path_resolver import (
    configure_hf_environment,
    get_config_dir,
    get_models_dir,
    get_model_dir,
    get_base_dir,
    normalize_model_id,
    get_isolated_venv_python,
    get_runtime_dir,
)
configure_hf_environment()

from downloader import ResumableDownloader


class ModelLifecycleManager:
    """
    Manages the full lifecycle of all 7 TTS models:
    - Status: NOT_INSTALLED → DOWNLOADING → VERIFYING → READY | CORRUPTED | DEPENDENCY_MISSING
    """

    def __init__(self):
        self.downloader = ResumableDownloader()
        self._download_status: dict = {}  # model_id -> progress_dict
        self._downloading: set = set()   # models currently being downloaded
        self._load_manifest()

    def _load_manifest(self) -> None:
        """Load model_manifest.json from app configs directory."""
        manifest_path = os.path.join(get_config_dir(), "model_manifest.json")
        if not os.path.exists(manifest_path):
            manifest_path = os.path.join(WORKSPACE_ROOT, "configs", "model_manifest.json")

        with open(manifest_path, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

    def get_manifest(self) -> dict:
        """Returns all model entries from manifest."""
        return self.manifest.get("models", {})

    def get_model_info(self, model_id: str) -> dict | None:
        """Returns manifest entry for model_id (handles aliases/normalization)."""
        canonical = normalize_model_id(model_id)
        models = self.get_manifest()
        # Try canonical ID first
        if canonical in models:
            return models[canonical]
        # Fallback: direct lookup
        if model_id.lower() in models:
            return models[model_id.lower()]
        return None

    def _check_required_files(self, model_id: str, info: dict) -> bool:
        """
        Returns True only if ALL required_files declared in manifest exist on disk
        in the managed model directory with non-zero size.
        """
        canonical = normalize_model_id(model_id)
        model_dir = get_model_dir(canonical)
        required = info.get("required_files", [])

        if not required:
            # No required_files declared — fall back to checking if dir has any content
            return os.path.isdir(model_dir) and len(os.listdir(model_dir)) > 0

        for rel_path in required:
            full_path = os.path.join(model_dir, rel_path)
            if not os.path.exists(full_path) or os.path.getsize(full_path) < 1000:
                return False
        return True

    def get_model_status(self, model_id: str) -> str:
        """
        Returns the current lifecycle status for a model:
          NOT_INSTALLED     — model weights not found in managed storage
          DOWNLOADING       — download in progress
          READY             — all required files present and verified
          CORRUPTED         — files present but too small / incomplete
          DEPENDENCY_MISSING — isolated venv not set up
        """
        canonical = normalize_model_id(model_id)
        info = self.get_model_info(model_id)
        if not info:
            return "UNKNOWN"

        # 1. Active download?
        if canonical in self._download_status:
            state = self._download_status[canonical].get("state", "")
            if state == "DOWNLOADING":
                return "DOWNLOADING"
            if state == "DOWNLOAD_FAILED":
                return "DOWNLOAD_FAILED"

        # 2. Check whether required files exist
        if not self._check_required_files(canonical, info):
            return "NOT_INSTALLED"

        # 3. For isolated runtime models, check that venv exists
        if info.get("runtime") == "isolated":
            venv_python = get_isolated_venv_python(canonical)
            if not os.path.exists(venv_python):
                return "DEPENDENCY_MISSING"

        return "READY"

    def verify_model(self, model_id: str) -> dict:
        """Verifies that all declared required_files exist and are non-trivial in size."""
        canonical = normalize_model_id(model_id)
        info = self.get_model_info(model_id)
        if not info:
            return {"valid": False, "reason": f"Model '{model_id}' not found in manifest."}

        model_dir = get_model_dir(canonical)

        for fspec in info.get("files", []):
            fpath = os.path.join(model_dir, fspec["rel_path"])
            if not os.path.exists(fpath):
                return {"valid": False, "reason": f"Missing file: {fspec['rel_path']}"}
            expected = fspec.get("size_bytes", 0)
            actual = os.path.getsize(fpath)
            if expected > 0 and actual < min(1000, expected):
                return {"valid": False, "reason": f"Truncated/corrupted file: {fspec['rel_path']} ({actual} bytes, expected {expected})"}

        return {"valid": True, "reason": "All weight files present and verified."}

    def smoke_test_model(self, model_id: str, reference_voice: str | None = None) -> dict:
        """Runs a short synthesis smoke test for the given model."""
        from tts_adapters import get_adapter

        info = self.get_model_info(model_id)
        if not info:
            return {"success": False, "error": f"Model '{model_id}' not found in manifest."}

        status = self.get_model_status(model_id)
        if status in ("NOT_INSTALLED", "DEPENDENCY_MISSING"):
            return {"success": False, "error": f"Cannot smoke test — model status: {status}"}

        adapter = get_adapter(model_id)
        test_out = os.path.join(get_base_dir(), "outputs", "test", f"smoke_test_{normalize_model_id(model_id)}.wav")
        os.makedirs(os.path.dirname(test_out), exist_ok=True)

        try:
            res = adapter.generate(
                text="TTS Studio model verification test.",
                reference_voice=reference_voice,
                output_path=test_out
            )
            is_ok = (
                res.get("backend") not in ["DEPENDENCY_MISSING", "none", "f5tts-error", "chatterbox-error"]
                and os.path.exists(test_out)
                and os.path.getsize(test_out) > 1000
            )
            return {
                "success": is_ok,
                "metrics": res,
                "error": None if is_ok else f"Inference failed: backend={res.get('backend')}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def download_model(self, model_id: str, progress_callback=None) -> bool:
        """
        Downloads model weight files to the managed models directory.
        Uses file-by-file direct downloads from manifest URLs — NO snapshot_download.
        Supports resumable downloads and progress callbacks.
        """
        canonical = normalize_model_id(model_id)
        info = self.get_model_info(model_id)
        if not info:
            print(f"[ModelManager] Model '{model_id}' not found in manifest.")
            return False

        if canonical in self._downloading:
            print(f"[ModelManager] Download already in progress for '{canonical}'. Skipping.")
            return False

        self._downloading.add(canonical)
        self._download_status[canonical] = {"state": "DOWNLOADING", "percent": 0.0}

        model_dir = get_model_dir(canonical)
        files = info.get("files", [])

        if not files:
            print(f"[ModelManager] No files declared in manifest for '{canonical}'.")
            self._downloading.discard(canonical)
            self._download_status[canonical] = {"state": "DOWNLOAD_FAILED", "percent": 0.0}
            return False

        total_files = len(files)
        success = True

        for file_idx, fspec in enumerate(files):
            dest_file = os.path.join(model_dir, fspec["rel_path"])
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)

            # Skip if already fully downloaded
            expected_size = fspec.get("size_bytes")
            if os.path.exists(dest_file) and expected_size:
                actual = os.path.getsize(dest_file)
                if actual >= expected_size * 0.99:  # 99% tolerance for rounding
                    print(f"[ModelManager] Already complete: {fspec['rel_path']}")
                    if progress_callback:
                        progress_callback({
                            "state": "DOWNLOADING",
                            "percent": round(100.0 * (file_idx + 1) / total_files, 1),
                            "speed_mbps": 0.0,
                            "downloaded_bytes": actual,
                            "total_bytes": expected_size,
                            "file": fspec["rel_path"],
                            "file_index": file_idx + 1,
                            "total_files": total_files,
                        })
                    continue

            print(f"[ModelManager] Downloading {fspec['rel_path']} from {fspec['url']}")

            def _wrapped_cb(data):
                # Adjust percent to account for multiple files
                local_pct = data.get("percent", 0.0)
                overall_pct = round(
                    ((file_idx / total_files) + (local_pct / 100.0 / total_files)) * 100.0, 1
                )
                self._download_status[canonical] = {
                    "state": "DOWNLOADING",
                    "percent": overall_pct,
                }
                if progress_callback:
                    progress_callback({
                        **data,
                        "percent": overall_pct,
                        "file": fspec["rel_path"],
                        "file_index": file_idx + 1,
                        "total_files": total_files,
                    })

            ok = self.downloader.download_file(
                url=fspec["url"],
                dest_path=dest_file,
                expected_size=expected_size,
                progress_callback=_wrapped_cb,
                repo_id=info.get("repo_id"),
                hf_filename=fspec["rel_path"]
            )

            if not ok:
                print(f"[ModelManager] Failed to download: {fspec['rel_path']}")
                success = False
                break

        self._downloading.discard(canonical)

        if success:
            self._download_status[canonical] = {"state": "READY", "percent": 100.0}
            print(f"[ModelManager] Download complete for '{canonical}'.")
        else:
            self._download_status[canonical] = {"state": "DOWNLOAD_FAILED", "percent": 0.0}

        return success

    def delete_model(self, model_id: str) -> bool:
        """Deletes all downloaded weights for a model from managed storage."""
        canonical = normalize_model_id(model_id)
        model_dir = get_model_dir(canonical)

        if os.path.exists(model_dir):
            try:
                shutil.rmtree(model_dir)
                print(f"[ModelManager] Deleted model dir: {model_dir}")
                # Reset status
                self._download_status.pop(canonical, None)
                return True
            except Exception as e:
                print(f"[ModelManager] Error deleting model dir: {e}")
                return False
        return True  # Already doesn't exist


_MODEL_MANAGER_SINGLETON = None


def get_model_manager() -> ModelLifecycleManager:
    global _MODEL_MANAGER_SINGLETON
    if _MODEL_MANAGER_SINGLETON is None:
        _MODEL_MANAGER_SINGLETON = ModelLifecycleManager()
    return _MODEL_MANAGER_SINGLETON
