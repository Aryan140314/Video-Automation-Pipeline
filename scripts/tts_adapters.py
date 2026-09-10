"""
TTS Studio Model Adapters Framework
===================================
Provides a unified interface (TTSModelAdapter) for all supported TTS architectures:
1. F5-TTS (f5tts) — DiT Flow Matching zero-shot voice cloning
2. Chatterbox Turbo (chatterbox) — Diffusion-based zero-shot voice cloning
3. CosyVoice 3 (cosyvoice) — FunAudioLLM 300M Zero-Shot Multilingual Model
4. XTTS-v2 (xttsv2) — Coqui GPT-2 Multi-Speaker Voice Cloning Backend

FIXES (v1.4.0):
  - Bug 1.3: readline() is now done in a background thread with a 180s timeout — prevents
             permanent pipe deadlock when tqdm/progress lines interleave JSON on stdout.
  - Bug 1.4: All hardcoded E:\\TTS paths removed; dynamic path_resolver used instead.
"""

import os
import sys
import time
import wave
import queue
import threading
import json
import subprocess
from abc import ABC, abstractmethod

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

try:
    from path_resolver import get_default_voice_path
except Exception:
    def get_default_voice_path():
        return None


class TTSModelAdapter(ABC):
    """
    Abstract base class for all TTS Studio model adapters.
    Ensures a standard signature across all zero-shot speech engines.
    """

    def __init__(self, model_name: str, model_id: str, default_max_words: int = 60):
        self.model_name = model_name
        self.model_id = model_id
        self.default_max_words = default_max_words

    @abstractmethod
    def load_model(self):
        """Loads and caches the underlying PyTorch model instance."""
        pass

    @abstractmethod
    def prepare_text(self, text: str) -> str:
        """Preprocesses text prompt for neural TTS synthesis."""
        pass

    @abstractmethod
    def generate(
        self,
        text: str,
        reference_voice: str | None,
        output_path: str,
        progress_callback=None
    ) -> dict:
        """
        Executes zero-shot speech synthesis for the model.
        Returns a dict containing metrics: model, backend, cloning_active, gen_time, duration, rtf, file_size_kb, output_path, device.
        """
        pass

    def get_safe_chunk_size(self) -> int:
        """Returns the optimal maximum word count per text chunk for this model."""
        return self.default_max_words

    def get_device(self) -> str:
        """Detects whether PyTorch CUDA is active."""
        try:
            import torch
            return "CUDA" if torch.cuda.is_available() else "CPU"
        except Exception:
            return "CUDA"


class _PersistentProcessManager:
    def __init__(self):
        self.processes = {}
        self.locks = {}

    def _resolve_python(self, venv_name: str) -> str:
        workspace_dir = WORKSPACE_ROOT
        # Bug 1.4 fix: no hardcoded E:\TTS — use sys.executable and dynamic workspace only
        candidates = [
            os.path.join(workspace_dir, venv_name, "Scripts", "python.exe"),
            os.path.join(workspace_dir, ".venv", "Scripts", "python.exe"),
            sys.executable,
        ]
        for c in candidates:
            if c and os.path.exists(c):
                return c
        return sys.executable

    def _resolve_script(self, runner_name: str) -> str:
        workspace_dir = WORKSPACE_ROOT
        # Bug 1.4 fix: no hardcoded E:\TTS — use script location and dynamic workspace only
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), runner_name),
            os.path.join(workspace_dir, "scripts", runner_name),
        ]
        for c in candidates:
            if c and os.path.exists(c):
                return c
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), runner_name)

    def get_process(self, model_id: str, venv_name: str, runner_name: str):
        if model_id not in self.locks:
            self.locks[model_id] = threading.Lock()
        
        with self.locks[model_id]:
            if model_id not in self.processes or self.processes[model_id].poll() is not None:
                venv_python = self._resolve_python(venv_name)
                runner_script = self._resolve_script(runner_name)

                if not os.path.exists(runner_script):
                    print(f"[{model_id}] Runner script not found: {runner_script}")
                    return None

                env = os.environ.copy()
                env["PYTHONHASHSEED"] = "0"
                env["PYTHONUNBUFFERED"] = "1"
                env["PYTHONIOENCODING"] = "utf-8"

                cmd = [venv_python, runner_script]
                print(f"[{model_id}] Launching persistent background runner: {venv_python} {runner_script}")
                
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                    bufsize=1
                )
                
                is_ready = False
                while True:
                    line = proc.stdout.readline()
                    if not line:
                        break
                    if "READY" in line:
                        print(f"[{model_id}] Persistent runner is ready.")
                        is_ready = True
                        break
                    safe_init = line.strip().encode('ascii', errors='replace').decode('ascii')
                    print(f"[{model_id} init] {safe_init}")
                
                if not is_ready or proc.poll() is not None:
                    print(f"[{model_id}] Process failed to reach READY state.")
                    return None

                self.processes[model_id] = proc
            
            return self.processes[model_id], self.locks[model_id]


_PROCESS_MANAGER = _PersistentProcessManager()


def _run_isolated_subprocess(
    model_id: str,
    venv_name: str,
    runner_name: str,
    text: str,
    reference_voice: str | None,
    output_path: str,
    model_name: str,
    device: str
) -> dict:
    """
    Executes an isolated subprocess runner using a persistent daemon to avoid reloading models
    and prevent CUDA thread crashes in multi-threaded servers.
    """
    start_t = time.time()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Bug 1.4 fix: resolve fallback voice via path_resolver — no hardcoded E:\TTS paths
    if reference_voice and os.path.exists(reference_voice):
        ref_wav = reference_voice
    else:
        ref_wav = get_default_voice_path() or ""

    subprocess_success = False
    backend_used = f"{model_id}-native"

    proc_tuple = _PROCESS_MANAGER.get_process(model_id, venv_name, runner_name)
    if proc_tuple is not None:
        proc, lock = proc_tuple
        with lock:
            req = {
                "text": text,
                "ref_audio": ref_wav,
                "output_path": output_path
            }
            try:
                proc.stdin.write(json.dumps(req) + "\n")
                proc.stdin.flush()

                # Bug 1.3 fix: drain stdout in a background thread with a 180s timeout.
                # This prevents readline() from blocking forever on tqdm / non-JSON lines.
                result_queue: queue.Queue = queue.Queue()

                def _drain_stdout():
                    while True:
                        line = proc.stdout.readline()
                        result_queue.put(line)
                        if not line:
                            break
                        stripped = line.strip()
                        if stripped.startswith("{"):
                            # First JSON line is the terminal result — stop draining
                            break

                drain_thread = threading.Thread(target=_drain_stdout, daemon=True)
                drain_thread.start()

                deadline = time.time() + 180  # 3-minute hard cap per synthesis
                while time.time() < deadline:
                    try:
                        line = result_queue.get(timeout=1.0)
                    except queue.Empty:
                        if proc.poll() is not None:
                            print(f"[{model_name}] Subprocess exited during synthesis.")
                            break
                        continue

                    if not line:
                        print(f"[{model_name}] Subprocess stdout closed.")
                        break

                    stripped = line.strip()
                    if not stripped:
                        continue

                    try:
                        data = json.loads(stripped)
                        if "error" not in data and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                            subprocess_success = True
                            backend_used = data.get("backend", f"{model_id}-native")
                        elif "error" in data:
                            print(f"[{model_name}] Runner error: {data['error']}")
                        break
                    except Exception:
                        safe_log = stripped.encode('ascii', errors='replace').decode('ascii')
                        print(f"[{model_name}] {safe_log}")

                if time.time() >= deadline:
                    print(f"[{model_name}] Synthesis timed out after 180s.")

            except Exception as err:
                print(f"[{model_name}] Subprocess communication error: {err}")

    gen_time = round(time.time() - start_t, 4)
    duration = 0.0
    file_size_kb = 0.0
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        file_size_kb = round(os.path.getsize(output_path) / 1024, 2)
        try:
            with wave.open(output_path, "r") as wf:
                duration = round(wf.getnframes() / float(wf.getframerate()), 2)
        except Exception:
            duration = round(len(text.split()) * 0.35, 2)

    return {
        "model": model_id,
        "model_name": model_name,
        "backend": backend_used if subprocess_success else f"{model_id}-error",
        "cloning_active": True,
        "gen_time": gen_time,
        "duration": duration,
        "rtf": round(gen_time / max(duration, 0.1), 4),
        "file_size_kb": file_size_kb,
        "output_path": output_path,
        "device": device
    }


# ─────────────────────────────────────────────────────────────────────────────
# Concrete Adapters for Models
# ─────────────────────────────────────────────────────────────────────────────

class F5TTSAdapter(TTSModelAdapter):
    def __init__(self):
        super().__init__("F5-TTS", "f5tts", default_max_words=60)

    def load_model(self):
        return None

    def prepare_text(self, text: str) -> str:
        from speech_synth_helper import preprocess_tts_text
        return preprocess_tts_text(text)

    def get_safe_chunk_size(self) -> int:
        return 60

    def generate(self, text: str, reference_voice: str | None, output_path: str, progress_callback=None) -> dict:
        text = self.prepare_text(text)
        return _run_isolated_subprocess(
            self.model_id, 
            ".venv", 
            "isolated_f5tts_runner.py", 
            text, 
            reference_voice, 
            output_path, 
            self.model_name, 
            self.get_device()
        )


class ChatterboxAdapter(TTSModelAdapter):
    def __init__(self):
        super().__init__("Chatterbox Turbo", "chatterbox", default_max_words=60)

    def load_model(self):
        return None

    def prepare_text(self, text: str) -> str:
        from speech_synth_helper import preprocess_tts_text
        return preprocess_tts_text(text)

    def get_safe_chunk_size(self) -> int:
        return 60

    def generate(self, text: str, reference_voice: str | None, output_path: str, progress_callback=None) -> dict:
        text = self.prepare_text(text)
        return _run_isolated_subprocess(
            self.model_id, 
            ".venv", 
            "isolated_chatterbox_runner.py", 
            text, 
            reference_voice, 
            output_path, 
            self.model_name, 
            self.get_device()
        )


class CosyVoiceAdapter(TTSModelAdapter):
    def __init__(self):
        super().__init__("CosyVoice 3", "cosyvoice", default_max_words=80)

    def load_model(self):
        return None

    def prepare_text(self, text: str) -> str:
        from speech_synth_helper import preprocess_tts_text
        return preprocess_tts_text(text)

    def get_safe_chunk_size(self) -> int:
        return 80

    def generate(self, text: str, reference_voice: str | None, output_path: str, progress_callback=None) -> dict:
        text = self.prepare_text(text)
        return _run_isolated_subprocess(
            self.model_id, 
            ".venv_cosyvoice", 
            "isolated_cosyvoice_runner.py", 
            text, 
            reference_voice, 
            output_path, 
            self.model_name, 
            self.get_device()
        )


class XTTSv2Adapter(TTSModelAdapter):
    def __init__(self):
        super().__init__("XTTS-v2", "xttsv2", default_max_words=60)

    def load_model(self):
        return None

    def prepare_text(self, text: str) -> str:
        from speech_synth_helper import preprocess_tts_text
        return preprocess_tts_text(text)

    def get_safe_chunk_size(self) -> int:
        return 60

    def generate(self, text: str, reference_voice: str | None, output_path: str, progress_callback=None) -> dict:
        text = self.prepare_text(text)
        return _run_isolated_subprocess(
            self.model_id, 
            ".venv_xtts", 
            "isolated_xtts_runner.py", 
            text, 
            reference_voice, 
            output_path, 
            self.model_name, 
            self.get_device()
        )


# ─────────────────────────────────────────────────────────────────────────────
# Model Adapter Factory & Registry Singleton
# ─────────────────────────────────────────────────────────────────────────────

_ADAPTER_REGISTRY = {
    "f5tts": F5TTSAdapter(),
    "chatterbox": ChatterboxAdapter(),
    "cosyvoice": CosyVoiceAdapter(),
    "xttsv2": XTTSv2Adapter(),
}

def get_adapter(model_id: str) -> TTSModelAdapter:
    """Returns the cached TTSModelAdapter instance for the given model_id."""
    clean_id = model_id.lower().replace("-", "").replace("_", "")
    for key, adapter in _ADAPTER_REGISTRY.items():
        if key == clean_id or key == model_id.lower():
            return adapter
    return _ADAPTER_REGISTRY["f5tts"]
