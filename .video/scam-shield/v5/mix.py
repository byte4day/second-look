"""Audio: Bit's voice lines at their timeline positions + soft synthesised clicks. Voice only, no music."""
import json, math, random, struct, subprocess, wave
from pathlib import Path
ROOT = Path(__file__).resolve().parent
LINES = json.loads((ROOT / "vo" / "lines.json").read_text())
GAPS = [1.1, 0.5, 1.0, 0.5, 0.6, 0.6, 0.7, 0.9, 0.0]
t = 0.8
for ln, g in zip(LINES, GAPS):
    ln["start"] = t; t += ln["dur"] + g
TOTAL = t + 2.8
SS = [0.0] + [ln["start"] - 0.35 for ln in LINES[1:]]
CLICKS = [SS[1] + 0.6, SS[1] + 2.5, SS[3] + 0.7, SS[3] + 3.9, SS[3] + 5.6, SS[6] + 1.4]
SR = 48000
buf = [0.0] * int(TOTAL * SR)
random.seed(4)
for c in CLICKS:
    s0 = int(c * SR)
    for k in range(int(0.03 * SR)):
        env = math.exp(-k / (0.004 * SR))
        v = (random.uniform(-1, 1) * 0.5 + math.sin(2 * math.pi * 2200 * k / SR) * 0.5) * env * 0.18
        if s0 + k < len(buf): buf[s0 + k] += v
with wave.open(str(ROOT / "clicks.wav"), "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x)) * 32767)) for x in buf))
args = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(ROOT / "clicks.wav")]
filt = []
for i, ln in enumerate(LINES):
    args += ["-i", ln["file"]]
    ms = int(ln["start"] * 1000)
    filt.append(f"[{i+1}:a]aresample=48000,adelay={ms}|{ms},apad[v{i}]")
mix = "".join(f"[v{i}]" for i in range(len(LINES)))
filt.append(f"[0:a]apad[c];{mix}[c]amix=inputs={len(LINES)+1}:normalize=0,atrim=0:{TOTAL:.3f},"
            "highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,loudnorm=I=-16:TP=-1.5:LRA=7[out]")
args += ["-filter_complex", ";".join(filt), "-map", "[out]", "-ar", "48000", "-ac", "2", str(ROOT / "audio.wav")]
subprocess.run(args, check=True)
print("audio", round(TOTAL, 2))
