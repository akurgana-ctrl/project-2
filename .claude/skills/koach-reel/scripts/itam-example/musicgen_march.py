"""Generate ~42 s of original epic orchestral music with MusicGen (local, CPU). usage: musicgen_epic.py <out.wav> [model]"""
import sys, numpy as np, soundfile as sf, torch
from transformers import AutoProcessor, MusicgenForConditionalGeneration
out = sys.argv[1]; name = sys.argv[2] if len(sys.argv) > 2 else "facebook/musicgen-medium"
torch.manual_seed(23)
proc = AutoProcessor.from_pretrained(name)
model = MusicgenForConditionalGeneration.from_pretrained(name)
model.eval()
SR = model.config.audio_encoder.sampling_rate
PROMPT = ("dramatic epic military march, driving marching snare drum rolls and cadence, heavy timpani and bass drum on every beat, "
          "bold brass fanfare, trumpets and french horns, staccato strings ostinato, cymbal crashes, heroic and intense, "
          "rising to a powerful triumphant climax, 116 bpm, steady march rhythm, no vocals")
torch.set_num_threads(4)
with torch.no_grad():
    inp = proc(text=[PROMPT], padding=True, return_tensors="pt")
    a = model.generate(**inp, do_sample=True, guidance_scale=3.0, max_new_tokens=1500)[0, 0].numpy()  # ~30 s
    print("part A", len(a) / SR, flush=True)
    tail = a[-int(SR * 8):]
    inp2 = proc(audio=[tail], sampling_rate=SR, text=[PROMPT + ", triumphant finale"], padding=True, return_tensors="pt")
    b = model.generate(**inp2, do_sample=True, guidance_scale=3.0, max_new_tokens=1000)[0, 0].numpy()  # prompt(8s)+~12s
    b = b[int(SR * 8):]
    print("part B", len(b) / SR, flush=True)
x = np.concatenate([a, b]).astype(np.float32)
x /= np.abs(x).max() / 0.9
sf.write(out, x, SR)
print("ok", len(x) / SR)
