import os, sys, traceback

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

log_f = open(os.path.join(WORKSPACE_ROOT, "f5_import_step.log"), "w")

def log(msg):
    log_f.write(msg + "\n")
    log_f.flush()

try:
    log("Importing torch...")
    import torch
    log("Importing soundfile...")
    import soundfile as sf
    log("Importing huggingface_hub...")
    from huggingface_hub import hf_hub_download
    log("Importing vocos...")
    from vocos import Vocos
    log("Importing f5_tts...")
    import f5_tts
    log("Importing f5_tts.model...")
    from f5_tts.model import CFM, DiT, UNetT
    log("Importing f5_tts.infer.utils_infer...")
    from f5_tts.infer.utils_infer import load_model, preprocess_ref_audio_text, infer_process
    log("All imports succeeded!")
except Exception as e:
    log(f"Import error: {e}")
    traceback.print_exc(file=log_f)
finally:
    log_f.close()
