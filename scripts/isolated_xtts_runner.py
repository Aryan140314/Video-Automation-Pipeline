import os
import sys
import time
import json
import argparse
import wave
import torch
import transformers.pytorch_utils

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
    parser = argparse.ArgumentParser(description="XTTS-v2 Isolated Subprocess Runner")
    parser.add_argument("--text", type=str, required=True, help="Text to synthesize")
    parser.add_argument("--ref_audio", type=str, default="", help="Reference speaker audio WAV")
    parser.add_argument("--output_path", type=str, required=True, help="Output WAV file path")
    args = parser.parse_args()

    start_time = time.time()
    os.makedirs(os.path.dirname(os.path.abspath(args.output_path)), exist_ok=True)

    try:
        from huggingface_hub import snapshot_download
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts

        appdata = os.environ.get("LOCALAPPDATA", r"C:\Users\aryan\AppData\Local")
        model_dir = os.path.join(appdata, "TTS-Studio", "models", "xtts_v2")
        os.makedirs(model_dir, exist_ok=True)

        if not os.path.isfile(os.path.join(model_dir, 'config.json')):
            for attempt in range(10):
                try:
                    snapshot_download(repo_id='coqui/XTTS-v2', local_dir=model_dir, ignore_patterns=['*.git*'])
                    if os.path.exists(os.path.join(model_dir, 'config.json')):
                        break
                except Exception as e:
                    time.sleep(3)

        config = XttsConfig()
        config.load_json(os.path.join(model_dir, "config.json"))
        model = Xtts.init_from_config(config)
        model.load_checkpoint(config, checkpoint_dir=model_dir, use_deepspeed=False, eval=True)

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)

        ref_voice = args.ref_audio if args.ref_audio and os.path.exists(args.ref_audio) else r'E:\TTS\voices\Narration\deep_male_narrator.wav'
        gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[ref_voice])

        out = model.inference(
            text=args.text,
            language="en",
            gpt_cond_latent=gpt_cond_latent,
            speaker_embedding=speaker_embedding,
            temperature=0.7,
        )

        sf.write(args.output_path, out["wav"], 24000)

        gen_time = round(time.time() - start_time, 4)
        duration = 0.0
        if os.path.exists(args.output_path):
            with wave.open(args.output_path, "r") as wf:
                duration = round(wf.getnframes() / float(wf.getframerate()), 2)
        file_size_kb = round(os.path.getsize(args.output_path) / 1024, 2)
        rtf = round(gen_time / max(duration, 0.1), 4)

        result = {
            "model": "xttsv2",
            "backend": "xttsv2-native",
            "cloning_active": bool(args.ref_audio),
            "gen_time": gen_time,
            "duration": duration,
            "rtf": rtf,
            "file_size_kb": file_size_kb,
            "output_path": args.output_path,
            "device": device
        }
        print(json.dumps(result))
    except Exception as e:
        err_res = {
            "model": "xttsv2",
            "backend": "xttsv2-error",
            "error": str(e),
            "gen_time": round(time.time() - start_time, 4),
            "output_path": args.output_path
        }
        print(json.dumps(err_res))
        sys.exit(1)

if __name__ == "__main__":
    main()
