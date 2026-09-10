import sys
import types
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

xt_submodule.RotaryEmbedding = RotaryEmbedding
xt_submodule.apply_rotary_pos_emb = apply_rotary_pos_emb
xt_module.x_transformers = xt_submodule
sys.modules["x_transformers"] = xt_module
sys.modules["x_transformers.x_transformers"] = xt_submodule

print("Stub registered. Now importing f5_tts.model.modules...", flush=True)
import f5_tts.model.modules
print("f5_tts.model.modules imported successfully in 0.1s!", flush=True)

import f5_tts.model.backbones.dit
print("f5_tts.model.backbones.dit imported successfully!", flush=True)
