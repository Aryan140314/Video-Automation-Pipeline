"""
Chatterbox Turbo Isolated Subprocess Runner — v1.3.1
===================================================
Runs Chatterbox Turbo inside a dedicated, isolated Python process.
Uses local weights from AppData\\Local\\TTS-Studio\\cache\\huggingface.
Communicates via JSON stdin/stdout lines.
"""

import os
import sys
import time
import json
import torch
import torchaudio

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from path_resolver import configure_hf_environment, get_default_voice_path
configure_hf_environment()

# Safe cuDNN settings for Windows GeForce RTX cards
if torch.cuda.is_available():
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def main():
    try:
        sys.stdout.write("LOADING\n")
        sys.stdout.flush()

        # Perth Watermarker monkeypatch
        try:
            import perth
            class DummyWatermarker:
                def __init__(self, *args, **kwargs): pass
                def apply_watermark(self, wav, *args, **kwargs): return wav
            perth.PerthImplicitWatermarker = DummyWatermarker
            if hasattr(perth, "Perth"):
                perth.Perth.apply_watermark = lambda self, wav, *args, **kwargs: wav
        except Exception:
            pass

        from chatterbox.tts import ChatterboxTTS
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Enable offline loading from existing HF cache
        import huggingface_hub
        _orig_hf_download = huggingface_hub.hf_hub_download
        def _offline_hf_download(*args, **kwargs):
            try:
                return _orig_hf_download(*args, local_files_only=True, **kwargs)
            except Exception:
                return _orig_hf_download(*args, **kwargs)
        huggingface_hub.hf_hub_download = _offline_hf_download
        
        model = ChatterboxTTS.from_pretrained(device=device)

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

                if not ref_audio or not os.path.exists(ref_audio):
                    ref_audio = get_default_voice_path() or ""

                wav = model.generate(text, audio_prompt_path=ref_audio)
                if isinstance(wav, torch.Tensor):
                    wav = wav.cpu()

                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                torchaudio.save(output_path, wav, model.sr)

                if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                    sys.stdout.write(json.dumps({"success": True, "backend": "chatterbox-clone"}) + "\n")
                else:
                    sys.stdout.write(json.dumps({"error": "Output file not generated or too small."}) + "\n")
                sys.stdout.flush()

            except Exception as e:
                import traceback
                traceback.print_exc(file=sys.stderr)
                sys.stdout.write(json.dumps({"error": f"Chatterbox generation error: {str(e)}"}) + "\n")
                sys.stdout.flush()

    except Exception as init_err:
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stdout.write(json.dumps({"error": f"Chatterbox runner init error: {str(init_err)}"}) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
