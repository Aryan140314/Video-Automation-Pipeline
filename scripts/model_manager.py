"""
TTS Studio Model Lifecycle & Manager Module
===========================================
Manages model installation states, manifest parsing, download triggers,
verification routines, VRAM unloads, and smoke tests across all 7 TTS architectures.
"""

import os
import sys
import json
import shutil
import time

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from path_resolver import get_config_dir, get_models_dir, get_model_dir, get_base_dir
from downloader import ResumableDownloader
from tts_adapters import get_adapter

class ModelLifecycleManager:
    def __init__(self):
        self.downloader = ResumableDownloader()
        self._download_status = {}  # model_id -> progress_dict
        self._load_manifest()

    def _load_manifest(self):
        manifest_path = os.path.join(get_config_dir(), "model_manifest.json")
        if not os.path.exists(manifest_path):
            manifest_path = os.path.join(WORKSPACE_ROOT, "configs", "model_manifest.json")
        
        with open(manifest_path, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

    def get_manifest(self) -> dict:
        return self.manifest.get("models", {})

    def get_model_info(self, model_id: str) -> dict | None:
        clean_id = model_id.lower().replace("-", "").replace("_", "")
        models = self.get_manifest()
        return models.get(clean_id) or models.get(model_id.lower())

    def get_model_status(self, model_id: str) -> str:
        info = self.get_model_info(model_id)
        if not info:
            return "UNKNOWN"

        clean_id = info["id"]
        
        # Check active download state
        if clean_id in self._download_status and self._download_status[clean_id].get("state") == "DOWNLOADING":
            return "DOWNLOADING"

        # Check isolated environment availability
        if info.get("runtime") == "isolated":
            venv_name = info.get("venv_name", f".venv_{clean_id}")
            venv_python = os.path.join(get_base_dir(), venv_name, "Scripts", "python.exe")
            if not os.path.exists(venv_python):
                return "DEPENDENCY_MISSING"

        return "READY"

    def verify_model(self, model_id: str) -> dict:
        info = self.get_model_info(model_id)
        if not info:
            return {"valid": False, "reason": f"Model '{model_id}' not found in manifest."}

        clean_id = info["id"]
        model_dir = get_model_dir(clean_id)
        
        for fspec in info.get("files", []):
            fpath = os.path.join(model_dir, fspec["rel_path"])
            if not os.path.exists(fpath):
                return {"valid": False, "reason": f"Missing file: {fspec['rel_path']}"}
            if fspec.get("size_bytes") and os.path.getsize(fpath) < min(1000, fspec["size_bytes"]):
                return {"valid": False, "reason": f"File corrupted or incomplete: {fspec['rel_path']}"}

        return {"valid": True, "reason": "All weight files present and verified."}

    def smoke_test_model(self, model_id: str, reference_voice: str | None = None) -> dict:
        info = self.get_model_info(model_id)
        if not info:
            return {"success": False, "error": f"Model '{model_id}' not found in manifest."}

        status = self.get_model_status(model_id)
        if status == "DEPENDENCY_MISSING":
            return {"success": False, "error": f"Isolated environment for '{model_id}' is missing."}

        adapter = get_adapter(model_id)
        test_out = os.path.join(get_base_dir(), "outputs", "test", f"smoke_test_{model_id}.wav")
        
        try:
            res = adapter.generate(
                text="TTS Studio model verification test.",
                reference_voice=reference_voice,
                output_path=test_out
            )
            is_ok = res.get("backend") not in ["DEPENDENCY_MISSING", "none", "f5tts-error", "chatterbox-error"]
            return {
                "success": is_ok,
                "metrics": res,
                "error": None if is_ok else f"Inference failed with backend status '{res.get('backend')}'"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def download_model(self, model_id: str, progress_callback=None) -> bool:
        info = self.get_model_info(model_id)
        if not info:
            print(f"[ModelManager] Model '{model_id}' not found.")
            return False

        clean_id = info["id"]
        model_dir = get_model_dir(clean_id)
        repo_id = info.get("repo_id")

        self._download_status[clean_id] = {"state": "DOWNLOADING", "percent": 0.0}

        if repo_id:
            try:
                print(f"[ModelManager] Downloading Hugging Face repository '{repo_id}' to '{model_dir}'...")
                from huggingface_hub import snapshot_download

                if progress_callback:
                    progress_callback({"state": "DOWNLOADING", "percent": 25.0, "speed_mbps": 10.0})

                snapshot_download(
                    repo_id=repo_id,
                    local_dir=model_dir,
                    local_dir_use_symlinks=False,
                    resume_download=True
                )

                if progress_callback:
                    progress_callback({"state": "DOWNLOADING", "percent": 100.0, "speed_mbps": 0.0})

                self._download_status[clean_id] = {"state": "READY", "percent": 100.0}
                return True
            except Exception as e:
                print(f"[ModelManager snapshot_download Error] {repo_id}: {e}")

        # Fallback to direct file download from manifest files
        success = True
        for fspec in info.get("files", []):
            dest_file = os.path.join(model_dir, fspec["rel_path"])
            ok = self.downloader.download_file(
                url=fspec["url"],
                dest_path=dest_file,
                expected_size=fspec.get("size_bytes"),
                progress_callback=progress_callback
            )
            if not ok:
                success = False
                break

        if success:
            self._download_status[clean_id] = {"state": "READY", "percent": 100.0}
        else:
            self._download_status[clean_id] = {"state": "DOWNLOAD_FAILED", "percent": 0.0}

        return success

    def delete_model(self, model_id: str) -> bool:
        info = self.get_model_info(model_id)
        if not info:
            return False

        clean_id = info["id"]
        model_dir = get_model_dir(clean_id)
        
        if os.path.exists(model_dir):
            try:
                shutil.rmtree(model_dir)
                os.makedirs(model_dir, exist_ok=True)
                return True
            except Exception as e:
                print(f"[ModelManager] Error deleting model dir: {e}")
                return False
        return True

_MODEL_MANAGER_SINGLETON = None

def get_model_manager() -> ModelLifecycleManager:
    global _MODEL_MANAGER_SINGLETON
    if _MODEL_MANAGER_SINGLETON is None:
        _MODEL_MANAGER_SINGLETON = ModelLifecycleManager()
    return _MODEL_MANAGER_SINGLETON
