#!/usr/bin/env python3
"""Genere l'image de partage Open Graph (1200x630) pour le portfolio.

Composition : degrade teal, monogramme JF, nom, metier, pile technique.
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = "/home/kruger/portfolio"
W, H = 1200, 630
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(size, c0, c1, angle="diag"):
    """Degrade lineaire ; 'diag' = diagonal, sinon vertical."""
    w, h = size
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    n = (w + h) if angle == "diag" else h
    for i in range(n):
        d.line([(i, 0), (i, h)] if angle == "diag" else [(0, i), (w, i)], fill=lerp(c0, c1, i / max(n - 1, 1)))
    return img


def radial_glow(size, center, radius, color, strength=1.0):
    """Halo radial doux, dessine sur un calque puis compose en 'lighter'."""
    w, h = size
    layer = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(layer)
    steps = 42
    for i in range(steps, 0, -1):
        r = radius * i / steps
        v = int(255 * (1 - i / steps) ** 2 * strength)
        d.ellipse([center[0] - r, center[1] - r, center[0] + r, center[1] + r], fill=v)
    layer = layer.filter(ImageFilter.GaussianBlur(radius=radius * 0.08))
    glow = Image.new("RGB", (w, h), color)
    return glow, layer


def monogram(img, xy, size, radius_ratio=0.22):
    """Monogramme JF coherent avec favicon.svg."""
    x, y = xy
    pad = int(size * 0.16)
    box = size - pad * 2
    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    grad = gradient((size, size), (15, 118, 110), (20, 184, 166))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=int(size * radius_ratio), fill=255
    )
    tile.paste(grad, (0, 0), mask)

    d = ImageDraw.Draw(tile)
    k = box / 64.0
    ox, oy = x + pad, y + pad
    w = int(round(5.5 * k))
    white = (255, 255, 255, 255)

    def cap_line(x1, y1, x2, y2):
        d.line([(ox + x1 * k, oy + y1 * k), (ox + x2 * k, oy + y2 * k)], fill=white, width=w)
        r = w / 2.0
        for cx, cy in ((x1, y1), (x2, y2)):
            d.ellipse([ox + cx * k - r, oy + cy * k - r, ox + cx * k + r, oy + cy * k + r], fill=white)

    cap_line(20, 21, 30, 21)
    cap_line(25, 21, 25, 47)
    cap_line(38.5, 26, 38.5, 47)
    cap_line(38.5, 21, 45, 21)
    d.arc([ox + (38.5 - 4.6) * k, oy + (26 - 4.6) * k, ox + (38.5 + 4.6) * k, oy + (26 + 4.6) * k],
          90, 180, fill=white, width=w)
    cap_line(38.5, 26, 45, 26)

    img.alpha_composite(tile) if img.mode == "RGBA" else img.paste(tile, (x, y), tile)


def main():
    img = gradient((W, H), (8, 24, 42), (11, 60, 68)).convert("RGBA")

    for center, radius, color, s in (
        ((1080, 90), 620, (20, 184, 166), 0.55),
        ((120, 600), 560, (37, 99, 235), 0.38),
    ):
        glow, mask = radial_glow((W, H), center, radius, color, s)
        img = Image.composite(
            Image.new("RGBA", (W, H), color + (255,)), img, mask
        ).convert("RGBA")
        img = Image.alpha_composite(img, Image.new("RGBA", (W, H)))

    d = ImageDraw.Draw(img)

    # --- badge de disponibilite ---
    badge = (86, 224, 195, 34)
    bx, by, bw, bh = 76, 74, 330, 46
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=bh // 2, fill=badge)
    d.ellipse([bx + 20, by + bh / 2 - 7, bx + 34, by + bh / 2 + 7], fill=(110, 231, 183, 255))
    d.text((bx + 48, by + bh / 2), "DISPONIBLE POUR DE NOUVELLES OPPORTUNITÉS",
           font=ImageFont.truetype(BOLD, 21), fill=(167, 243, 208, 255), anchor="lm")

    # --- monogramme ---
    monogram(img, (76, 168), 132)

    # --- nom + metier ---
    d.text((76, 336), "Abessolo Ovono Jean Freddy",
           font=ImageFont.truetype(BOLD, 68), fill=(255, 255, 255, 255))
    d.text((76, 428), "Développeur Backend  ·  Django / API REST / Java",
           font=ImageFont.truetype(REG, 38), fill=(148, 226, 214, 255))

    # --- pile technique ---
    chips = ["Python", "Django", "PostgreSQL", "Docker", "Linux", "Spring Boot"]
    f = ImageFont.truetype(MONO, 24)
    x, y = 76, 512
    for c in chips:
        w = d.textlength(c, font=f)
        d.rounded_rectangle([x, y, x + w + 34, y + 46], radius=23,
                            fill=(255, 255, 255, 26), outline=(110, 231, 183, 90))
        d.text((x + 17, y + 23), c, font=f, fill=(226, 254, 245, 255), anchor="lm")
        x += w + 34 + 14

    # --- mention de lieu ---
    d.text((W - 76, H - 52), "Bafoussam, Cameroun",
           font=ImageFont.truetype(REG, 26), fill=(190, 214, 226, 200), anchor="rs")

    out = f"{OUT}/og-image.png"
    img.convert("RGB").save(out, "PNG", optimize=True)
    print(f"{os.path.getsize(out) // 1024} Ko  og-image.png  {W}x{H}")


if __name__ == "__main__":
    main()
