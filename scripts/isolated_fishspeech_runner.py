"""
Fish Speech S2 Isolated Subprocess Runner
==========================================
Uses the correct Fish Speech 1.5 API:
  - launch_thread_safe_queue() → creates llama_queue worker thread
  - load_dac_decoder() → loads DAC/VQ-GAN decoder
  - TTSInferenceEngine(llama_queue, decoder_model, precision, compile) → engine
  - engine.inference(ServeTTSRequest) → yields InferenceResult
"""
import os
import sys
import time
import json
import wave
import argparse

import torch
import soundfile as sf
import numpy as np

def main():
    parser = argparse.ArgumentParser(description="Fish Speech S2 Isolated Subprocess Runner")
    parser.add_argument("--text", type=str, required=True)
    parser.add_argument("--ref_audio", type=str, default="")
    parser.add_argument("--output_path", type=str, required=True)
    args = parser.parse_args()

    start_time = time.time()
    os.makedirs(os.path.dirname(os.path.abspath(args.output_path)), exist_ok=True)

    try:
        from fish_speech.models.text2semantic.inference import (
            launch_thread_safe_queue, init_model
        )
        from fish_speech.models.dac.modded_dac import DAC
        from fish_speech.inference_engine import TTSInferenceEngine
        from fish_speech.utils.schema import ServeTTSRequest, ServeReferenceAudio

        device = "cuda" if torch.cuda.is_available() else "cpu"
        precision = torch.bfloat16

        appdata = os.environ.get("LOCALAPPDATA", r"C:\Users\aryan\AppData\Local")
        models_dir = os.path.join(appdata, "TTS-Studio", "models", "fishspeech")

        # ── 1. Load DAC decoder ───────────────────────────────────────────────
        dac_ckpt = os.path.join(models_dir, "firefly-gan-vq-fsq-8x1024-21hz-generator.pth")
        if not os.path.exists(dac_ckpt):
            raise FileNotFoundError(f"DAC weights not found: {dac_ckpt}")

        import hydra
        hydra.core.global_hydra.GlobalHydra.instance().clear()
        hydra.initialize_config_module("fish_speech.configs", version_base="1.3")
        cfg = hydra.compose(config_name="modded_dac_vq")
        dac_decoder = hydra.utils.instantiate(cfg)
        state_dict = torch.load(dac_ckpt, map_location=device, weights_only=True)
        if "generator" in state_dict:
            state_dict = state_dict["generator"]
        dac_decoder.load_state_dict(state_dict, strict=False)
        dac_decoder.eval().to(device)

        # ── 2. Launch LLAMA queue worker thread ───────────────────────────────
        llama_queue, llama_event = launch_thread_safe_queue(
            checkpoint_path=models_dir,
            device=device,
            precision=precision,
            compile=False,
        )
        llama_event.wait(timeout=60)

        # ── 3. Build inference engine ─────────────────────────────────────────
        engine = TTSInferenceEngine(
            llama_queue=llama_queue,
            decoder_model=dac_decoder,
            precision=precision,
            compile=False,
        )

        # ── 4. Build request (with optional reference voice) ──────────────────
        references = []
        if args.ref_audio and os.path.exists(args.ref_audio):
            with open(args.ref_audio, "rb") as f:
                audio_bytes = f.read()
            references = [ServeReferenceAudio(audio=audio_bytes, text="")]

        req = ServeTTSRequest(
            text=args.text,
            references=references,
            max_new_tokens=1024,
            top_p=0.8,
            repetition_penalty=1.1,
            temperature=0.8,
            streaming=False,
            chunk_length=200,
        )

        # ── 5. Run inference ──────────────────────────────────────────────────
        audio_segments = []
        sample_rate = 44100
        for result in engine.inference(req):
            if result.code == "final" and result.audio is not None:
                sample_rate, audio_np = result.audio
                audio_segments.append(audio_np)
            elif result.code == "error":
                raise RuntimeError(str(result.error))

        if not audio_segments:
            raise RuntimeError("Fish Speech produced no audio segments.")

        combined = np.concatenate(audio_segments, axis=0)
        sf.write(args.output_path, combined, sample_rate)

        # ── 6. Compute metrics ────────────────────────────────────────────────
        gen_time = round(time.time() - start_time, 4)
        duration = 0.0
        file_size_kb = 0.0
        if os.path.exists(args.output_path):
            file_size_kb = round(os.path.getsize(args.output_path) / 1024, 2)
            try:
                with wave.open(args.output_path, "r") as wf:
                    duration = round(wf.getnframes() / float(wf.getframerate()), 2)
            except Exception:
                duration = round(len(combined) / sample_rate, 2)

        print(json.dumps({
            "model": "fishspeech",
            "backend": "fishspeech-s2-native",
            "cloning_active": bool(references),
            "gen_time": gen_time,
            "duration": duration,
            "rtf": round(gen_time / max(duration, 0.1), 4),
            "file_size_kb": file_size_kb,
            "output_path": args.output_path,
            "device": device
        }))

    except Exception as e:
        print(json.dumps({
            "model": "fishspeech",
            "backend": "fishspeech-error",
            "error": str(e),
            "gen_time": round(time.time() - start_time, 4),
            "output_path": args.output_path
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
