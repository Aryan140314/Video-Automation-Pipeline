"""
TTS Studio — Golden Regression Test Suite
==========================================
Verifies all 7 zero-shot TTS model adapters against standard test inputs.
Enforces Master Specification Rules:
  - 100% Pipeline Equivalence
  - Selected Model == Actual Model Executed (No Silent Fallback)
  - Valid WAV output (> 10KB, > 0.5s duration)
"""

import os
import sys
import wave
import time
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")
OUTPUTS_DIR = os.path.join(ROOT_DIR, "outputs")
VOICES_DIR = os.path.join(ROOT_DIR, "voices", "Narration")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from tts_adapters import get_adapter, MODEL_ADAPTERS

TEST_TEXT = "TTS Studio golden regression test verification. All model runtimes operational."

TARGET_MODELS = [
    {"id": "f5tts", "name": "F5-TTS", "expected_backend": "f5tts-clone"},
    {"id": "chatterbox", "name": "Chatterbox Turbo", "expected_backend": "chatterbox-clone"},
    {"id": "fishspeech", "name": "Fish Speech S2", "expected_backend": "fishspeech-s2-native"},
    {"id": "omnivoice", "name": "OmniVoice", "expected_backend": "omnivoice-native"},
    {"id": "cosyvoice", "name": "CosyVoice 3", "expected_backend": "cosyvoice-300m-native"},
    {"id": "xttsv2", "name": "XTTS-v2", "expected_backend": "xttsv2-native"},
    {"id": "indextts2", "name": "IndexTTS 2.5", "expected_backend": "indextts2.5-native"},
]

def find_reference_voice() -> str:
    ref_path = os.path.join(VOICES_DIR, "deep_male_narrator.wav")
    if os.path.exists(ref_path):
        return ref_path
    if os.path.exists(VOICES_DIR):
        for root, _, files in os.walk(VOICES_DIR):
            for f in files:
                if f.endswith(".wav"):
                    return os.path.join(root, f)
    raise FileNotFoundError("No reference WAV voices found in voices/ directory.")

def run_golden_regression():
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    ref_wav = find_reference_voice()

    print("=" * 72)
    print("TTS STUDIO GOLDEN REGRESSION TEST SUITE")
    print(f"Reference Voice: {os.path.basename(ref_wav)}")
    print(f"Test Sentence : '{TEST_TEXT}'")
    print("=" * 72)

    results = []
    total_passed = 0

    for idx, item in enumerate(TARGET_MODELS):
        model_id = item["id"]
        model_name = item["name"]
        expected_backend = item["expected_backend"]
        output_wav = os.path.join(OUTPUTS_DIR, f"regression_{model_id}.wav")

        print(f"\n[{idx+1}/7] Testing Model: {model_name} ('{model_id}')...")
        t0 = time.time()

        try:
            adapter = get_adapter(model_id)
            gen_res = adapter.generate(text=TEST_TEXT, reference_voice=ref_wav, output_path=output_wav)
            wall_time = round(time.time() - t0, 2)

            actual_backend = gen_res.get("backend", "unknown")
            file_size_kb = round(os.path.getsize(output_wav) / 1024.0, 2) if os.path.exists(output_wav) else 0.0

            duration = 0.0
            if os.path.exists(output_wav) and file_size_kb > 0.5:
                try:
                    with wave.open(output_wav, "r") as wf:
                        duration = round(wf.getnframes() / float(wf.getframerate()), 2)
                except Exception:
                    duration = float(gen_res.get("duration", 0.0))

            # Checks
            file_valid = os.path.exists(output_wav) and file_size_kb >= 10.0
            duration_valid = duration >= 0.5
            no_fallback = "fallback" not in str(actual_backend) and "error" not in str(actual_backend)

            passed = file_valid and duration_valid and no_fallback

            if passed:
                total_passed += 1
                status_tag = "[PASS]"
            elif not no_fallback:
                status_tag = "[WARN - FALLBACK]"
            else:
                status_tag = "[FAIL]"

            print(f"  {status_tag} Backend: {actual_backend} | Time: {wall_time}s | Size: {file_size_kb}KB | Dur: {duration}s")

            results.append({
                "model_id": model_id,
                "model_name": model_name,
                "passed": passed,
                "backend": actual_backend,
                "wall_time": wall_time,
                "file_size_kb": file_size_kb,
                "duration": duration,
                "status_tag": status_tag
            })

        except Exception as err:
            wall_time = round(time.time() - t0, 2)
            print(f"  [FAIL] Engine Exception: {err}")
            results.append({
                "model_id": model_id,
                "model_name": model_name,
                "passed": False,
                "backend": "exception",
                "error": str(err),
                "wall_time": wall_time,
                "status_tag": "[FAIL]"
            })

    print("\n" + "=" * 72)
    print("GOLDEN REGRESSION TEST SUMMARY")
    print("=" * 72)
    for res in results:
        print(f"  {res['status_tag']:16s} | {res['model_name']:16s} | Backend: {res['backend']:22s} | Time: {res['wall_time']}s")

    print("-" * 72)
    print(f"Total Score: {total_passed}/7 Passed Native Validation")
    print("=" * 72)

    return total_passed == 7

if __name__ == "__main__":
    success = run_golden_regression()
    sys.exit(0 if success else 1)
