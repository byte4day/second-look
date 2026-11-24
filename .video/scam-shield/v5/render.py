"""Scam Shield — 50s explainer narrated by Bit. Real captures from cap/, VO from vo/.
Renders 1920x1080 @ 60fps frames with Pillow and pipes them to ffmpeg."""
from __future__ import annotations

import array
import json
import math
import subprocess
import sys
import wave
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
CAP = ROOT / "cap"
FONTS = ROOT / "fonts"
W, H, FPS = 1920, 1080, 60
PREVIEW = "--preview" in sys.argv

# ---------- palette (the app's own tokens) ----------
BG = (233, 238, 236)
PAPER = (243, 245, 242)
INK = (20, 32, 26)
MUTED = (58, 74, 66)
NAVY = (10, 77, 140)
DANGER = (155, 28, 28)
WHITE = (255, 255, 255)
GOLD = (232, 185, 49)


def font(name: str, size: int, wght: int | None = None):
    f = ImageFont.truetype(str(FONTS / name), size)
    if wght:
        f.set_variation_by_name("Bold")
    return f


F_CAP = font("AtkinsonHyperlegible-Regular.ttf", 38)
F_CAP_B = font("AtkinsonHyperlegible-Bold.ttf", 26)
F_TAG = font("AtkinsonHyperlegible-Bold.ttf", 40)
F_TAGN = font("AtkinsonHyperlegible-Bold.ttf", 34)
F_URL = font("AtkinsonHyperlegible-Regular.ttf", 22)
F_OUTRO = font("AtkinsonHyperlegible-Bold.ttf", 32)
F_SMS = font("AtkinsonHyperlegible-Regular.ttf", 27)
F_SMS_B = font("AtkinsonHyperlegible-Bold.ttf", 27)
F_TITLE = font("SourceSerif4.ttf", 120, 700)
F_SUB = font("AtkinsonHyperlegible-Regular.ttf", 44)
F_MONO = ImageFont.truetype("/usr/share/fonts/TTF/JetBrainsMonoNerdFontMono-Bold.ttf", 25)
F_MONO_R = ImageFont.truetype("/usr/share/fonts/TTF/JetBrainsMonoNLNerdFont-Regular.ttf", 25)

# ---------- voice timeline ----------
LINES = json.loads((ROOT / "vo" / "lines.json").read_text())
GAPS = [1.1, 0.5, 1.0, 0.5, 0.6, 0.6, 0.7, 0.9, 0.0]
LEAD, TAIL = 0.8, 2.8
t = LEAD
for ln, g in zip(LINES, GAPS):
    ln["start"] = round(t, 3)
    t += ln["dur"] + g
TOTAL = t + TAIL
SCENE_START = [max(0.0, ln["start"] - 0.35) for ln in LINES]
SCENE_START[0] = 0.0
SCENE_END = SCENE_START[1:] + [TOTAL]


def load_env(path: Path) -> tuple[list[float], int]:
    with wave.open(str(path)) as w:
        sr, n, sw = w.getframerate(), w.getnframes(), w.getsampwidth()
        raw = w.readframes(n)
    if sw == 2:
        a = array.array("h", raw)
        scale = 32768.0
    else:  # float32 from soundfile is written as PCM_16 by default; keep a fallback
        a = array.array("i", raw)
        scale = 2**31
    hop = sr // FPS
    env = []
    for i in range(0, len(a), hop):
        chunk = a[i : i + hop]
        env.append(math.sqrt(sum(x * x for x in chunk) / max(1, len(chunk))) / scale)
    return env, sr


ENVS = [load_env(Path(ln["file"]))[0] for ln in LINES]


def speaking(tt: float) -> tuple[int | None, float]:
    for i, ln in enumerate(LINES):
        if ln["start"] <= tt < ln["start"] + ln["dur"]:
            env = ENVS[i]
            k = int((tt - ln["start"]) * FPS)
            return i, env[k] if k < len(env) else 0.0
    return None, 0.0


def active_line(tt: float) -> int | None:
    """Caption stays up from the line's start until the next scene begins."""
    for i, ln in enumerate(LINES):
        end = SCENE_END[i] if i < len(LINES) - 1 else TOTAL
        if ln["start"] - 0.1 <= tt < end - 0.05:
            return i
    return None


# ---------- easing ----------
def ease(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ease_out(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def interp(keys: list[tuple[float, float]], tt: float) -> float:
    if tt <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if tt <= t1:
            return v0 + (v1 - v0) * ease((tt - t0) / max(1e-6, t1 - t0))
    return keys[-1][1]


# ---------- Bit ----------
TOP = ["....KKKKKKKK....", "..KKGGGGGGGGKK..", ".KGBBBBBBBBBBGK.", "KGBLLBBBBBBBBBGK", "KGBLBBBBBBBBBBGK"]
BOTTOM = [".KGBBWWWWWWBBGK.", ".KGBBBWWWWBBBGK.", "..KGBBBBBBBBGK..", "...KGBBBBBBGK...",
          "....KGBBBBGK....", ".....KGBBGK.....", "......KGGK......", ".......KK......."]
FACES = {
    "happy": ["KGBBWWWWWWWWBBGK", "KGBBWEWWWWEWBBGK", "KGBBWEWWWWEWBBGK", "KGBBWWWWWWWWBBGK", "KGBBWPKWWKPWBBGK"],
    "calm": ["KGBBWWWWWWWWBBGK", "KGBBWEWWWWEWBBGK", "KGBBWEWWWWEWBBGK", "KGBBWWWWWWWWBBGK", "KGBBWPWKKWPWBBGK"],
    "worried": ["KGBBWKWWWWKWBBGK", "KGBBWEWWWWEWBBGK", "KGBBWEWWWWEWSBGK", "KGBBWWWWWWWWSBGK", "KGBBWWKKKKWWBBGK"],
    "thinking": ["KGBBWWWWWKKWBBGK", "KGBBWWEWWWEWBBGK", "KGBBWWEWWWEWBBGK", "KGBBWWWWWWWWBBGK", "KGBBWWWWKKKWBBGK"],
}
OPEN = {  # mouth-open rows 8 and 9 for talking
    "happy": ("KGBBWWWKKWWWBBGK", "KGBBWPWKKWPWBBGK"),
    "calm": ("KGBBWWWKKWWWBBGK", "KGBBWPWKKWPWBBGK"),
    "worried": ("KGBBWWWKKWWWSBGK", "KGBBWWKKKKWWBBGK"),
    "thinking": ("KGBBWWWWKKWWBBGK", "KGBBWWWWKKWWBBGK"),
}
PIX = {"K": INK, "G": GOLD, "B": NAVY, "L": (79, 143, 209), "W": WHITE, "E": INK, "P": (242, 156, 163), "S": (142, 197, 242)}


@lru_cache(maxsize=64)
def bit_img(mood: str, cell: int, open_mouth: bool, blink: bool) -> Image.Image:
    face = list(FACES[mood])
    if open_mouth:
        face[3], face[4] = OPEN[mood]
    if blink:
        face[1] = face[1].replace("E", "W")
        face[2] = face[2].replace("E", "K")
    rows = TOP + face + BOTTOM
    im = Image.new("RGBA", (16 * cell, 18 * cell), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                d.rectangle([x * cell, y * cell, (x + 1) * cell - 1, (y + 1) * cell - 1], fill=PIX[ch])
    return im


def bit_shadow(cell: int) -> Image.Image:
    sh = Image.new("RGBA", (16 * cell + 80, 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([40, 8, 16 * cell + 40, 32], fill=(20, 32, 26, 60))
    return sh.filter(ImageFilter.GaussianBlur(6))


# ---------- captures ----------
META = json.loads((CAP / "meta.json").read_text())
VIEW_W_CSS = 900
WIN = (70, 92, 1250, 1000)  # browser window on canvas
BAR = 52
CONTENT = (WIN[0], WIN[1] + BAR, WIN[2], WIN[3])
CW, CH = CONTENT[2] - CONTENT[0], CONTENT[3] - CONTENT[1]
BASE_SCALE = CW / VIEW_W_CSS  # canvas px per css px at zoom 1


@lru_cache(maxsize=40)
def cap(name: str) -> Image.Image:
    return Image.open(CAP / f"{name}.png").convert("RGB")


def box(name: str, key: str) -> dict:
    return META[name]["boxes"][key]


def render_page(name: str, scroll: float, zoom: float, focus_x: float = 450) -> tuple[Image.Image, tuple]:
    img = cap(name)
    vw, vh = VIEW_W_CSS / zoom, (CH / BASE_SCALE) / zoom
    left = min(max(0.0, focus_x - vw / 2), VIEW_W_CSS - vw)
    top = min(max(0.0, scroll), max(0.0, META[name]["height"] - vh))
    crop = img.crop((round(left * 2), round(top * 2), round((left + vw) * 2), round((top + vh) * 2)))
    out = crop.resize((CW, CH), Image.BICUBIC)
    return out, (left, top, BASE_SCALE * zoom)


def path_for(name: str) -> str:
    return {
        "home": "/", "check_empty": "/check", "result": "/check/result", "practise": "/practise",
        "debrief": "/practise/debrief", "help": "/help", "family": "/family", "scams": "/scams-near-me",
    }.get(name, "/check" if name.startswith("check") else "/practise/chat")


# ---------- scenes: return (capture, scroll_css, zoom, focus_x, cursor(x,y)|None, click_t|None) ----------
def c(name, key, dx=0.5, dy=0.5):
    b = box(name, key)
    return b["x"] + b["w"] * dx, b["y"] + b["h"] * dy


def scene_camera(i: int, tt: float):
    """tt is seconds since the scene started."""
    if i == 0:
        return "home", 0, 1.0, 450, None, None
    if i == 1:
        if tt < 0.75:
            x, y = c("home", "check", 0.3)
            cur = (interp([(0, 720), (0.55, x)], tt), interp([(0, 420), (0.55, y)], tt))
            return "home", 0, 1.0, 450, cur, 0.6
        steps = 6
        k = min(steps, max(1, 1 + int((tt - 0.8) / 0.22)))
        name = f"check_type_{k}"
        b = box(name, "box")
        sx, sy = c(name, "submit", 0.5)
        z = interp([(0.8, 1.0), (1.4, 1.18)], tt)
        scroll = interp([(0.8, 0), (1.4, b["y"] - 120)], tt)
        cur = (interp([(1.9, b["x"] + b["w"] * 0.7), (2.45, sx)], tt), interp([(1.9, b["y"] + b["h"] + 20), (2.45, sy)], tt))
        return name, scroll, z, 450, cur if tt > 1.9 else None, 2.5
    if i == 2:
        mk, td = box("result", "marks"), box("result", "todo")
        scroll = interp([(0, 120), (1.6, 120), (2.6, mk["y"] - 150), (5.6, mk["y"] - 150), (6.8, td["y"] - 60)], tt)
        zoom = interp([(0, 1.0), (1.6, 1.0), (2.6, 1.22), (5.6, 1.22), (6.8, 1.0)], tt)
        return "result", scroll, zoom, 450, None, None
    if i == 3:
        if tt < 0.95:
            qx, qy = c("practise", "quick", 0.5)
            cur = (interp([(0, 700), (0.6, qx)], tt), interp([(0, 700), (0.6, qy)], tt))
            return "practise", 0, 1.0, 450, cur, 0.7
        rb = box("chat_1", "reply")
        if tt < 2.4:
            return "chat_1", rb["y"] - 520, 1.0, 450, None, None
        if tt < 4.0:
            k = min(4, max(1, 1 + int((tt - 2.4) / 0.3)))
            name = f"chat_type_{k}"
            sx, sy = c(name, "send", 0.5)
            cur = (interp([(3.2, rb["x"] + 500), (3.85, sx)], tt), interp([(3.2, rb["y"] + 60), (3.85, sy)], tt))
            return name, rb["y"] - 520, 1.0, 450, cur if tt > 3.2 else None, 3.9
        hb = box("chat_2", "hang")
        hx, hy = c("chat_2", "hang", 0.5)
        scroll = interp([(4.0, rb["y"] - 520), (4.6, hb["y"] - 560)], tt)
        cur = (interp([(4.8, 600), (5.5, hx)], tt), interp([(4.8, hb["y"] - 200), (5.5, hy)], tt))
        return "chat_2", scroll, 1.0, 450, cur if tt > 4.8 else None, 5.6
    if i == 4:
        return "debrief", interp([(0, 0), (2.2, 260)], tt), 1.0, 450, None, None
    if i == 5:
        st = box("help", "steps")
        return "help", interp([(0, 0), (1.2, 0), (3.2, st["y"] - 160)], tt), interp([(1.2, 1.0), (3.2, 1.1)], tt), 450, None, None
    if i == 6:
        split = LINES[6]["start"] - SCENE_START[6] + 2.15
        if tt < split:
            tx, ty = c("family", "text", 0.5)
            cur = (interp([(0.4, 760), (1.3, tx)], tt), interp([(0.4, 600), (1.3, ty)], tt))
            return "family", 0, 1.0, 450, cur, 1.4
        ch = box("scams", "chart")
        return "scams", interp([(split, 0), (split + 1.1, ch["y"] - 140)], tt), 1.0, 450, None, None
    return None


SCENE_TAG = {
    0: (None, "Meet Margaret, 74"),
    1: ("1", "Check a message"),
    2: ("1", "Check a message"),
    3: ("2", "Practise"),
    4: ("2", "Practise"),
    5: ("3", "I need help now"),
    7: (None, "Under the hood"),
}
BIT_MOOD = {0: "happy", 1: "calm", 2: "worried", 3: "thinking", 4: "happy", 5: "calm", 6: "happy", 7: "happy", 8: "happy"}


def scene_index(tt: float) -> int:
    for i in range(len(LINES)):
        if SCENE_START[i] <= tt < SCENE_END[i]:
            return i
    return len(LINES) - 1


# ---------- drawing helpers ----------
def rounded(d: ImageDraw.ImageDraw, xy, r, **kw):
    d.rounded_rectangle(xy, radius=r, **kw)


def shadow_layer(xy, r, blur=24, alpha=50, offset=10):
    x0, y0, x1, y1 = xy
    pad = blur * 3
    sh = Image.new("RGBA", (x1 - x0 + pad * 2, y1 - y0 + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + offset, pad + x1 - x0, pad + y1 - y0 + offset], radius=r, fill=(20, 32, 26, alpha))
    return sh.filter(ImageFilter.GaussianBlur(blur)), (x0 - pad, y0 - pad)


WIN_SHADOW = shadow_layer(WIN, 18)


def wrap(text: str, f, width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if f.getlength(trial) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def draw_window(frame: Image.Image, content: Image.Image, url: str):
    frame.alpha_composite(WIN_SHADOW[0], WIN_SHADOW[1])
    d = ImageDraw.Draw(frame)
    rounded(d, WIN, 18, fill=WHITE)
    d.rounded_rectangle([WIN[0], WIN[1], WIN[2], WIN[1] + BAR + 18], radius=18, fill=(236, 239, 241))
    d.rectangle([WIN[0], WIN[1] + BAR, WIN[2], WIN[1] + BAR + 18], fill=WHITE)
    for k, col in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        cx = WIN[0] + 30 + k * 26
        d.ellipse([cx - 8, WIN[1] + BAR / 2 - 8, cx + 8, WIN[1] + BAR / 2 + 8], fill=col)
    ux0, ux1 = WIN[0] + 320, WIN[2] - 320
    rounded(d, [ux0, WIN[1] + 11, ux1, WIN[1] + BAR - 11], 9, fill=WHITE)
    label = "localhost:5173" + url
    d.text(((ux0 + ux1) / 2, WIN[1] + BAR / 2), label, font=F_URL, fill=MUTED, anchor="mm")
    mask = Image.new("L", content.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, CW - 1, CH - 1 + 20], radius=18, fill=255)
    mask = mask.crop((0, 0, CW, CH))
    ImageDraw.Draw(mask).rectangle([0, 0, CW, 20], fill=255)
    frame.paste(content, (CONTENT[0], CONTENT[1]), mask)
    d.line([CONTENT[0], CONTENT[1], CONTENT[2], CONTENT[1]], fill=(210, 214, 216), width=1)


CURSOR = [(0, 0), (0, 30), (8, 23), (13, 35), (18, 33), (13, 21), (23, 21)]


def draw_cursor(frame, x, y, tt, click_t):
    d = ImageDraw.Draw(frame)
    if click_t is not None and click_t <= tt < click_t + 0.45:
        p = (tt - click_t) / 0.45
        r = 14 + 34 * ease_out(p)
        a = int(140 * (1 - p))
        ring = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse([x - r, y - r, x + r, y + r], outline=(10, 77, 140, a), width=5)
        frame.alpha_composite(ring)
    s = 1.35 * (0.86 if click_t is not None and click_t <= tt < click_t + 0.15 else 1.0)
    pts = [(x + px * s, y + py * s) for px, py in CURSOR]
    d.polygon([(px + 2, py + 3) for px, py in pts], fill=(0, 0, 0, 70))
    d.polygon(pts, fill=INK, outline=WHITE)
    d.line(pts + [pts[0]], fill=WHITE, width=2)


def draw_sms(frame, p: float):
    """Margaret's text, as a phone notification sliding over the page."""
    if p <= 0:
        return
    x0, w_, h_ = WIN[0] + 160, 860, 210
    y0 = int(WIN[1] + BAR + 40 - (1 - ease_out(p)) * 260)
    layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    sh, pos = shadow_layer((x0, y0, x0 + w_, y0 + h_), 26, blur=20, alpha=70)
    layer.alpha_composite(sh, pos)
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x0, y0, x0 + w_, y0 + h_], radius=26, fill=(250, 250, 250, 250), outline=(205, 210, 214), width=2)
    d.rounded_rectangle([x0 + 26, y0 + 24, x0 + 70, y0 + 68], radius=11, fill=(40, 200, 64))
    d.text((x0 + 48, y0 + 46), "✉", font=F_SMS_B, fill=WHITE, anchor="mm")
    d.text((x0 + 88, y0 + 46), "MESSAGES", font=F_URL, fill=MUTED, anchor="lm")
    d.text((x0 + w_ - 30, y0 + 46), "now", font=F_URL, fill=MUTED, anchor="rm")
    d.text((x0 + 28, y0 + 90), "Metro Bank", font=F_SMS_B, fill=INK)
    body = "Your account has been LOCKED. Reply with the 6-digit code we just sent within 30 minutes or your account will be closed."
    for k, ln in enumerate(wrap(body, F_SMS, w_ - 60)[:2]):
        d.text((x0 + 28, y0 + 126 + k * 34), ln, font=F_SMS, fill=INK)
    layer.putalpha(Image.eval(layer.getchannel("A"), lambda a: int(a * min(1, p * 3))))
    frame.alpha_composite(layer)


def draw_panel(frame, tt: float, i: int):
    d = ImageDraw.Draw(frame)
    px0, px1 = 1320, 1860
    # number tag + label
    tag = SCENE_TAG.get(i)
    if i == 6:
        split = SCENE_START[6] + (LINES[6]["start"] - SCENE_START[6]) + 2.15
        tag = ("4", "My family") if tt < split else ("5", "Scams near me")
    if tag:
        num, label = tag
        x = px0
        y = 150
        if num:
            d.ellipse([x, y - 30, x + 60, y + 30], fill=NAVY)
            d.text((x + 30, y + 1), num, font=F_TAGN, fill=WHITE, anchor="mm")
            x += 80
        d.text((x, y), label, font=F_TAG, fill=INK, anchor="lm")
    # Bit
    talking_i, amp = speaking(tt)
    mood = BIT_MOOD[i]
    if i == 0 and tt > LINES[0]["start"] + 2.3:
        mood = "worried"
    open_m = talking_i is not None and amp > 0.035 and int(tt * 12) % 3 != 2
    blink = (tt % 3.7) < 0.12
    cell = 15
    bob = math.sin(tt * 2.0) * 6
    bx = (px0 + px1) // 2 - 8 * cell
    by = int(230 + bob)
    frame.alpha_composite(bit_shadow(cell), (bx - 40, 230 + 18 * cell + 4))
    frame.alpha_composite(bit_img(mood, cell, open_m, blink), (bx, by))
    # speech bubble with the narration
    li = active_line(tt)
    if li is None:
        return
    text = LINES[li]["text"].replace("Uno Router A P I", "Unorouter API")
    lines = wrap(text, F_CAP, px1 - px0 - 56)
    bh = 70 + len(lines) * 50
    y0 = 560
    appear = ease_out((tt - (LINES[li]["start"] - 0.1)) / 0.25)
    y0 += int((1 - appear) * 20)
    bub = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(bub)
    edge = DANGER if mood == "worried" else INK
    bd.rounded_rectangle([px0, y0, px1, y0 + bh], radius=22, fill=WHITE, outline=edge, width=3)
    tx = (px0 + px1) // 2
    bd.polygon([(tx - 18, y0 + 2), (tx, y0 - 22), (tx + 18, y0 + 2)], fill=WHITE)
    bd.line([(tx - 18, y0 + 1), (tx, y0 - 22), (tx + 18, y0 + 1)], fill=edge, width=3)
    bd.text((px0 + 28, y0 + 22), "Bit says", font=F_CAP_B, fill=NAVY)
    for k, ln in enumerate(lines):
        bd.text((px0 + 28, y0 + 58 + k * 50), ln, font=F_CAP, fill=INK)
    bub.putalpha(Image.eval(bub.getchannel("A"), lambda a: int(a * appear)))
    frame.alpha_composite(bub)


TERM_LINES = [
    ("$", "make test-backend"),
    (" ", "69 passed in 10.2s"),
    ("$", "make test-frontend"),
    (" ", "Test Files 9 passed  Tests 18 passed"),
    ("$", "node scripts/a11y_session.mjs"),
    (" ", "routes: 7   axeIssues: 0"),
    ("$", "pytest tests/test_unorouter_provider.py"),
    (" ", "5 passed"),
    ("$", "curl api.unorouter.com/v1/models | jq length"),
    (" ", "288 models available"),
]


def draw_terminal(frame, tt: float):
    frame.alpha_composite(WIN_SHADOW[0], WIN_SHADOW[1])
    d = ImageDraw.Draw(frame)
    rounded(d, WIN, 18, fill=(24, 30, 28))
    d.rounded_rectangle([WIN[0], WIN[1], WIN[2], WIN[1] + BAR], radius=18, fill=(40, 48, 45))
    d.rectangle([WIN[0], WIN[1] + BAR - 18, WIN[2], WIN[1] + BAR], fill=(40, 48, 45))
    for k, col in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        cx = WIN[0] + 30 + k * 26
        d.ellipse([cx - 8, WIN[1] + BAR / 2 - 8, cx + 8, WIN[1] + BAR / 2 + 8], fill=col)
    d.text(((WIN[0] + WIN[2]) / 2, WIN[1] + BAR / 2), "scam-shield — tests", font=F_URL, fill=(190, 198, 194), anchor="mm")
    shown = int(tt / 0.42) + 1
    y = WIN[1] + BAR + 50
    for k, (p, ln) in enumerate(TERM_LINES[:shown]):
        if p == "$":
            d.text((WIN[0] + 50, y), "$ ", font=F_MONO, fill=(120, 200, 140))
            d.text((WIN[0] + 90, y), ln, font=F_MONO_R, fill=(230, 235, 232))
        else:
            ok = "passed" in ln or "axeIssues: 0" in ln or "models" in ln
            col = (120, 210, 150) if ok else (150, 190, 240)
            d.text((WIN[0] + 90, y), ("✓ " if ok else "") + ln, font=F_MONO, fill=col)
        y += 46 if p == "$" else 64
    # Unorouter badge
    bx0, by0 = WIN[0] + 50, WIN[3] - 150
    rounded(d, [bx0, by0, bx0 + 640, by0 + 90], 16, fill=(36, 44, 41), outline=(90, 110, 100), width=2)
    d.text((bx0 + 30, by0 + 45), "AI by the Unorouter API", font=F_TAG, fill=WHITE, anchor="lm")


def draw_outro(frame, tt: float):
    p = ease_out(tt / 0.6)
    d = ImageDraw.Draw(frame)
    cell = 22
    bob = math.sin(tt * 2.2) * 8
    talking_i, amp = speaking(SCENE_START[8] + tt)
    open_m = talking_i is not None and amp > 0.035 and int(tt * 12) % 3 != 2
    im = bit_img("happy", cell, open_m, (tt % 3.0) < 0.12)
    bx, by = W // 2 - 8 * cell, int(150 + bob + (1 - p) * 40)
    frame.alpha_composite(bit_shadow(cell), (bx - 40, 150 + 18 * cell + 8))
    frame.alpha_composite(im, (bx, by))
    a = int(255 * p)
    txt = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(txt)
    td.text((W // 2, 690), "Scam Shield", font=F_TITLE, fill=NAVY + (a,), anchor="mm")
    td.text((W // 2, 800), "Stopping is always a good move.", font=F_SUB, fill=INK + (a,), anchor="mm")
    q = ease_out((tt - 1.0) / 0.6)
    td.text((W // 2, 900), "1 Check    2 Practise    3 Help now    4 Family    5 Scams near me", font=F_OUTRO, fill=MUTED + (int(255 * q),), anchor="mm")
    frame.alpha_composite(txt)


BASE = Image.new("RGBA", (W, H), BG + (255,))


def render(tt: float) -> Image.Image:
    frame = BASE.copy()
    i = scene_index(tt)
    st = tt - SCENE_START[i]
    if i == 8:
        draw_outro(frame, st)
    else:
        if i == 7:
            draw_terminal(frame, st)
        else:
            name, scroll, zoom, fx, cur, click_t = scene_camera(i, st)
            content, (left, top, sc) = render_page(name, scroll, zoom, fx)
            draw_window(frame, content, path_for(name))
            if i == 0:
                draw_sms(frame, (tt - (LINES[0]["start"] + 2.0)) / 0.5)
            if cur:
                x = CONTENT[0] + (cur[0] - left) * sc
                y = CONTENT[1] + (cur[1] - top) * sc
                draw_cursor(frame, x, y, st, click_t)
        draw_panel(frame, tt, i)
    # cross-fade at scene starts (short dip)
    if 0 < st < 0.12 and i > 0:
        pass
    return frame.convert("RGB")


def main():
    if PREVIEW:
        out = ROOT / "preview"
        out.mkdir(exist_ok=True)
        for tt in [float(x) for x in sys.argv[2:]] or [2, 6, 9, 14, 20, 24, 27, 31, 35, 40, 46]:
            render(tt).save(out / f"t{tt:05.1f}.png")
        print("preview", TOTAL)
        return
    n = int(TOTAL * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", str(ROOT / "video.mp4")],
        stdin=subprocess.PIPE,
    )
    for f in range(n):
        ff.stdin.write(render(f / FPS).tobytes())
        if f % 300 == 0:
            print(f"{f}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    (ROOT / "timeline.json").write_text(json.dumps({"total": TOTAL, "lines": LINES}, indent=1))
    print("done", TOTAL)


if __name__ == "__main__":
    main()
