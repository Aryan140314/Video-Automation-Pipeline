import sys, traceback
try:
    print("Testing x_transformers and modules:", flush=True)
    import torch
    print("torch ok", flush=True)
    import x_transformers
    print("x_transformers ok", flush=True)
    from x_transformers.x_transformers import RotaryEmbedding
    print("RotaryEmbedding ok", flush=True)
    import f5_tts.model.modules
    print("f5 modules ok", flush=True)
except Exception:
    traceback.print_exc()
