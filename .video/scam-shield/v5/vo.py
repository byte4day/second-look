import json, sys, numpy as np, soundfile as sf
from pathlib import Path
from kokoro_onnx import Kokoro
m = "/home/byte/Videos/the-notification/models"
VOICE = sys.argv[1] if len(sys.argv) > 1 else "af_heart"
out = Path(__file__).resolve().parent / "vo"
k = Kokoro(f"{m}/kokoro-v1.0.onnx", f"{m}/voices-v1.0.bin")
LINES = [
  "Hi, I'm Bit. Meet Margaret. She's seventy four, and a text just said her bank account is locked.",
  "She presses number one, and pastes it in.",
  "Scam Shield marks the exact red flags, a fake fraud alert, a rushed reply, and says what to do next, in plain English.",
  "Number two is practice. A pretend scammer calls, asking for a code. Margaret hangs up.",
  "Then a debrief shows every trick she spotted.",
  "If it's happening right now, number three gives five calm steps and real helplines.",
  "Number four alerts her family. Number five shows scams reported nearby.",
  "Powered by the Uno Router A P I, with an offline demo mode, and tested end to end.",
  "Scam Shield. Stopping is always a good move.",
]
meta=[]
for i,t in enumerate(LINES):
    a, sr = k.create(t, voice=VOICE, speed=1.0, lang="en-us")
    idx = np.flatnonzero(np.abs(a) > 0.01)
    a = a[max(0, idx[0]-int(.04*sr)): idx[-1]+int(.06*sr)]
    p = out/f"{i:02d}.wav"; sf.write(p, a, sr)
    meta.append({"i":i,"dur":round(len(a)/sr,2),"text":t,"file":str(p)})
(out/"lines.json").write_text(json.dumps(meta,indent=1))
tot=0
for x in meta: tot+=x["dur"]; print(f'{x["dur"]:5.2f}s  {x["text"]}')
print("total speech", round(tot,1))
