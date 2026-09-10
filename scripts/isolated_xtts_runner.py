import os
import sys
import time
import json
import argparse
import wave
import torch
import transformers.pytorch_utils

# Set up path resolver for consistent voice/model path resolution
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

try:
    from path_resolver import configure_hf_environment, get_default_voice_path
    configure_hf_environment()
except Exception:
    def get_default_voice_path():
        return None

if torch.cuda.is_available():
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

if not hasattr(transformers.pytorch_utils, 'isin_mps_friendly'):
    def isin_mps_friendly(elements, test_elements):
        return torch.isin(elements, test_elements)
    transformers.pytorch_utils.isin_mps_friendly = isin_mps_friendly

import soundfile as sf
def custom_load_audio(audiopath, sampling_rate=22050):
    data, sr = sf.read(audiopath)
    audio = torch.tensor(data, dtype=torch.float32)
    if audio.ndim == 1:
        audio = audio.unsqueeze(0)
    elif audio.ndim == 2 and audio.shape[0] > audio.shape[1]:
        audio = audio.T
    if sr != sampling_rate:
        import torchaudio.transforms as T
        resampler = T.Resample(sr, sampling_rate)
        audio = resampler(audio)
    return audio

import TTS.tts.models.xtts
TTS.tts.models.xtts.load_audio = custom_load_audio

def main():
    try:
        from huggingface_hub import snapshot_download
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts

        appdata = os.environ.get("LOCALAPPDATA", os.path.join(os.path.expanduser("~"), "AppData", "Local"))
        model_dir = os.path.join(appdata, "TTS-Studio", "models", "xttsv2")
        os.makedirs(model_dir, exist_ok=True)

        config_path = os.path.join(model_dir, 'config.json')
        model_path = os.path.join(model_dir, 'model.pth')
        if not os.path.isfile(config_path) or not os.path.isfile(model_path):
            sys.stdout.write(json.dumps({"error": f"XTTS-v2 weights not found: {model_dir}"}) + "\n")
            sys.stdout.flush()
            sys.exit(1)

        sys.stdout.write("LOADING\n")
        sys.stdout.flush()

        config = XttsConfig()
        config.load_json(os.path.join(model_dir, "config.json"))
        model = Xtts.init_from_config(config)
        model.load_checkpoint(config, checkpoint_dir=model_dir, use_deepspeed=False, eval=True)

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)

        sys.stdout.write("READY\n")
        sys.stdout.flush()

        while True:
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                req = json.loads(line)
            except Exception:
                continue

            text = req.get("text", "")
            ref_audio = req.get("ref_audio", "")
            output_path = req.get("output_path", "")

            start_time = time.time()
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

            try:
                ref_voice = ref_audio if ref_audio and os.path.exists(ref_audio) else None
                if not ref_voice:
                    # Bug 1.4 fix: use path_resolver instead of fragile relative navigation
                    ref_voice = get_default_voice_path()

                gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[ref_voice])

                out = model.inference(
                    text=text,
                    language="en",
                    gpt_cond_latent=gpt_cond_latent,
                    speaker_embedding=speaker_embedding,
                    temperature=0.7,
                )

                sf.write(output_path, out["wav"], 24000)

                gen_time = round(time.time() - start_time, 4)
                duration = 0.0
                if os.path.exists(output_path):
                    with wave.open(output_path, "r") as wf:
                        duration = round(wf.getnframes() / float(wf.getframerate()), 2)
                file_size_kb = round(os.path.getsize(output_path) / 1024, 2)
                rtf = round(gen_time / max(duration, 0.1), 4)

                result = {
                    "model": "xttsv2",
                    "backend": "xttsv2-native",
                    "cloning_active": bool(ref_audio),
                    "gen_time": gen_time,
                    "duration": duration,
                    "rtf": rtf,
                    "file_size_kb": file_size_kb,
                    "output_path": output_path,
                    "device": device
                }
                sys.stdout.write(json.dumps(result) + "\n")
                sys.stdout.flush()
                
            except Exception as e:
                err_res = {
                    "model": "xttsv2",
                    "backend": "xttsv2-error",
                    "error": str(e),
                    "gen_time": round(time.time() - start_time, 4),
                    "output_path": output_path
                }
                sys.stdout.write(json.dumps(err_res) + "\n")
                sys.stdout.flush()

    except Exception as fatal_e:
        err_res = {"error": f"Fatal runner error: {str(fatal_e)}"}
        sys.stdout.write(json.dumps(err_res) + "\n")
        sys.stdout.flush()
        sys.exit(1)

if __name__ == "__main__":
    main()
