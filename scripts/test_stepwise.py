import sys, traceback
try:
    print("Testing line by line:", flush=True)
    import os
    print("1 os ok", flush=True)
    import torch
    print("2 torch ok", flush=True)
    import soundfile
    print("3 soundfile ok", flush=True)
    import f5_tts
    print("4 f5_tts ok", flush=True)
    from f5_tts.model import CFM, DiT, UNetT
    print("5 f5 model ok", flush=True)
    from vocos import Vocos
    print("6 vocos ok", flush=True)
    from f5_tts.model.utils import get_tokenizer
    print("7 tokenizer ok", flush=True)
    from f5_tts.infer.utils_infer import load_model, preprocess_ref_audio_text, infer_process
    print("8 utils_infer ok", flush=True)
except Exception as e:
    traceback.print_exc()
