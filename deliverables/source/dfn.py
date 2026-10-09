"""DeepFilterNet3 speech enhancement: python3 dfn.py in.wav out.wav [atten_db]"""
import sys, types
# deepfilternet imports a torchaudio module that was removed in torchaudio 2.x; stub it.
_b = types.ModuleType("torchaudio.backend"); _c = types.ModuleType("torchaudio.backend.common")
_c.AudioMetaData = object; _b.common = _c
sys.modules["torchaudio.backend"] = _b; sys.modules["torchaudio.backend.common"] = _c
import numpy as np, soundfile as sf, torch
from df.enhance import enhance, init_df
model, state, _ = init_df()
x, sr = sf.read(sys.argv[1], dtype="float32")
if x.ndim > 1: x = x.mean(1)
assert sr == state.sr(), (sr, state.sr())
atten = float(sys.argv[3]) if len(sys.argv) > 3 else None
y = enhance(model, state, torch.from_numpy(x)[None], atten_lim_db=atten)
sf.write(sys.argv[2], y.squeeze(0).numpy(), sr, subtype="PCM_24")
print("enhanced", sys.argv[2])
