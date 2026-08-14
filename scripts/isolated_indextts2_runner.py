import os
import sys
import time
import json
import argparse
import wave
import torch
import soundfile as sf
from huggingface_hub import snapshot_download, hf_hub_download

index_root = r'E:\TTS\runtimes\IndexTTS2'
if index_root not in sys.path:
    sys.path.insert(0, index_root)

def main():
    parser = argparse.ArgumentParser(description="IndexTTS 2.5 Isolated Subprocess Runner")
    parser.add_argument("--text", type=str, required=True, help="Text to synthesize")
    parser.add_argument("--ref_audio", type=str, default="", help="Reference speaker audio WAV")
    parser.add_argument("--output_path", type=str, required=True, help="Output WAV file path")
    args = parser.parse_args()

    start_time = time.time()
    os.makedirs(os.path.dirname(os.path.abspath(args.output_path)), exist_ok=True)

    try:
        appdata = os.environ.get("LOCALAPPDATA", r"C:\Users\aryan\AppData\Local")
        model_dir = os.path.join(appdata, "TTS-Studio", "models", "indextts2")
        os.makedirs(model_dir, exist_ok=True)

        if not os.path.isdir(model_dir) or len(os.listdir(model_dir)) < 3:
            for attempt in range(5):
                try:
                    snapshot_download(repo_id='IndexTeam/IndexTTS-2.5', local_dir=model_dir, ignore_patterns=['*.git*'])
                    break
                except Exception as err:
                    time.sleep(3)

        cfg_path = os.path.join(model_dir, 'config.yaml')
        if not os.path.exists(cfg_path):
            try:
                hf_hub_download(repo_id='IndexTeam/IndexTTS-2.5', filename='config.yaml', local_dir=model_dir)
            except Exception:
                pass

        stat_file = os.path.join(model_dir, 'wav2vec2bert_stats.pt')
        if not os.path.exists(stat_file):
            try:
                hf_hub_download(repo_id='IndexTeam/IndexTTS-2.5', filename='wav2vec2bert_stats.pt', local_dir=model_dir)
            except Exception:
                pass

        w2v_dir = os.path.join(model_dir, 'hf_cache', 'w2v-bert-2.0')
        os.makedirs(w2v_dir, exist_ok=True)
        if not os.listdir(w2v_dir):
            for attempt in range(5):
                try:
                    snapshot_download('facebook/w2v-bert-2.0', local_dir=w2v_dir)
                    break
                except Exception:
                    time.sleep(3)

        maskgct_dir = os.path.join(model_dir, 'hf_cache')
        maskgct_path = os.path.join(maskgct_dir, 'semantic_codec_model.safetensors')
        if not os.path.exists(maskgct_path):
            for attempt in range(5):
                try:
                    hf_hub_download(repo_id='amphion/MaskGCT', filename='semantic_codec/model.safetensors', local_dir=maskgct_dir)
                    break
                except Exception:
                    time.sleep(3)

        from indextts.infer_v2_5 import IndexTTS2
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        tts = IndexTTS2(cfg_path=cfg_path, model_dir=model_dir, device=device)

        ref_voice = args.ref_audio if args.ref_audio and os.path.exists(args.ref_audio) else r'E:\TTS\voices\Narration\deep_male_narrator.wav'

        res = tts.infer(
            spk_audio_prompt=ref_voice,
            text=args.text,
            output_path=None,
            lang="auto"
        )

        if isinstance(res, tuple):
            sr, wav_np = res
            sf.write(args.output_path, wav_np.squeeze(), sr)

        gen_time = round(time.time() - start_time, 4)
        duration = 0.0
        if os.path.exists(args.output_path):
            with wave.open(args.output_path, "r") as wf:
                duration = round(wf.getnframes() / float(wf.getframerate()), 2)
        file_size_kb = round(os.path.getsize(args.output_path) / 1024, 2)
        rtf = round(gen_time / max(duration, 0.1), 4)

        result = {
            "model": "indextts2",
            "backend": "indextts2.5-native",
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
            "model": "indextts2",
            "backend": "indextts2-error",
            "error": str(e),
            "gen_time": round(time.time() - start_time, 4),
            "output_path": args.output_path
        }
        print(json.dumps(err_res))
        sys.exit(1)

if __name__ == "__main__":
    main()
