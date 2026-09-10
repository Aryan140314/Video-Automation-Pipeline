"""
F5-TTS Isolated Subprocess Runner — v1.4.0
==========================================
Runs F5-TTS inside a dedicated, isolated Python process.
Uses local weights from AppData\\Local\\TTS-Studio\\models and AppData\\Local\\TTS-Studio\\cache\\huggingface.
Configures PyTorch CUDA backend to prevent cuDNN CUDNN_STATUS_INTERNAL_ERROR on Windows.
Communicates via JSON stdin/stdout lines with ASCII/UTF-8 safety.

FIXES (v1.4.0):
  - Bug 1.1: Vocos now loads from local models/f5tts/vocos/ first, falling back to HF cache.
  - Bug 1.2: vocab_file resolved via f5_tts package location (no more .venv hardcoding).
  - Bug 1.3: All stdout writes are flushed immediately; non-JSON progress lines are suppressed
             to stderr so the parent readline() loop never blocks on intermediate tqdm output.
"""

import os
import sys
import glob
import types
import warnings
warnings.filterwarnings("ignore")

# Stub Trainer to prevent training dependencies from blowing up during pure inference
trainer_stub = types.ModuleType("f5_tts.model.trainer")
trainer_stub.Trainer = None
sys.modules["f5_tts.model.trainer"] = trainer_stub

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

# Ensure ffmpeg in PATH
try:
    import imageio_ffmpeg
    ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    if ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
except Exception:
    pass

from path_resolver import configure_hf_environment, get_model_dir, get_default_voice_path
configure_hf_environment()

import json
import torch
import soundfile as sf

# FIX FOR WINDOWS CUDA CUDNN_STATUS_INTERNAL_ERROR in F.conv1d
if torch.cuda.is_available():
    torch.backends.cudnn.enabled = False
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

# Redirect tqdm & progress output to stderr so stdout stays JSON-only
# This prevents pipe readline() deadlocks in the parent (Bug 1.3)
import io
_STDERR_SINK = sys.stderr

try:
    from tqdm import tqdm as _orig_tqdm
    class _SilentTqdm(_orig_tqdm):
        def __init__(self, *args, **kwargs):
            kwargs.setdefault("file", _STDERR_SINK)
            super().__init__(*args, **kwargs)
    import tqdm as _tqdm_mod
    _tqdm_mod.tqdm = _SilentTqdm
except Exception:
    pass


def _load_vocos_local_or_hf(vocos_local_dir: str, device: str):
    """
    Bug 1.1 fix: Load Vocos from local models/f5tts/vocos/ first.
    Falls back to HuggingFace pretrained download only if local not found.
    """
    from vocos import Vocos

    config_path = os.path.join(vocos_local_dir, "config.yaml")
    if os.path.isfile(config_path):
        try:
            vocoder = Vocos.from_hparams(config_path)
            # Look for checkpoint
            checkpoint_candidates = glob.glob(os.path.join(vocos_local_dir, "*.bin")) + \
                                    glob.glob(os.path.join(vocos_local_dir, "pytorch_model.bin"))
            if checkpoint_candidates:
                import torch as _torch
                state = _torch.load(checkpoint_candidates[0], map_location=device, weights_only=True)
                vocoder.load_state_dict(state, strict=False)
            vocoder = vocoder.to(device)
            sys.stderr.write(f"[f5tts] Vocos loaded from local: {vocos_local_dir}\n")
            sys.stderr.flush()
            return vocoder
        except Exception as local_err:
            sys.stderr.write(f"[f5tts] Local Vocos load failed ({local_err}), falling back to HF...\n")
            sys.stderr.flush()

    # Fallback: HuggingFace pretrained (works if cache exists)
    vocoder = Vocos.from_pretrained("charactr/vocos-mel-24khz")
    return vocoder.to(device)


def main():
    try:
        sys.stdout.write("LOADING\n")
        sys.stdout.flush()

        from huggingface_hub import hf_hub_download
        from f5_tts.model.backbones.dit import DiT
        from f5_tts.infer.utils_infer import load_model, preprocess_ref_audio_text, infer_process
        import f5_tts

        device = "cuda" if torch.cuda.is_available() else "cpu"

        # 1. Resolve F5-TTS checkpoint path
        model_cls = DiT
        model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)

        f5_model_dir = get_model_dir("f5tts")
        safetensors_files = glob.glob(os.path.join(f5_model_dir, "**", "*.safetensors"), recursive=True)

        if safetensors_files:
            ckpt_path = safetensors_files[0]
        else:
            try:
                ckpt_path = hf_hub_download(repo_id="SWivid/F5-TTS", filename="F5TTS_v1_Base/model_1250000.safetensors", local_files_only=True)
            except Exception:
                ckpt_path = hf_hub_download(repo_id="SWivid/F5-TTS", filename="F5TTS_v1_Base/model_1250000.safetensors")

        # Bug 1.2 fix: resolve vocab_file from f5_tts package install location (no .venv hardcoding)
        vocab_file = os.path.join(os.path.dirname(f5_tts.__file__), "infer", "examples", "vocab.txt")
        if not os.path.exists(vocab_file):
            # Last-resort scan across site-packages
            for sp in sys.path:
                candidate = os.path.join(sp, "f5_tts", "infer", "examples", "vocab.txt")
                if os.path.exists(candidate):
                    vocab_file = candidate
                    break

        sys.stderr.write(f"vocab : {vocab_file}\n")
        sys.stderr.write(f"token : custom\n")
        sys.stderr.write(f"model : {ckpt_path}\n")
        sys.stderr.flush()

        ema_model = load_model(model_cls, model_cfg, ckpt_path, mel_spec_type="vocos", vocab_file=vocab_file, device=device)

        # Bug 1.1 fix: load Vocos from local dir first
        vocos_local_dir = os.path.join(f5_model_dir, "vocos")
        vocoder = _load_vocos_local_or_hf(vocos_local_dir, device)

        sys.stdout.write("READY\n")
        sys.stdout.flush()

        while True:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                text = data.get("text", "")
                ref_audio = data.get("ref_audio", "")
                output_path = data.get("output_path", "")
                ref_text = data.get("ref_text", "")

                if not ref_audio or not os.path.exists(ref_audio):
                    ref_audio = get_default_voice_path() or ""

                # If reference text is empty, check for companion txt file or fallback
                if not ref_text and ref_audio:
                    txt_candidate = os.path.splitext(ref_audio)[0] + ".txt"
                    if os.path.exists(txt_candidate):
                        try:
                            with open(txt_candidate, "r", encoding="utf-8") as tf:
                                ref_text = tf.read().strip()
                        except Exception:
                            pass
                if not ref_text:
                    ref_text = "In the realm of voice cloning, precision and clarity define the narrative."

                # Preprocess reference audio
                ref_audio_clean, ref_text_clean = preprocess_ref_audio_text(ref_audio, ref_text)

                # Run inference — all tqdm goes to stderr via the silencer above
                final_wave, final_sample_rate, _ = infer_process(
                    ref_audio_clean,
                    ref_text_clean,
                    text,
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

                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                sf.write(output_path, final_wave, final_sample_rate)

                if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                    sys.stdout.write(json.dumps({"success": True, "backend": "f5tts-clone"}) + "\n")
                else:
                    sys.stdout.write(json.dumps({"error": "Output file not generated or too small."}) + "\n")
                sys.stdout.flush()

            except Exception as e:
                import traceback
                traceback.print_exc(file=sys.stderr)
                sys.stdout.write(json.dumps({"error": f"F5-TTS generation error: {str(e)}"}) + "\n")
                sys.stdout.flush()

    except Exception as init_err:
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stdout.write(json.dumps({"error": f"F5-TTS runner init error: {str(init_err)}"}) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
