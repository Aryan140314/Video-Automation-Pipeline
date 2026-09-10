import os, sys, traceback

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from path_resolver import configure_hf_environment
configure_hf_environment()

try:
    print("Testing Vocos loading directly...", flush=True)
    from vocos import Vocos
    vocoder = Vocos.from_pretrained("charactr/vocos-mel-24khz")
    print("Vocos loaded successfully!", flush=True)
except Exception as e:
    traceback.print_exc()
