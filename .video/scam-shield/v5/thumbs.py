"""Thumbnails for Second Look (formerly Scam Shield).
- project_3x2.png : 2400x1600, hackathon project overview (< 5 MB)
- youtube_16x9.jpg: 1280x720, YouTube (< 2 MB)
Uses the real Result capture and the mascot (mascot/*.png if present, else pixel Bit)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import render as r

ROOT = Path(__file__).resolve().parent
OUT = Path.home() / "hackathon" / "docs" / "brand"
OUT.mkdir(parents=True, exist_ok=True)
F = ROOT / "fonts"

NAVY_DEEP = (8, 33, 60)
NAVY = (10, 77, 140)
GOLD = (232, 185, 49)
INK = (17, 24, 21)
WHITE = (255, 255, 255)
RED = (196, 38, 38)
HIGHLIGHT = (255, 224, 102)


def inter(size, weight="Bold"):
    f = ImageFont.truetype(str(F / "Inter.ttf"), size)
    f.set_variation_by_name(weight)
    return f


def serif(size, weight="Bold"):
    f = ImageFont.truetype(str(F / "SourceSerif4.ttf"), size)
    f.set_variation_by_name(weight)
    return f


def mascot(height: int, mood: str = "happy") -> Image.Image:
    d = ROOT / "mascot"
    if d.exists():
        for name in (mood, "default", "happy"):
            p = d / f"{name}.png"
            if p.exists():
                im = Image.open(p).convert("RGBA")
                return im.resize((int(im.width * height / im.height), height), Image.LANCZOS)
    cell = height // 18
    return r.bit_img(mood, cell, False, False)


def shadow(size, box, radius, blur, alpha, dy=0, color=(0, 0, 0)):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    ImageDraw.Draw(im).rounded_rectangle([x0, y0 + dy, x1, y1 + dy], radius=radius, fill=color + (alpha,))
    return im.filter(ImageFilter.GaussianBlur(blur))


def vertical_gradient(size, top, bottom):
    w, h = size
    im = Image.new("RGB", size)
    d = ImageDraw.Draw(im)
    for y in range(h):
        k = y / (h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * k) for a, b in zip(top, bottom)))
    return im.convert("RGBA")


def browser(content: Image.Image, width: int, url: str) -> Image.Image:
    bar = int(width * 0.045)
    k = width / content.width
    body = content.resize((width, int(content.height * k)), Image.LANCZOS)
    h = bar + body.height
    win = Image.new("RGBA", (width, h), WHITE + (255,))
    d = ImageDraw.Draw(win)
    d.rectangle([0, 0, width, bar], fill=(243, 244, 245))
    d.line([0, bar, width, bar], fill=(222, 225, 228), width=2)
    for i in range(3):
        cx = bar * 0.6 + i * bar * 0.5
        d.ellipse([cx - bar * 0.14, bar / 2 - bar * 0.14, cx + bar * 0.14, bar / 2 + bar * 0.14], fill=(208, 211, 214))
    pw = width * 0.42
    d.rounded_rectangle([width / 2 - pw / 2, bar * 0.2, width / 2 + pw / 2, bar * 0.8], radius=bar * 0.18, fill=WHITE, outline=(226, 229, 232))
    d.text((width / 2, bar / 2), url, font=inter(int(bar * 0.36), "Medium"), fill=(88, 100, 94), anchor="mm")
    win.paste(body, (0, bar))
    mask = Image.new("L", win.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, width - 1, h - 1], radius=int(width * 0.018), fill=255)
    out = Image.new("RGBA", win.size, (0, 0, 0, 0))
    out.paste(win, (0, 0), mask)
    return out


# ---------------------------------------------------------------- 3:2 project card
def project_card():
    W, H = 2400, 1600
    im = vertical_gradient((W, H), (11, 42, 76), NAVY_DEEP)
    # one quiet accent: a large soft glow behind the product shot
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([1250, 150, 2550, 1450], fill=(40, 110, 190, 70))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(160)))
    d = ImageDraw.Draw(im)

    # product shot: the real Result screen
    res = Image.open(ROOT / "cap" / "result.png").convert("RGB")
    crop = res.crop((190, 640, 1610, 1760))  # risk box, Bit, marked phrases
    win = browser(crop, 1000, "localhost:5173/check/result")
    wx, wy = 1270, 330
    im.alpha_composite(shadow((W, H), (wx, wy, wx + win.width, wy + win.height), 24, 50, 150, 40))
    im.alpha_composite(win, (wx, wy))

    # mascot overlapping the window corner
    m = mascot(400, "happy")
    mx, my = wx + win.width - m.width + 70, wy + win.height - m.height + 190
    im.alpha_composite(shadow((W, H), (mx + 30, my + m.height - 30, mx + m.width - 30, my + m.height + 6), 40, 22, 140))
    im.alpha_composite(m, (mx, my))

    # wordmark
    x = 150
    icon = r.bit_img("calm", 5, False, False)
    im.alpha_composite(icon, (x, 150))
    d.text((x + icon.width + 24, 150 + icon.height / 2), "Second Look", font=serif(54), fill=WHITE, anchor="lm")

    # headline
    y = 380
    for line in ["Every scam", "falls apart on", "a second look."]:
        d.text((x, y), line, font=serif(132), fill=WHITE)
        y += 150
    d.rectangle([x, y + 40, x + 120, y + 48], fill=GOLD)
    body = inter(40, "Regular")
    y += 100
    for line in ["A calm scam coach for older adults.", "Check a message, practise with a pretend", "scammer, and get help in the moment."]:
        d.text((x, y), line, font=body, fill=(206, 219, 233))
        y += 58

    # numbered features
    y = 1340
    chip_f, num_f = inter(30, "SemiBold"), inter(28, "Bold")
    chips = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(chips)
    cx = x
    for n, label in enumerate(["Check", "Practise", "Help now", "Family", "Scams near me"], 1):
        tw = chip_f.getlength(label)
        wdt = 56 + 14 + tw + 30
        d.rounded_rectangle([cx, y, cx + wdt, y + 64], radius=32, fill=(255, 255, 255, 18), outline=(255, 255, 255, 60), width=2)
        d.ellipse([cx + 10, y + 10, cx + 54, y + 54], fill=GOLD)
        d.text((cx + 32, y + 33), str(n), font=num_f, fill=NAVY_DEEP, anchor="mm")
        d.text((cx + 68, y + 32), label, font=chip_f, fill=WHITE, anchor="lm")
        cx += wdt + 18
    im.alpha_composite(chips)
    d = ImageDraw.Draw(im)
    d.text((W - 150, 1500), "Built with the Unorouter API", font=inter(28, "Medium"), fill=(150, 175, 205), anchor="rm")
    d.text((x, 1500), "Build Anything hackathon, 2026", font=inter(28, "Medium"), fill=(150, 175, 205), anchor="lm")

    out = OUT / "second-look-project-3x2.png"
    im.convert("RGB").save(out, optimize=True)
    return out


# ---------------------------------------------------------------- YouTube 16:9
def youtube():
    W, H = 1280, 720
    im = vertical_gradient((W, H), (14, 22, 19), (24, 36, 31))
    d = ImageDraw.Draw(im)

    # the scam text, big, as a phone notification with red-marked phrases
    cx0, cy0, cw, ch = 60, 120, 640, 330
    im.alpha_composite(shadow((W, H), (cx0, cy0, cx0 + cw, cy0 + ch), 28, 30, 160, 20))
    d.rounded_rectangle([cx0, cy0, cx0 + cw, cy0 + ch], radius=28, fill=(250, 250, 250))
    d.rounded_rectangle([cx0 + 26, cy0 + 24, cx0 + 60, cy0 + 58], radius=8, fill=(52, 199, 89))
    d.text((cx0 + 74, cy0 + 41), "Messages", font=inter(22, "SemiBold"), fill=(110, 118, 114), anchor="lm")
    d.text((cx0 + cw - 26, cy0 + 41), "now", font=inter(22, "SemiBold"), fill=(110, 118, 114), anchor="rm")
    d.text((cx0 + 28, cy0 + 96), "Metro Bank", font=inter(36, "Bold"), fill=INK, anchor="lm")
    bf = inter(34, "Medium")
    rows = [
        [("Your account has been ", False), ("LOCKED.", True)],
        [("Reply with the ", False), ("6-digit code", True)],
        [("within ", False), ("30 minutes", True), (" or it", False)],
        [("will be closed.", False)],
    ]
    ty = cy0 + 150
    for row in rows:
        tx = cx0 + 28
        for text, mark in row:
            wdt = bf.getlength(text)
            if mark:
                d.rectangle([tx - 4, ty - 22, tx + wdt + 4, ty + 22], fill=HIGHLIGHT)
                d.line([tx - 4, ty + 22, tx + wdt + 4, ty + 22], fill=RED, width=4)
            d.text((tx, ty), text, font=bf, fill=INK, anchor="lm")
            tx += wdt
        ty += 52

    # verdict badge, straight (not a rotated rubber stamp)
    bx, by = cx0 + 28, cy0 + ch + 34
    vf = inter(40, "Black")
    vw = vf.getlength("LIKELY A SCAM") + 80
    d.rounded_rectangle([bx, by, bx + vw, by + 74], radius=14, fill=RED)
    d.ellipse([bx + 22, by + 25, bx + 46, by + 49], fill=WHITE)
    d.text((bx + 60, by + 38), "LIKELY A SCAM", font=vf, fill=WHITE, anchor="lm")

    # headline: 4 words, huge
    hf = inter(112, "Black")
    d.text((770, 96), "Would", font=hf, fill=WHITE)
    d.text((770, 210), "you", font=hf, fill=WHITE)
    d.text((770, 324), "reply?", font=hf, fill=GOLD)

    # mascot, worried, bottom right, under the headline
    m = mascot(230, "worried")
    im.alpha_composite(m, (W - m.width - 70, H - m.height - 24))

    # brand
    icon = r.bit_img("calm", 2, False, False)
    im.alpha_composite(icon, (60, 40))
    d.text((60 + icon.width + 12, 40 + icon.height / 2), "Second Look", font=serif(34), fill=WHITE, anchor="lm")

    out = OUT / "second-look-youtube-16x9.jpg"
    im.convert("RGB").save(out, quality=92, optimize=True)
    return out


if __name__ == "__main__":
    for p in (project_card(), youtube()):
        print(p, round(p.stat().st_size / 1e6, 2), "MB", Image.open(p).size)
