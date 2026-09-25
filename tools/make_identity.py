#!/usr/bin/env python3
"""Genere les assets d'identite du portfolio (favicon / apple-touch-icon / logo).
Monogramme 'JF' sur degrade teal, meme geometrie que favicon.svg."""
import os

from PIL import Image, ImageDraw

OUT = "/home/kruger/portfolio"
S = 8  # supersampling pour l'antialiasing


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def render(size, radius_ratio=0.22, bg=True):
    """Rend le monogramme a la taille demandee."""
    n = size * S
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    if bg:
        # degrade diagonal teal (#0f766e -> #14b8a6)
        c0, c1 = (15, 118, 110), (20, 184, 166)
        grad = Image.new("RGB", (n, n))
        gd = ImageDraw.Draw(grad)
        for i in range(n):
            gd.line([(i, 0), (i, n)], fill=lerp(c0, c1, i / max(n - 1, 1)))
        mask = Image.new("L", (n, n), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [0, 0, n - 1, n - 1], radius=int(n * radius_ratio), fill=255
        )
        img.paste(grad, (0, 0), mask)

    # --- monogramme : coordonnees du viewBox 64x64 mises a l'echelle ---
    k = n / 64.0
    w = 5.5 * k
    white = (255, 255, 255, 255)

    def cap_line(x1, y1, x2, y2):
        """Segment a extremites rondes."""
        d.line([(x1 * k, y1 * k), (x2 * k, y2 * k)], fill=white, width=int(round(w)))
        r = w / 2.0
        for cx, cy in ((x1, y1), (x2, y2)):
            d.ellipse([cx * k - r, cy * k - r, cx * k + r, cy * k + r], fill=white)

    def cap_arc(cx, cy, r, a0, a1):
        """Arc (encoche du F) a extremites rondes."""
        d.arc(
            [(cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k],
            a0, a1, fill=white, width=int(round(w)),
        )

    # J : barre horizontale + hampe verticale
    cap_line(20, 21, 30, 21)
    cap_line(25, 21, 25, 47)
    # F : hampe verticale, barre du haut, encoette arrondie vers la gauche
    cap_line(38.5, 26, 38.5, 47)
    cap_line(38.5, 21, 45, 21)
    cap_arc(38.5, 26, 4.6, 90, 180)
    cap_line(38.5, 26, 45, 26)  # raccord de l'encoette

    return img.resize((size, size), Image.LANCZOS)


def main():
    # Favicons
    render(16).save(f"{OUT}/favicon-16.png")
    render(32).save(f"{OUT}/favicon-32.png")
    render(48).save(f"{OUT}/favicon-48.png")

    # ICO multi-tailles (le .ico embarque lui-meme le PNG 32x32)
    render(64).save(
        f"{OUT}/favicon.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)],
    )

    # Apple touch icon : fond plein, pas de coins arrondis (iOS applique les siens)
    render(180, radius_ratio=0.0, bg=True).save(f"{OUT}/apple-touch-icon.png")

    # Logo lisible pour la nav et le profil
    render(96).save(f"{OUT}/icons/logo-96.png")

    for f in ("favicon-16.png", "favicon-32.png", "favicon-48.png", "favicon.ico",
              "apple-touch-icon.png", "icons/logo-96.png"):
        p = os.path.join(OUT, f)
        print(f"{os.path.getsize(p):>7} o  {f}")


if __name__ == "__main__":
    main()
