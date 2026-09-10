"""
TTS Studio All Backends Verification Script
===========================================
Tests all 3 active TTS models end-to-end:
1. F5-TTS
2. Chatterbox Turbo
3. XTTS-v2
"""

import os
import sys
import time

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from path_resolver import get_default_voice_path, get_outputs_dir
from tts_adapters import get_adapter

def test_models():
    ref_voice = get_default_voice_path()
    output_dir = get_outputs_dir()
    os.makedirs(output_dir, exist_ok=True)
    
    print("============================================================", flush=True)
    print("TTS STUDIO MULTI-MODEL SYNTHESIS VERIFICATION", flush=True)
    print(f"Reference Voice: {ref_voice}", flush=True)
    print(f"Output Directory: {output_dir}", flush=True)
    print("============================================================\n", flush=True)

    models_to_test = ["chatterbox", "f5tts", "xttsv2"]
    
    for model_id in models_to_test:
        print(f"\n>>> TESTING MODEL: {model_id.upper()} <<<", flush=True)
        try:
            adapter = get_adapter(model_id)
            out_file = os.path.join(output_dir, f"verify_{model_id}.wav")
            t0 = time.time()
            res = adapter.generate(
                text=f"Testing high-fidelity offline voice cloning for {adapter.model_name}.",
                reference_voice=ref_voice,
                output_path=out_file
            )
            elapsed = round(time.time() - t0, 2)
            print(f"Status: SUCCESS in {elapsed}s", flush=True)
            print(f"Result: {res}\n", flush=True)
        except Exception as e:
            print(f"Status: FAILED with error: {e}\n", flush=True)

if __name__ == "__main__":
    test_models()
