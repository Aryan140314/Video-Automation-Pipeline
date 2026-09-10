"""
CosyVoice 3 Isolated Subprocess Runner — Patched Version
=========================================================
Key patches applied BEFORE CosyVoice import:
  1. torchaudio.load → soundfile (avoids torchcodec crash)
  2. wetext/ttsfrd import → stubbed out (avoids FST compilation hang)
  3. load_wav → soundfile-based (avoids sr mismatch crash)
"""
import os
import sys
import time
import json
import wave
import torch
import soundfile as sf
import torchaudio

cosy_root = r'E:\TTS\runtimes\CosyVoice'
if cosy_root not in sys.path:
    sys.path.insert(0, cosy_root)
matcha_root = os.path.join(cosy_root, 'third_party', 'Matcha-TTS')
if matcha_root not in sys.path:
    sys.path.insert(0, matcha_root)

# ── PATCH 1: torchaudio.load → soundfile (avoids torchcodec crash) ───────────
def _sf_load(filepath, **kwargs):
    if isinstance(filepath, torch.Tensor):
        return filepath, 16000
    data, sr = sf.read(filepath)
    tensor = torch.from_numpy(data).float()
    if tensor.ndim == 1:
        tensor = tensor.unsqueeze(0)
    elif tensor.ndim == 2 and tensor.shape[0] > tensor.shape[1]:
        tensor = tensor.T
    return tensor, sr

torchaudio.load = _sf_load

# ── PATCH 2: wetext stub (prevents FST compilation hang ≥ 10 min) ───────────
import types, importlib, unittest.mock

class _DummyNormalizer:
    def __init__(self, *a, **kw):
        pass
    def normalize(self, text):
        return text

_wetext_mod = types.ModuleType("wetext")
_wetext_mod.Normalizer = _DummyNormalizer
sys.modules["wetext"] = _wetext_mod

# ── PATCH 3: load_wav via soundfile ──────────────────────────────────────────
def _custom_load_wav(wav, target_sr=16000):
    if isinstance(wav, torch.Tensor):
        speech = wav
        sample_rate = target_sr
    elif isinstance(wav, str):
        data, sample_rate = sf.read(wav)
        speech = torch.from_numpy(data).float()
    else:
        import numpy as np
        data = np.array(wav)
        speech = torch.from_numpy(data).float()
        sample_rate = target_sr

    if speech.ndim == 1:
        speech = speech.unsqueeze(0)
    elif speech.ndim == 2 and speech.shape[0] > speech.shape[1]:
        speech = speech.T

    if sample_rate != target_sr:
        import torchaudio.transforms as T
        resampler = T.Resample(sample_rate, target_sr)
        speech = resampler(speech)

    return speech

import cosyvoice.utils.file_utils
cosyvoice.utils.file_utils.load_wav = _custom_load_wav


def main():
    try:
        from cosyvoice.cli.cosyvoice import CosyVoice

        model_dir = r'E:\TTS\runtimes\CosyVoice\pretrained_models\CosyVoice-300M'
        
        sys.stdout.write("LOADING\n")
        sys.stdout.flush()
        
        cosyvoice_model = CosyVoice(model_dir)
        device = "cuda" if torch.cuda.is_available() else "cpu"

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
                ref_voice = (
                    ref_audio if ref_audio and os.path.exists(ref_audio)
                    else r'E:\TTS\voices\Narration\deep_male_narrator.wav'
                )
                prompt_speech_16k = _custom_load_wav(ref_voice, 16000)

                for i, res in enumerate(cosyvoice_model.inference_zero_shot(
                    text,
                    'This is a prompt speaker voice.',
                    prompt_speech_16k
                )):
                    speech = res['tts_speech'].squeeze(0).cpu().numpy()
                    sf.write(output_path, speech, cosyvoice_model.sample_rate)
                    break

                gen_time = round(time.time() - start_time, 4)
                duration = 0.0
                file_size_kb = 0.0
                if os.path.exists(output_path):
                    file_size_kb = round(os.path.getsize(output_path) / 1024, 2)
                    try:
                        with wave.open(output_path, "r") as wf:
                            duration = round(wf.getnframes() / float(wf.getframerate()), 2)
                    except Exception:
                        pass
                rtf = round(gen_time / max(duration, 0.1), 4)

                result = {
                    "model": "cosyvoice",
                    "backend": "cosyvoice-300m-native",
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
                    "model": "cosyvoice",
                    "backend": "cosyvoice-error",
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
