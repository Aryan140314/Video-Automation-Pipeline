"""
TTS Studio — Runtime Manager Module
====================================
Implements Master Specification Section 26:
  - Detects active Python & PyTorch model runtimes (main vs isolated environments)
  - Selects GPU (CUDA) or CPU device based on hardware auto-discovery
  - Manages isolated subprocess lifecycle for incompatible model environments
  - Reports runtime status, VRAM footprint, progress, and execution errors
  - Prevents incompatible model runtimes from interfering with each other
"""

import os
import sys
import json
import time
import subprocess
import torch

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(WORKSPACE_ROOT, "scripts")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from path_resolver import get_base_dir
from hardware_detector import inspect_hardware

RUNTIMES_MANIFEST = {
    "f5tts": {
        "runtime_type": "main",
        "venv_dir": ".venv",
        "runner_script": None,
        "cuda_supported": True,
        "cpu_supported": True,
    },
    "chatterbox": {
        "runtime_type": "main",
        "venv_dir": ".venv",
        "runner_script": None,
        "cuda_supported": True,
        "cpu_supported": True,
    },
    "fishspeech": {
        "runtime_type": "isolated",
        "venv_dir": ".venv_fishspeech",
        "runner_script": os.path.join(SCRIPTS_DIR, "isolated_fishspeech_runner.py"),
        "cuda_supported": True,
        "cpu_supported": True,
    },
    "omnivoice": {
        "runtime_type": "isolated",
        "venv_dir": ".venv_omnivoice",
        "runner_script": os.path.join(SCRIPTS_DIR, "isolated_omnivoice_runner.py"),
        "cuda_supported": True,
        "cpu_supported": True,
    },
    "cosyvoice": {
        "runtime_type": "isolated",
        "venv_dir": ".venv_cosyvoice",
        "runner_script": os.path.join(SCRIPTS_DIR, "isolated_cosyvoice_runner.py"),
        "cuda_supported": True,
        "cpu_supported": True,
    },
    "xttsv2": {
        "runtime_type": "isolated",
        "venv_dir": ".venv_xtts",
        "runner_script": os.path.join(SCRIPTS_DIR, "isolated_xtts_runner.py"),
        "cuda_supported": True,
        "cpu_supported": True,
    },
    "indextts2": {
        "runtime_type": "isolated",
        "venv_dir": ".venv_indextts2",
        "runner_script": os.path.join(SCRIPTS_DIR, "isolated_indextts2_runner.py"),
        "cuda_supported": True,
        "cpu_supported": True,
    },
}

class RuntimeManager:
    def __init__(self):
        self.hardware = inspect_hardware()

    def get_runtime_info(self, model_id: str) -> dict:
        """Returns runtime execution details for a given model ID."""
        from path_resolver import get_isolated_venv_python, get_runtime_dir, normalize_model_id

        canonical_id = normalize_model_id(model_id)
        info = RUNTIMES_MANIFEST.get(canonical_id, {
            "runtime_type": "main",
            "venv_dir": ".venv",
            "runner_script": None,
            "cuda_supported": True,
            "cpu_supported": True,
        })

        # Use production path_resolver — NEVER use WORKSPACE_ROOT for venv paths
        python_exe = get_isolated_venv_python(canonical_id)
        runtime_dir = get_runtime_dir(canonical_id)

        # For "main" runtime (f5tts, chatterbox), the process uses the current Python interpreter
        if info.get("runtime_type") == "main":
            python_exe = sys.executable
            exists = True
        else:
            exists = os.path.exists(python_exe)

        return {
            "model_id": canonical_id,
            "runtime_type": info.get("runtime_type", "main"),
            "venv_path": runtime_dir,
            "python_exe": python_exe,
            "environment_exists": exists,
            "device": self.select_device(info),
            "runner_script": info.get("runner_script")
        }


    def select_device(self, runtime_info: dict) -> str:
        """Selects CUDA or CPU based on hardware probe and model capabilities."""
        if self.hardware["cuda_available"] and runtime_info.get("cuda_supported", True):
            return "CUDA"
        return "CPU"

    def execute_isolated_runner(
        self,
        model_id: str,
        text: str,
        reference_voice: str | None,
        output_path: str,
        timeout_sec: int = 600
    ) -> dict:
        """
        Executes zero-shot synthesis inside an isolated Python virtual environment process.
        """
        r_info = self.get_runtime_info(model_id)
        runner_script = r_info["runner_script"]
        python_exe = r_info["python_exe"]

        if not os.path.exists(runner_script):
            return {
                "model": model_id,
                "backend": "DEPENDENCY_MISSING",
                "error": f"Runner script missing: {runner_script}"
            }

        cmd = [python_exe, runner_script, "--text", text, "--output_path", output_path]
        if reference_voice:
            cmd.extend(["--ref_audio", reference_voice])

        t0 = time.time()
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                cwd=WORKSPACE_ROOT,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )
            elapsed = round(time.time() - t0, 3)

            # Parse JSON output from last line of stdout
            out_lines = [l.strip() for l in res.stdout.strip().split("\n") if l.strip()]
            for line in reversed(out_lines):
                if line.startswith("{") and line.endswith("}"):
                    try:
                        data = json.loads(line)
                        data["wall_time"] = elapsed
                        return data
                    except Exception:
                        pass

            return {
                "model": model_id,
                "backend": f"{model_id}-error",
                "error": f"Process finished without valid JSON. stderr: {res.stderr[-300:]}",
                "wall_time": elapsed
            }

        except subprocess.TimeoutExpired:
            return {
                "model": model_id,
                "backend": "timeout",
                "error": f"Subprocess timed out after {timeout_sec}s",
                "wall_time": timeout_sec
            }
        except Exception as err:
            return {
                "model": model_id,
                "backend": "exception",
                "error": str(err),
                "wall_time": round(time.time() - t0, 3)
            }

_RUNTIME_MANAGER_SINGLETON = None

def get_runtime_manager() -> RuntimeManager:
    global _RUNTIME_MANAGER_SINGLETON
    if _RUNTIME_MANAGER_SINGLETON is None:
        _RUNTIME_MANAGER_SINGLETON = RuntimeManager()
    return _RUNTIME_MANAGER_SINGLETON
