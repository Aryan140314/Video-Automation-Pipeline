import os, sys, traceback

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

try:
    from path_resolver import configure_hf_environment
    configure_hf_environment()
    from huggingface_hub import hf_hub_download
    from f5_tts.model import CFM, DiT, UNetT
    from f5_tts.infer.utils_infer import load_model, load_vocoder
    import f5_tts, torch

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model_cls = DiT
    model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)
    ckpt_path = hf_hub_download(repo_id='SWivid/F5-TTS', filename='F5TTS_v1_Base/model_1250000.safetensors')
    vocab_file = os.path.join(os.path.dirname(f5_tts.__file__), 'infer', 'examples', 'vocab.txt')
    ema_model = load_model(model_cls, model_cfg, ckpt_path, mel_spec_type='vocos', vocab_file=vocab_file, device=device)
    print('F5 Model loaded successfully!', flush=True)
    vocoder = load_vocoder(vocoder_name='vocos', is_local=False, device=device)
    print('Vocos loaded successfully!', flush=True)
except Exception:
    traceback.print_exc()
