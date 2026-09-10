import os, sys, time, traceback

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from path_resolver import configure_hf_environment
configure_hf_environment()

try:
    print("Testing full F5-TTS loading...", flush=True)
    from huggingface_hub import hf_hub_download
    from f5_tts.model import CFM, DiT, UNetT
    from f5_tts.infer.utils_infer import load_model, preprocess_ref_audio_text, infer_process
    from vocos import Vocos
    import f5_tts, torch, soundfile as sf

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_cls = DiT
    model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)
    
    ckpt_path = hf_hub_download(repo_id="SWivid/F5-TTS", filename="F5TTS_v1_Base/model_1250000.safetensors")
    vocab_file = os.path.join(os.path.dirname(f5_tts.__file__), "infer", "examples", "vocab.txt")
    
    ema_model = load_model(model_cls, model_cfg, ckpt_path, mel_spec_type="vocos", vocab_file=vocab_file, device=device)
    vocoder = Vocos.from_pretrained("charactr/vocos-mel-24khz").to(device)
    print("F5-TTS and Vocos loaded successfully on", device, "!", flush=True)

    # Test synthesis
    ref_audio = os.path.join(WORKSPACE_ROOT, "voices", "Narration", "deep_male_narrator.wav")
    ref_audio_clean, ref_text = preprocess_ref_audio_text(ref_audio, "")
    out_file = os.path.join(WORKSPACE_ROOT, "outputs", "f5_direct_test.wav")

    final_wave, final_sr, _ = infer_process(
        ref_audio_clean,
        ref_text,
        "Testing high quality F5 TTS neural voice generation.",
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
    print(f"Generated speech to {out_file} (size: {os.path.getsize(out_file)} bytes)!", flush=True)

except Exception:
    traceback.print_exc()
