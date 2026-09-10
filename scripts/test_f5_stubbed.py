import sys, types, os

# Stub Trainer to prevent training dependencies from blowing up during pure inference
trainer_stub = types.ModuleType("f5_tts.model.trainer")
trainer_stub.Trainer = None
sys.modules["f5_tts.model.trainer"] = trainer_stub

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from path_resolver import configure_hf_environment
configure_hf_environment()

import torch
from huggingface_hub import hf_hub_download
from f5_tts.model import CFM, DiT
from f5_tts.infer.utils_infer import load_model, preprocess_ref_audio_text, infer_process
from vocos import Vocos
import f5_tts, soundfile as sf

print("Loaded F5-TTS modules without trainer!", flush=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
model_cls = DiT
model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)

ckpt_path = hf_hub_download(repo_id="SWivid/F5-TTS", filename="F5TTS_v1_Base/model_1250000.safetensors", local_files_only=True)
vocab_file = os.path.join(WORKSPACE_ROOT, ".venv", "Lib", "site-packages", "f5_tts", "infer", "examples", "vocab.txt")
ema_model = load_model(model_cls, model_cfg, ckpt_path, mel_spec_type="vocos", vocab_file=vocab_file, device=device)
vocoder = Vocos.from_pretrained("charactr/vocos-mel-24khz").to(device)
print("F5-TTS model & Vocos initialized on", device, "!", flush=True)

# Reference audio with reference text
ref_audio = os.path.join(WORKSPACE_ROOT, "voices", "Narration", "deep_male_narrator.wav")
ref_text = "In the realm of voice cloning, precision and clarity define the narrative."

ref_audio_clean, ref_text_clean = preprocess_ref_audio_text(ref_audio, ref_text)
out_file = os.path.join(WORKSPACE_ROOT, "outputs", "f5_final_verify.wav")

print("Starting F5-TTS synthesis...", flush=True)
final_wave, final_sr, _ = infer_process(
    ref_audio_clean,
    ref_text_clean,
    "F5 TTS zero shot voice cloning running completely offline on CUDA with high speed flow matching.",
    ema_model,
    vocoder,
    mel_spec_type="vocos",
    target_rms=0.1,
    cross_fade_duration=0.15,
    nfe_step=32,
    cfg_strength=2.0,
    speed=1.0,
    device=device
)
sf.write(out_file, final_wave, final_sr)
print(f"SUCCESS: Generated speech to {out_file} (size: {os.path.getsize(out_file)} bytes)!", flush=True)
