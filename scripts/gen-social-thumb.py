#!/usr/bin/env python3
"""
Generate the Open Graph social thumbnail (1200x630) for the portfolio.

Layout reverse-engineered from the original committed thumb:
- Background: #111213
- Circular avatar on the left, center (263, 311), radius 118
- Name: bold sans, white, cap-height 62, baseline y=314, left x=426
- Headline: serif, white, total ink height ~34, cap-top y=361, left x=426

WARNING: the live committed social-thumb.png is hand-made with Geist (by
Pablo, in a design tool), NOT produced by this script. This script only
renders an Arial Bold / Georgia approximation, because Geist is not installed
as a system font. Do NOT run it to "regenerate" the live thumb: it would
overwrite the Geist version with the fallback. Use it as a quick draft only,
then redo the final in Geist. Keep NAME / HEADLINE in sync with profile.md.
"""
from PIL import Image, ImageDraw, ImageFont

NAME = "Pablo Roccella"
HEADLINE = "Design Engineer & Product Builder"
AVATAR = "/Users/iwa/repos/portfolio/media/2026-avatar.png"
OUT = "/Users/iwa/repos/portfolio/media/social-thumb.png"

W, H = 1200, 630
BG = (17, 18, 19)
WHITE = (255, 255, 255)
CX, CY, R = 263, 311, 118
LEFT = 426
NAME_BASELINE = 314
NAME_CAP_H = 62
NAME_CAP_TOP = NAME_BASELINE - NAME_CAP_H  # 252
HEAD_CAP_TOP = 361
HEAD_TOTAL_H = 34

NAME_FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
HEAD_FONT = "/System/Library/Fonts/Supplemental/Georgia.ttf"


def ink_image(text, font):
    """Render text on transparent canvas, return (cropped_rgba, bbox_size)."""
    tmp = Image.new("RGBA", (4000, 400), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    d.text((10, 200), text, font=font, fill=WHITE)
    bbox = tmp.getbbox()
    return tmp.crop(bbox), (bbox[2] - bbox[0], bbox[3] - bbox[1])


def fit_font(path, text, target_h, which, start=80):
    """Pick a font size so rendered ink height of `text` matches target_h."""
    size = start
    for _ in range(8):
        f = ImageFont.truetype(path, size)
        _, (w, h) = ink_image(text, f)
        meas = h if which == "total" else h
        if abs(meas - target_h) <= 1:
            break
        size = max(6, round(size * target_h / max(meas, 1)))
    return ImageFont.truetype(path, size), size


img = Image.new("RGB", (W, H), BG)

# Avatar: cover-fit into a circle with supersampled antialiased mask
av = Image.open(AVATAR).convert("RGB")
d = 2 * R
aw, ah = av.size
scale = max(d / aw, d / ah)
av = av.resize((round(aw * scale), round(ah * scale)), Image.LANCZOS)
aw, ah = av.size
av = av.crop(((aw - d) // 2, (ah - d) // 2, (aw - d) // 2 + d, (ah - d) // 2 + d))
ss = 4
mask = Image.new("L", (d * ss, d * ss), 0)
ImageDraw.Draw(mask).ellipse((0, 0, d * ss, d * ss), fill=255)
mask = mask.resize((d, d), Image.LANCZOS)
img.paste(av, (CX - R, CY - R), mask)

draw = ImageDraw.Draw(img)

# Name: match cap-height (no descenders in "Pablo Roccella")
name_font, name_size = fit_font(NAME_FONT, NAME, NAME_CAP_H, "cap", start=88)
name_ink, _ = ink_image(NAME, name_font)
img.paste(name_ink, (LEFT, NAME_CAP_TOP), name_ink)

# Headline: match total ink height (has ascenders + descenders)
head_font, head_size = fit_font(HEAD_FONT, HEADLINE, HEAD_TOTAL_H, "total", start=38)
head_ink, _ = ink_image(HEADLINE, head_font)
img.paste(head_ink, (LEFT, HEAD_CAP_TOP), head_ink)

img.save(OUT)
print(f"saved {OUT}  name_size={name_size}  head_size={head_size}")
