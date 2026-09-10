import sys, traceback
try:
    print("Testing direct backbone imports:", flush=True)
    import torch
    from f5_tts.model.backbones.dit import DiT
    print("DiT backbone ok!", flush=True)
    from f5_tts.model.cfm import CFM
    print("CFM ok!", flush=True)
    from vocos import Vocos
    print("Vocos ok!", flush=True)
    from f5_tts.model.utils import get_tokenizer
    print("Tokenizer ok!", flush=True)
except Exception as e:
    traceback.print_exc()
