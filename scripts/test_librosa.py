import sys, traceback
try:
    print("Testing librosa import...", flush=True)
    import librosa
    print("librosa imported successfully!", flush=True)
except Exception:
    traceback.print_exc()
