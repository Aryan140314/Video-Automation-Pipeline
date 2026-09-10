import os, sys, traceback

log_f = open(r"E:\TTS\f5_infer_lines.log", "w")

def log(msg):
    log_f.write(msg + "\n")
    log_f.flush()

try:
    log("1: matplotlib Agg")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pylab as plt
    
    log("2: numpy, torch, torchaudio, tqdm")
    import numpy as np
    import torch
    import torchaudio
    import tqdm

    log("3: pydub")
    from pydub import AudioSegment, silence

    log("4: transformers pipeline")
    from transformers import pipeline

    log("5: f5 model utils")
    from f5_tts.model.utils import convert_char_to_pinyin, get_tokenizer

    log("6: all top level imports in utils_infer done")
except Exception as e:
    log(f"Error: {e}")
    traceback.print_exc(file=log_f)
finally:
    log_f.close()
