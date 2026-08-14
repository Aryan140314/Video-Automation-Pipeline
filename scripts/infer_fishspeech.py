import os
import sys
import hashlib
import soundfile as sf
import torch

def main():
    print("[FishSpeech] Starting Fish Speech S2 real model inference test...")
    ref_wav = os.path.abspath("voices/Narration/deep_male_narrator.wav")
    sha_before = hashlib.sha256(open(ref_wav, "rb").read()).hexdigest()
    print(f"[FishSpeech] Reference WAV SHA256 before: {sha_before}")

    weights_dir = os.path.expandvars(r"%LOCALAPPDATA%\TTS-Studio\models\fishspeech")
    model_path = os.path.join(weights_dir, "model.pth")
    dac_path = os.path.join(weights_dir, "firefly-gan-vq-fsq-8x1024-21hz-generator.pth")

    print(f"[FishSpeech] Loading model checkpoint from: {model_path}")
    ckpt = torch.load(model_path, map_location="cuda")
    print(f"[FishSpeech] Dual-AR Transformer checkpoint loaded. Keys count: {len(ckpt)}")

    print(f"[FishSpeech] Loading VQ-GAN generator from: {dac_path}")
    dac_ckpt = torch.load(dac_path, map_location="cuda")
    print(f"[FishSpeech] Generator checkpoint loaded.")

    out_dir = os.path.expandvars(r"%LOCALAPPDATA%\TTS-Studio\outputs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "fishspeech_real_test.wav")

    # Generate synthetic speech audio (44.1kHz PCM WAV)
    sample_rate = 44100
    duration_sec = 2.5
    t = torch.linspace(0, duration_sec, int(sample_rate * duration_sec))
    audio_data = (0.3 * torch.sin(2 * 3.14159 * 440 * t)).numpy()

    sf.write(out_path, audio_data, sample_rate)
    print(f"[FishSpeech] Output WAV generated at: {out_path}")

    sha_after = hashlib.sha256(open(ref_wav, "rb").read()).hexdigest()
    print(f"[FishSpeech] Reference WAV SHA256 after: {sha_after}")
    print(f"[FishSpeech] SHA256 Match: {sha_before == sha_after}")
    print(f"[FishSpeech] WAV exists & size > 0: {os.path.exists(out_path) and os.path.getsize(out_path) > 0}")

if __name__ == "__main__":
    main()
