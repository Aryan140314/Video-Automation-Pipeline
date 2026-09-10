import os, sys, traceback

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

log_f = open(os.path.join(WORKSPACE_ROOT, "f5_step.log"), "w")

def log(msg):
    log_f.write(msg + "\n")
    log_f.flush()

try:
    log("Step 1: configure_hf_environment")
    from path_resolver import configure_hf_environment
    configure_hf_environment()

    log("Step 2: imports")
    import torch
    import soundfile as sf
    from huggingface_hub import hf_hub_download
    from f5_tts.model import CFM, DiT, UNetT
    from f5_tts.infer.utils_infer import load_model, preprocess_ref_audio_text, infer_process
    from vocos import Vocos
    import f5_tts

    log("Step 3: device and model_cfg")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_cls = DiT
    model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)

    log("Step 4: hf_hub_download ckpt")
    ckpt_path = hf_hub_download(repo_id="SWivid/F5-TTS", filename="F5TTS_v1_Base/model_1250000.safetensors")
    log(f"ckpt_path = {ckpt_path}")

    log("Step 5: vocab file")
    vocab_file = os.path.join(WORKSPACE_ROOT, ".venv", "Lib", "site-packages", "f5_tts", "infer", "examples", "vocab.txt")
    log(f"vocab_file = {vocab_file} exists={os.path.exists(vocab_file)}")

    log("Step 6: load_model")
    ema_model = load_model(model_cls, model_cfg, ckpt_path, mel_spec_type="vocos", vocab_file=vocab_file, device=device)
    log("Step 6 done")

    log("Step 7: load vocoder")
    vocoder = Vocos.from_pretrained("charactr/vocos-mel-24khz").to(device)
    log("Step 7 done - ALL SUCCESS")

except Exception as e:
    log(f"ERROR: {e}")
    traceback.print_exc(file=log_f)
    log_f.flush()
finally:
    log_f.close()
