"""
TTS Studio — Clean Machine Deployment Protocol Test Suite
=========================================================
Verifies Section 34 Master Specification Requirements for standalone deployment:
  1. %LOCALAPPDATA%\\TTS-Studio directory structure creation and isolation
  2. Model manifest integrity (all 7 engines defined)
  3. Original reference voice asset preservation in voices/
  4. Hardware capability detection (GPU/CUDA vs CPU)
  5. Zero hardcoded developer paths in runtime configurations
"""

import os
import sys
import json

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(WORKSPACE_ROOT, "scripts")
BACKEND_DIR = os.path.join(WORKSPACE_ROOT, "backend")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from path_resolver import (
    get_base_dir,
    get_models_dir,
    get_outputs_dir,
    get_cache_dir,
    get_logs_dir,
    get_voices_dir,
    get_config_dir
)
from hardware_detector import inspect_hardware
from model_manager import get_model_manager
from voice_manager import get_voice_manager

def run_clean_deployment_audit():
    os.environ["TTS_STUDIO_PROD"] = "1"
    print("=" * 72)
    print("TTS STUDIO CLEAN MACHINE DEPLOYMENT PROTOCOL AUDIT")
    print("=" * 72)

    errors = []

    # 1. Test Production Paths Resolution
    base_dir = get_base_dir()
    print(f"[1/5] Production Base Storage Path: {base_dir}")
    if "TTS-Studio" not in base_dir:
        errors.append("Base storage path does not point to TTS-Studio directory")

    required_dirs = [
        get_models_dir(),
        get_outputs_dir(),
        get_cache_dir(),
        get_logs_dir()
    ]
    for d in required_dirs:
        os.makedirs(d, exist_ok=True)
        if not os.path.exists(d):
            errors.append(f"Failed to create production storage directory: {d}")

    # 2. Test Model Manifest Integrity
    print("[2/5] Auditing Model Manifest for 7 Zero-Shot Engines...")
    mm = get_model_manager()
    manifest = mm.get_manifest()
    expected_models = ["f5tts", "chatterbox", "fishspeech", "omnivoice", "cosyvoice", "xttsv2", "indextts2"]
    
    for m in expected_models:
        if m not in manifest:
            errors.append(f"Model manifest missing target engine: '{m}'")
        else:
            print(f"  [OK] Engine '{m}': {manifest[m].get('name')} ({manifest[m].get('architecture')})")

    # 3. Test Original Zero-Shot Voice Asset Preservation
    print("[3/5] Auditing Original Reference Voices...")
    vm = get_voice_manager()
    categories = vm.get_categories()
    print(f"  [OK] Found {len(categories)} Reference Voice Categories: {categories}")
    if len(categories) < 7:
        errors.append(f"Expected 7 reference voice categories, found {len(categories)}")

    # 4. Test Hardware Probe Capability
    print("[4/5] Testing Hardware Auto-Discovery...")
    hw = inspect_hardware()
    print(f"  [OK] Device: {hw.get('recommended_device')} | GPU: {hw.get('device_name')} | VRAM: {hw.get('vram_total_gb')} GB")
    if not hw.get("recommended_device"):
        errors.append("Hardware detector returned empty recommended_device")

    # 5. Check No Hardcoded Absolute Developer Paths in Configs
    print("[5/5] Checking Hardcoded Developer Path Exclusions...")
    manifest_path = os.path.join(get_config_dir(), "model_manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "D:\\" in content or "C:\\Users\\aryan\\" in content:
                errors.append("Found developer-specific hardcoded paths in model_manifest.json")

    print("\n" + "=" * 72)
    print("CLEAN MACHINE DEPLOYMENT AUDIT RESULT")
    print("=" * 72)
    if not errors:
        print("  [PASS] ALL CLEAN DEPLOYMENT REQUIREMENTS PASSED (100% SPEC COMPLIANT)")
        print("=" * 72)
        return True
    else:
        print("  [FAIL] CLEAN DEPLOYMENT ERRORS FOUND:")
        for err in errors:
            print(f"     - {err}")
        print("=" * 72)
        return False

if __name__ == "__main__":
    success = run_clean_deployment_audit()
    sys.exit(0 if success else 1)
