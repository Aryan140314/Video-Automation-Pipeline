import os
import sys
import time
import json
import argparse
import wave
import torch
import numpy as np
import soundfile as sf
from huggingface_hub import snapshot_download

def main():
    parser = argparse.ArgumentParser(description="OmniVoice Isolated Subprocess Runner")
    parser.add_argument("--text", type=str, required=True, help="Text to synthesize")
    parser.add_argument("--ref_audio", type=str, default="", help="Reference speaker audio WAV")
    parser.add_argument("--output_path", type=str, required=True, help="Output WAV file path")
    args = parser.parse_args()

    start_time = time.time()
    os.makedirs(os.path.dirname(os.path.abspath(args.output_path)), exist_ok=True)

    try:
        appdata = os.environ.get("LOCALAPPDATA", r"C:\Users\aryan\AppData\Local")
        model_dir = os.path.join(appdata, "TTS-Studio", "models", "omnivoice")
        os.makedirs(model_dir, exist_ok=True)

        if not os.path.exists(os.path.join(model_dir, "config.json")):
            for attempt in range(5):
                try:
                    snapshot_download("k2-fsa/OmniVoice", local_dir=model_dir, ignore_patterns=["*.git*"])
                    break
                except Exception as err:
                    time.sleep(3)

        from omnivoice import OmniVoice
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = OmniVoice.from_pretrained(model_dir)
        if hasattr(model, "to"):
            model.to(device)

        if args.ref_audio and os.path.exists(args.ref_audio):
            res = model.generate(text=args.text, ref_audio=args.ref_audio)
        else:
            res = model.generate(text=args.text)

        if isinstance(res, list):
            res = np.concatenate([t.detach().cpu().numpy() if isinstance(t, torch.Tensor) else np.array(t) for t in res], axis=-1)
        elif isinstance(res, torch.Tensor):
            res = res.detach().cpu().numpy()

        res = res.squeeze()
        sf.write(args.output_path, res, 24000)

        gen_time = round(time.time() - start_time, 4)
        duration = 0.0
        if os.path.exists(args.output_path):
            with wave.open(args.output_path, "r") as wf:
                duration = round(wf.getnframes() / float(wf.getframerate()), 2)
        file_size_kb = round(os.path.getsize(args.output_path) / 1024, 2)
        rtf = round(gen_time / max(duration, 0.1), 4)

        result = {
            "model": "omnivoice",
            "backend": "omnivoice-native",
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
            "model": "omnivoice",
            "backend": "omnivoice-error",
            "error": str(e),
            "gen_time": round(time.time() - start_time, 4),
            "output_path": args.output_path
        }
        print(json.dumps(err_res))
        sys.exit(1)

if __name__ == "__main__":
    main()
