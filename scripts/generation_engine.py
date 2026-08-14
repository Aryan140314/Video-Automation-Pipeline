"""
TTS Studio Generation Engine Module
====================================
Bridges synthesis requests to target TTS model adapters, enforcing strict
No Silent Fallback rules and post-processing voice tuning.
"""

import os
import sys
import time

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from path_resolver import get_outputs_dir
from tts_adapters import get_adapter
from voice_manager import get_voice_manager
from model_manager import get_model_manager
from speech_synth_helper import apply_voice_tuning

class GenerationEngine:
    def __init__(self):
        self.vm = get_voice_manager()
        self.mm = get_model_manager()

    def generate(
        self,
        text: str,
        model_id: str = "f5tts",
        voice_category: str | None = None,
        output_path: str | None = None,
        pitch: float = 0.0,
        speed: float = 1.0,
        trim_sec: float | None = None
    ) -> dict:
        """
        Executes zero-shot voice synthesis for the specified model_id.
        STRICT RULE: No Silent Fallback. If model cannot run, returns explicit error status.
        """
        if not text or not text.strip():
            return {
                "status": "error",
                "model": model_id,
                "error": "EMPTY_TEXT",
                "backend": "none"
            }

        # 1. Resolve Reference Voice WAV first if provided
        ref_wav = None
        if voice_category:
            ref_wav = self.vm.resolve_category_wav(voice_category)
            if not ref_wav:
                return {
                    "status": "error",
                    "model": model_id,
                    "error": "VOICE_NOT_FOUND",
                    "backend": "none",
                    "message": f"Reference voice '{voice_category}' not found in voices/"
                }

        # 2. Model Availability & Status Check (No Silent Fallback Rule)
        model_status = self.mm.get_model_status(model_id)
        if model_status == "DEPENDENCY_MISSING":
            return {
                "status": "error",
                "model": model_id,
                "error": "DEPENDENCY_MISSING",
                "backend": "DEPENDENCY_MISSING",
                "message": f"Isolated runtime environment for '{model_id}' is not installed."
            }
        elif model_status == "NOT_INSTALLED":
            return {
                "status": "error",
                "model": model_id,
                "error": "MODEL_NOT_DOWNLOADED",
                "backend": "MODEL_NOT_DOWNLOADED",
                "message": f"Model weights for '{model_id}' are not downloaded."
            }

        # 3. Determine Output Filepath
        adapter = get_adapter(model_id)
        if output_path:
            out_file = output_path
        else:
            model_out_dir = os.path.join(get_outputs_dir(), adapter.model_id)
            os.makedirs(model_out_dir, exist_ok=True)
            out_file = os.path.join(model_out_dir, f"{adapter.model_id}_out_{int(time.time())}.wav")

        # 4. Invoke Model Adapter (Strict Target Execution)
        result = adapter.generate(
            text=text,
            reference_voice=ref_wav,
            output_path=out_file
        )

        # Validate adapter output
        backend_status = result.get("backend", "none")
        if backend_status in ["DEPENDENCY_MISSING", "none", "f5tts-error", "chatterbox-error", "xttsv2-error"]:
            return {
                "status": "error",
                "model": adapter.model_id,
                "model_name": adapter.model_name,
                "backend": backend_status,
                "cloning_active": False,
                "gen_time": result.get("gen_time", 0.0),
                "duration": 0.0,
                "rtf": 0.0,
                "file_size_kb": 0.0,
                "output_path": out_file,
                "device": adapter.get_device(),
                "error": f"Inference execution failed with status: {backend_status}"
            }

        # 5. Optional Post-Processing Voice Tuning (Pitch, Speed, Trim)
        if pitch != 0.0 or speed != 1.0 or trim_sec is not None:
            try:
                tuned = apply_voice_tuning(
                    input_wav=out_file,
                    output_wav=out_file,
                    speed=speed,
                    pitch=pitch,
                    trim_sec=trim_sec
                )
                result["duration"] = tuned["duration"]
                result["file_size_kb"] = tuned["file_size_kb"]
            except Exception as e:
                print(f"[GenerationEngine] Post-processing tuning warning: {e}")

        result["status"] = "success"
        try:
            from synthesis_benchmark import log_synthesis_result
            log_synthesis_result(result)
        except Exception as log_err:
            print(f"[GenerationEngine] Benchmark log warning: {log_err}")
        return result

_GENERATION_ENGINE_SINGLETON = None

def get_generation_engine() -> GenerationEngine:
    global _GENERATION_ENGINE_SINGLETON
    if _GENERATION_ENGINE_SINGLETON is None:
        _GENERATION_ENGINE_SINGLETON = GenerationEngine()
    return _GENERATION_ENGINE_SINGLETON
