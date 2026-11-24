"""Scam Shield explainer v6: editorial / broadcast style.
Reuses the timeline, camera moves and captures from render.py; new graphics package:
centred footage with hairline frame, lower-third chapter titles, chunked subtitles,
corner mascot presenter, dissolves. Mascot art comes from mascot/ when present."""
from __future__ import annotations

import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import render as r

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1920, 1080, 60
FONTS = ROOT / "fonts"
MASCOT_DIR = ROOT / "mascot"

INK = (17, 24, 21)
MUTED = (88, 100, 94)
NAVY = (10, 77, 140)
RED = (176, 38, 38)
BG_TOP = (246, 247, 246)
BG_BOT = (232, 236, 234)
WHITE = (255, 255, 255)


def inter(size: int, weight: str = "SemiBold") -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTS / "Inter.ttf"), size)
    f.set_variation_by_name(weight)
    return f


F_SUB = inter(42, "SemiBold")
F_LT_NUM = inter(40, "Bold")
F_LT = inter(46, "Bold")
F_LT_KICK = inter(22, "Medium")
F_URL = inter(19, "Medium")
F_TITLE = inter(128, "Bold")
F_TAG = inter(40, "Medium")
F_ROW = inter(28, "SemiBold")
F_ROWN = inter(28, "Bold")
F_SMS_APP = inter(22, "SemiBold")
F_SMS_T = inter(34, "Bold")
F_SMS_B = inter(30, "Regular")
F_MONO = ImageFont.truetype("/usr/share/fonts/TTF/JetBrainsMonoNLNerdFont-Regular.ttf", 26)
F_MONO_B = ImageFont.truetype("/usr/share/fonts/TTF/JetBrainsMonoNerdFontMono-Bold.ttf", 26)

LINES, TOTAL = r.LINES, r.TOTAL
SS, SE = r.SCENE_START, r.SCENE_END
ease, ease_out, interp = r.ease, r.ease_out, r.interp


def ease_back(x: float) -> float:
    x = min(1.0, max(0.0, x))
    c1 = 1.4
    return 1 + (c1 + 1) * (x - 1) ** 3 + c1 * (x - 1) ** 2


# ---------- background ----------
def make_bg() -> Image.Image:
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * k) for a, b in zip(BG_TOP, BG_BOT)))
    return bg.convert("RGBA")


BG = make_bg()

# ---------- footage frame ----------
WIN = (300, 96, 1620, 952)
BAR = 44
CONTENT = (WIN[0], WIN[1] + BAR, WIN[2], WIN[3])
CW, CH = CONTENT[2] - CONTENT[0], CONTENT[3] - CONTENT[1]
SCALE = CW / r.VIEW_W_CSS


def soft_shadow(box, radius, blur, alpha, dy):
    x0, y0, x1, y1 = box
    pad = blur * 3
    im = Image.new("RGBA", (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([pad, pad + dy, pad + x1 - x0, pad + y1 - y0 + dy], radius=radius, fill=(10, 20, 15, alpha))
    return im.filter(ImageFilter.GaussianBlur(blur)), (x0 - pad, y0 - pad)


SH_FAR = soft_shadow(WIN, 16, 40, 46, 26)
SH_NEAR = soft_shadow(WIN, 16, 6, 30, 3)

MASK = Image.new("L", (WIN[2] - WIN[0], WIN[3] - WIN[1]), 0)
ImageDraw.Draw(MASK).rounded_rectangle([0, 0, MASK.width - 1, MASK.height - 1], radius=14, fill=255)


def page_view(name: str, scroll: float, zoom: float, fx: float):
    img = r.cap(name)
    vw, vh = r.VIEW_W_CSS / zoom, (CH / SCALE) / zoom
    left = min(max(0.0, fx - vw / 2), r.VIEW_W_CSS - vw)
    top = min(max(0.0, scroll), max(0.0, r.META[name]["height"] - vh))
    crop = img.crop((round(left * 2), round(top * 2), round((left + vw) * 2), round((top + vh) * 2)))
    return crop.resize((CW, CH), Image.LANCZOS), (left, top, SCALE * zoom)


def window_image(content: Image.Image, url: str, dark: bool = False) -> Image.Image:
    w, h = WIN[2] - WIN[0], WIN[3] - WIN[1]
    im = Image.new("RGBA", (w, h), (24, 29, 27, 255) if dark else WHITE + (255,))
    d = ImageDraw.Draw(im)
    bar = (34, 40, 38) if dark else (243, 244, 245)
    d.rectangle([0, 0, w, BAR], fill=bar)
    d.line([0, BAR, w, BAR], fill=(52, 60, 57) if dark else (222, 225, 228), width=1)
    for k in range(3):
        cx = 26 + k * 22
        d.ellipse([cx - 6, BAR / 2 - 6, cx + 6, BAR / 2 + 6], fill=(80, 88, 85) if dark else (208, 211, 214))
    if url:
        pw = 420
        d.rounded_rectangle([w / 2 - pw / 2, 9, w / 2 + pw / 2, BAR - 9], radius=7, fill=(46, 54, 51) if dark else WHITE,
                            outline=None if dark else (226, 229, 232))
        d.text((w / 2, BAR / 2), url, font=F_URL, fill=(170, 178, 174) if dark else MUTED, anchor="mm")
    if content is not None:
        im.paste(content, (0, BAR))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(im, (0, 0), MASK)
    # hairline border, drawn inside the mask
    ImageDraw.Draw(out).rounded_rectangle([0, 0, w - 1, h - 1], radius=14, outline=(17, 24, 21, 36), width=1)
    return out


def place_window(frame: Image.Image, win: Image.Image, scale: float = 1.0, alpha: float = 1.0, dy: float = 0):
    if alpha <= 0:
        return
    if scale != 1.0:
        nw, nh = int(win.width * scale), int(win.height * scale)
        win = win.resize((nw, nh), Image.BICUBIC)
    x = (WIN[0] + WIN[2]) // 2 - win.width // 2
    y = (WIN[1] + WIN[3]) // 2 - win.height // 2 + int(dy)
    if alpha >= 0.999:
        frame.alpha_composite(SH_FAR[0], (SH_FAR[1][0] + x - WIN[0], SH_FAR[1][1] + y - WIN[1]))
        frame.alpha_composite(SH_NEAR[0], (SH_NEAR[1][0] + x - WIN[0], SH_NEAR[1][1] + y - WIN[1]))
        frame.alpha_composite(win, (x, y))
        return
    layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    layer.alpha_composite(SH_FAR[0], (SH_FAR[1][0] + x - WIN[0], SH_FAR[1][1] + y - WIN[1]))
    layer.alpha_composite(win, (x, y))
    a = layer.getchannel("A").point(lambda v: int(v * alpha))
    layer.putalpha(a)
    frame.alpha_composite(layer)


# ---------- mascot ----------
def _load_assets() -> dict[str, Image.Image]:
    """mascot/<mood>.png and optional mascot/<mood>_talk.png; falls back to the pixel Bit."""
    out: dict[str, Image.Image] = {}
    if MASCOT_DIR.exists():
        for p in MASCOT_DIR.glob("*.png"):
            out[p.stem.lower()] = Image.open(p).convert("RGBA")
    return out


ASSETS = _load_assets()


@lru_cache(maxsize=128)
def mascot(mood: str, talk: bool, blink: bool, height: int) -> Image.Image:
    key = f"{mood}_talk" if talk and f"{mood}_talk" in ASSETS else mood
    src = ASSETS.get(key) or ASSETS.get("default") or ASSETS.get("happy")
    if src is None:
        cell = max(2, height // 18)
        return r.bit_img(mood, cell, talk, blink)
    k = height / src.height
    return src.resize((max(1, int(src.width * k)), height), Image.LANCZOS)


MOOD = {0: "happy", 1: "calm", 2: "worried", 3: "thinking", 4: "happy", 5: "calm", 6: "happy", 7: "happy", 8: "happy"}


def draw_presenter(frame, tt: float, i: int, height: int = 250, pos=(150, 1010)):
    li, amp = r.speaking(tt)
    mood = MOOD[i]
    if i == 0 and tt > LINES[0]["start"] + 2.3:
        mood = "worried"
    talk = li is not None and amp > 0.035 and int(tt * 12) % 3 != 2
    blink = (tt % 3.7) < 0.12
    # pop in at the first line, stay on; small bob
    p = ease_back((tt - 0.3) / 0.5)
    if p <= 0:
        return
    h = max(8, int(height * p))
    im = mascot(mood, talk, blink, h)
    bob = math.sin(tt * 2.1) * 5
    x = pos[0] - im.width // 2
    y = int(pos[1] - im.height + bob)
    sh = Image.new("RGBA", (int(height * 0.9), 34), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([0, 6, sh.width, 28], fill=(10, 20, 15, int(55 * p)))
    sh = sh.filter(ImageFilter.GaussianBlur(7))
    frame.alpha_composite(sh, (pos[0] - sh.width // 2, pos[1] - 16))
    frame.alpha_composite(im, (x, y))


# ---------- subtitles ----------
def chunks_for(text: str, max_words: int = 7) -> list[str]:
    words = text.split()
    out, cur = [], []
    for w_ in words:
        cur.append(w_)
        end = w_.endswith((".", ",", "?", "!"))
        if len(cur) >= max_words or (end and len(cur) >= 3):
            out.append(" ".join(cur))
            cur = []
    if cur:
        if out and len(cur) <= 2:
            out[-1] += " " + " ".join(cur)
        else:
            out.append(" ".join(cur))
    return out


SUBS: list[tuple[float, float, str]] = []
for ln in LINES:
    text = ln["text"].replace("Uno Router A P I", "Unorouter API")
    parts = chunks_for(text)
    total = sum(len(p) for p in parts)
    t0 = ln["start"]
    for p in parts:
        d = ln["dur"] * len(p) / total
        SUBS.append((t0, t0 + d, p))
        t0 += d


def draw_subtitle(frame, tt: float):
    for s0, s1, text in SUBS:
        if s0 - 0.05 <= tt < s1 + 0.12:
            a = min(1.0, (tt - (s0 - 0.05)) / 0.12, (s1 + 0.12 - tt) / 0.12)
            tw = F_SUB.getlength(text)
            pad_x, h_ = 30, 66
            cx, cy = W // 2 + 60, 1012
            layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            d.rounded_rectangle([cx - tw / 2 - pad_x, cy - h_ / 2, cx + tw / 2 + pad_x, cy + h_ / 2], radius=10,
                                fill=(14, 20, 17, int(214 * a)))
            d.text((cx, cy + 1), text, font=F_SUB, fill=(255, 255, 255, int(255 * a)), anchor="mm")
            frame.alpha_composite(layer)
            return


# ---------- lower third ----------
CHAPTERS = [  # (scene, number or None, kicker, title)
    (1, "1", "Feature", "Check a message"),
    (3, "2", "Feature", "Practise with a pretend scammer"),
    (5, "3", "Feature", "I need help now"),
    (6, "4", "Feature", "My family"),
    (7, None, "How it works", "Under the hood"),
]


def chapter_at(tt: float):
    best = None
    for sc, num, kick, title in CHAPTERS:
        start = SS[sc] + 0.25
        if sc == 6:
            if tt >= SS[6] + (LINES[6]["start"] - SS[6]) + 2.15:
                num, title, start = "5", "Scams near me", SS[6] + (LINES[6]["start"] - SS[6]) + 2.15
        if tt >= start:
            best = (start, num, kick, title)
    if best is None:
        return None
    start, num, kick, title = best
    # hold a chapter until the next chapter or the outro
    return start, num, kick, title


def draw_lower_third(frame, tt: float):
    if tt >= SS[8] - 0.2:
        return
    ch = chapter_at(tt)
    if not ch:
        return
    start, num, kick, title = ch
    p = ease_out((tt - start) / 0.55)
    if p <= 0:
        return
    x, y = 300, 950 - 860  # sits above the footage, top-left aligned with it
    y = 22
    layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    tx = x
    if num:
        s = 48
        sq_p = ease_back((tt - start) / 0.45)
        sz = int(s * max(0.0, sq_p))
        if sz > 2:
            d.rectangle([x, y + 4 + (s - sz) // 2, x + sz, y + 4 + (s - sz) // 2 + sz], fill=NAVY)
            if sz > s * 0.7:
                d.text((x + s / 2, y + 4 + s / 2), num, font=F_LT_NUM, fill=WHITE, anchor="mm")
        tx = x + s + 16
    full = F_LT.getlength(title)
    # text revealed with a left-to-right wipe
    txt = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(txt)
    td.text((tx, y + 28), title, font=F_LT, fill=INK, anchor="lm")
    wipe = Image.new("L", frame.size, 0)
    ImageDraw.Draw(wipe).rectangle([tx - 4, 0, tx + full * p + 6, y + 60], fill=255)
    txt.putalpha(Image.composite(txt.getchannel("A"), Image.new("L", frame.size, 0), wipe))
    layer.alpha_composite(txt)
    frame.alpha_composite(layer)


# ---------- SMS cold open ----------
def draw_sms(frame, p: float):
    if p <= 0:
        return
    w_, h_ = 920, 236
    x0 = W // 2 - w_ // 2
    y0 = int(150 - (1 - ease_out(p)) * 120)
    a = min(1.0, p * 2.5)
    sh, pos = soft_shadow((x0, y0, x0 + w_, y0 + h_), 30, 30, int(70 * a), 18)
    frame.alpha_composite(sh, pos)
    card = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, w_ - 1, h_ - 1], radius=30, fill=(252, 252, 252, 248), outline=(17, 24, 21, 30))
    d.rounded_rectangle([28, 26, 64, 62], radius=9, fill=(52, 199, 89))
    d.text((80, 44), "Messages", font=F_SMS_APP, fill=MUTED, anchor="lm")
    d.text((w_ - 30, 44), "now", font=F_SMS_APP, fill=MUTED, anchor="rm")
    d.text((30, 98), "Metro Bank", font=F_SMS_T, fill=INK, anchor="lm")
    body = ["Your account has been LOCKED. Reply with the 6-digit", "code within 30 minutes or your account will be closed."]
    for k, ln in enumerate(body):
        d.text((30, 140 + k * 40), ln, font=F_SMS_B, fill=INK, anchor="lm")
    card.putalpha(card.getchannel("A").point(lambda v: int(v * a)))
    frame.alpha_composite(card, (x0, y0))


# ---------- terminal ----------
def terminal_content(st: float) -> Image.Image:
    im = Image.new("RGB", (CW, CH), (24, 29, 27))
    d = ImageDraw.Draw(im)
    shown = int(st / 0.42) + 1
    y = 56
    for p, ln in r.TERM_LINES[:shown]:
        if p == "$":
            d.text((60, y), "$", font=F_MONO_B, fill=(110, 196, 140))
            d.text((92, y), ln, font=F_MONO, fill=(226, 232, 229))
            y += 46
        else:
            ok = "passed" in ln or "axeIssues: 0" in ln or "models" in ln
            d.text((92, y), ("✓  " if ok else "") + ln, font=F_MONO_B, fill=(126, 214, 156) if ok else (150, 190, 240))
            y += 66
    return im


# ---------- end card ----------
def draw_endcard(frame, st: float):
    p = ease_out(st / 0.7)
    im = mascot("happy", *(lambda li_amp: (li_amp[0] is not None and li_amp[1] > 0.035 and int(st * 12) % 3 != 2,))(r.speaking(SS[8] + st)), (st % 3.0) < 0.12, 300)
    bob = math.sin(st * 2.0) * 6
    frame.alpha_composite(im, (W // 2 - im.width // 2, int(120 + (1 - p) * 30 + bob)))
    layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = int(255 * p)
    d.text((W // 2, 560), "Scam Shield", font=F_TITLE, fill=INK + (a,), anchor="mm")
    d.text((W // 2, 660), "Stopping is always a good move.", font=F_TAG, fill=MUTED + (a,), anchor="mm")
    # numbered feature row with hairline separators
    q = ease_out((st - 0.9) / 0.6)
    items = ["Check", "Practise", "Help now", "Family", "Scams near me"]
    widths = [F_ROWN.getlength(str(k + 1)) + 14 + F_ROW.getlength(t) for k, t in enumerate(items)]
    gap = 64
    total = sum(widths) + gap * (len(items) - 1)
    x = W / 2 - total / 2
    y = 790
    aa = int(255 * q)
    d.line([W / 2 - total / 2, y - 46, W / 2 + total / 2, y - 46], fill=(17, 24, 21, int(40 * q)), width=1)
    for k, (t, wd) in enumerate(zip(items, widths)):
        d.text((x, y), str(k + 1), font=F_ROWN, fill=NAVY + (aa,), anchor="lm")
        d.text((x + F_ROWN.getlength(str(k + 1)) + 14, y), t, font=F_ROW, fill=INK + (aa,), anchor="lm")
        x += wd + gap
    d.text((W / 2, 880), "Built for Build Anything with the Unorouter API", font=F_URL, fill=MUTED + (aa,), anchor="mm")
    frame.alpha_composite(layer)


# ---------- compose ----------
def scene_window(i: int, st: float):
    if i == 7:
        return window_image(terminal_content(st), "scam-shield  —  tests", dark=True), None
    name, scroll, zoom, fx, cur, click_t = r.scene_camera(i, st)
    content, (left, top, sc) = page_view(name, scroll, zoom, fx)
    win = window_image(content, "localhost:5173" + r.path_for(name))
    cursor = None
    if cur:
        cursor = (CONTENT[0] + (cur[0] - left) * sc, CONTENT[1] + (cur[1] - top) * sc, st, click_t)
    return win, cursor


XFADE = 0.28


def render(tt: float) -> Image.Image:
    frame = BG.copy()
    i = r.scene_index(tt)
    st = tt - SS[i]
    if i == 8:
        # dissolve from the last footage into the end card
        if st < 0.5:
            win, _ = scene_window(7, tt - SS[7])
            place_window(frame, win, 1.0 - 0.03 * ease(st / 0.5), 1 - ease(st / 0.5))
        draw_endcard(frame, st)
        return frame.convert("RGB")
    # slow push-in over each scene
    push = 1.0 + 0.012 * ease(st / max(0.1, SE[i] - SS[i]))
    win, cursor = scene_window(i, st)
    if i > 0 and st < XFADE:
        prev, _ = scene_window(i - 1, tt - SS[i - 1])
        place_window(frame, prev, 1.012)
        place_window(frame, win, push, ease(st / XFADE))
    else:
        dy = (1 - ease_out(tt / 0.6)) * 30 if i == 0 else 0
        place_window(frame, win, push, 1.0 if i else ease_out(tt / 0.5), dy)
    if cursor:
        r.draw_cursor(frame, *cursor)
    if i == 0:
        draw_sms(frame, (tt - (LINES[0]["start"] + 2.0)) / 0.5)
    draw_lower_third(frame, tt)
    draw_presenter(frame, tt, i)
    draw_subtitle(frame, tt)
    return frame.convert("RGB")


def main():
    if "--preview" in sys.argv:
        out = ROOT / "preview6"
        out.mkdir(exist_ok=True)
        ts = [float(x) for x in sys.argv[2:]] or [1.0, 4.0, 7.2, 12, 18, 22.5, 26, 31, 34.5, 40, 47]
        for tt in ts:
            render(tt).save(out / f"t{tt:05.1f}.png")
        print("preview", TOTAL)
        return
    n = int(TOTAL * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", str(ROOT / "video6.mp4")],
        stdin=subprocess.PIPE,
    )
    for f in range(n):
        ff.stdin.write(render(f / FPS).tobytes())
        if f % 300 == 0:
            print(f"{f}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("done", TOTAL)


if __name__ == "__main__":
    main()
