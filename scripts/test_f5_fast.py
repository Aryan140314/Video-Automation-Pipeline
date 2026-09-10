import os, sys, types
import torch
from torch import nn
from einops import rearrange

# Build lightweight stub for x_transformers
xt_module = types.ModuleType("x_transformers")
xt_submodule = types.ModuleType("x_transformers.x_transformers")

def rotate_half(x):
    x = rearrange(x, '... (d r) -> ... d r', r = 2)
    x1, x2 = x.unbind(dim = -1)
    x = torch.stack((-x2, x1), dim = -1)
    return rearrange(x, '... d r -> ... (d r)')

def apply_rotary_pos_emb(t, freqs, scale = 1):
    rot_dim, seq_len, orig_dtype = freqs.shape[-1], t.shape[-2], t.dtype
    freqs = freqs[:, -seq_len:, :]
    if torch.is_tensor(scale):
        scale = scale[:, -seq_len:, :]

    if t.ndim == 4 and freqs.ndim == 3:
        freqs = rearrange(freqs, 'b n d -> b 1 n d')
        if torch.is_tensor(scale):
            scale = rearrange(scale, 'b n d -> b 1 n d')

    t_rot, t_unrotated = t[..., :rot_dim], t[..., rot_dim:]
    t_rot = (t_rot * freqs.cos() * scale) + (rotate_half(t_rot) * freqs.sin() * scale)
    out = torch.cat((t_rot, t_unrotated), dim = -1)
    return out.type(orig_dtype)

class RMSNorm(nn.Module):
    def __init__(self, dim, scale = True):
        super().__init__()
        self.scale = dim ** 0.5
        self.gamma = nn.Parameter(torch.ones(dim)) if scale else None

    def forward(self, x):
        norm = torch.norm(x, dim = -1, keepdim = True) * self.scale
        return (x / norm.clamp(min = 1e-8)) * (self.gamma if self.gamma is not None else 1.0)

class RotaryEmbedding(nn.Module):
    def __init__(self, dim, use_xpos = False, scale_base = 512, interpolation_factor = 1., base = 10000, base_rescale_factor = 1.):
        super().__init__()
        base *= base_rescale_factor ** (dim / (dim - 2))
        inv_freq = 1. / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer('inv_freq', inv_freq)
        self.interpolation_factor = interpolation_factor
        if not use_xpos:
            self.register_buffer('scale', None)
        else:
            scale = (torch.arange(0, dim, 2) + 0.4 * dim) / (1.4 * dim)
            self.scale_base = scale_base
            self.register_buffer('scale', scale)

    def forward_from_seq_len(self, seq_len):
        device = self.inv_freq.device
        t = torch.arange(seq_len, device = device)
        return self.forward(t)

    def forward(self, t, offset = 0):
        max_pos = t.max() + 1
        if t.ndim == 1:
            t = rearrange(t, 'n -> 1 n')
        freqs = torch.einsum('b i , j -> b i j', t.type_as(self.inv_freq), self.inv_freq) / self.interpolation_factor
        freqs = torch.stack((freqs, freqs), dim = -1)
        freqs = rearrange(freqs, '... d r -> ... (d r)')
        if self.scale is None:
            return freqs, 1.
        power = (t - (max_pos // 2)) / self.scale_base
        scale = self.scale ** rearrange(power, '... n -> ... n 1')
        scale = torch.stack((scale, scale), dim = -1)
        scale = rearrange(scale, '... d r -> ... (d r)')
        return freqs, scale

xt_module.RMSNorm = RMSNorm
xt_submodule.RMSNorm = RMSNorm
xt_submodule.RotaryEmbedding = RotaryEmbedding
xt_submodule.apply_rotary_pos_emb = apply_rotary_pos_emb
xt_module.x_transformers = xt_submodule
sys.modules["x_transformers"] = xt_module
sys.modules["x_transformers.x_transformers"] = xt_submodule

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "scripts"))

from path_resolver import configure_hf_environment
configure_hf_environment()

from huggingface_hub import hf_hub_download
from f5_tts.model.backbones.dit import DiT
from f5_tts.infer.utils_infer import load_model, preprocess_ref_audio_text, infer_process
from vocos import Vocos
import f5_tts, soundfile as sf

print("Loading F5-TTS model on CUDA...", flush=True)
device = "cuda" if torch.cuda.is_available() else "cpu"
model_cls = DiT
model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)

ckpt_path = hf_hub_download(repo_id="SWivid/F5-TTS", filename="F5TTS_v1_Base/model_1250000.safetensors", local_files_only=True)
vocab_file = os.path.join(WORKSPACE_ROOT, ".venv", "Lib", "site-packages", "f5_tts", "infer", "examples", "vocab.txt")
ema_model = load_model(model_cls, model_cfg, ckpt_path, mel_spec_type="vocos", vocab_file=vocab_file, device=device)
vocoder = Vocos.from_pretrained("charactr/vocos-mel-24khz").to(device)
print("F5-TTS & Vocos loaded successfully on", device, flush=True)

# Test synthesis
ref_audio = os.path.join(WORKSPACE_ROOT, "voices", "Narration", "deep_male_narrator.wav")
ref_audio_clean, ref_text = preprocess_ref_audio_text(ref_audio, "")
out_file = os.path.join(WORKSPACE_ROOT, "outputs", "f5_fast_test.wav")

final_wave, final_sr, _ = infer_process(
    ref_audio_clean,
    ref_text,
    "Testing high performance F5 TTS voice cloning with fast custom kernel stub.",
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
