#!/usr/bin/env python3
"""Prepare les captures d'ecran des projets pour le portfolio.

Pour chaque source : redimensionne a une largeur lisible, compresse en JPEG et
genere un LQIP (tiny blurred base64) utilise comme fond pendant le chargement.
Les LQIP sont ecrits dans assets/projects/lqip.json pour injection dans le HTML.
"""
import json
import os

from PIL import Image, ImageFilter

OUT = "/home/kruger/portfolio/assets/projects"
MAX_W = 1000
QUALITY = 82

# slug -> (source, legende alternative)
SOURCES = {
    "supervision-ia": (
        "/home/kruger/Supervision/Supervision_Monitoring_App/"
        "rapport_supervision_monitoring_app/figures/figure_5.png",
        "Console de supervision : analyse IA d'un incident et recommandations operationnelles",
    ),
    "salon-mobilier": (
        "/home/kruger/salon-mobilier/docs/captures/dashboard.png",
        "Tableau de bord Salon Mobilier : chiffre d'affaires, commandes en cours et stock faible",
    ),
    "gestion-vente": (
        "/home/kruger/vente_captures/02_accueil.png",
        "Tableau de bord commercial du module de vente : ventes du jour, creances et alertes de stock",
    ),
}


def lqip(img, path, width=18):
    """Ecrit un mini JPEG flou (~300 o) servant de fond 'blur-up' de la capture."""
    w, h = img.size
    small = img.convert("RGB").resize((width, max(1, round(h * width / w))), Image.LANCZOS)
    small = small.filter(ImageFilter.GaussianBlur(radius=1.2))
    small.save(path, format="JPEG", quality=40, optimize=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = {}

    for slug, (src, alt) in SOURCES.items():
        if not os.path.exists(src):
            print(f"! source absente, ignore : {src}")
            continue

        im = Image.open(src)
        if im.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", im.size, (255, 255, 255))
            im = im.convert("RGBA")
            bg.paste(im, mask=im.split()[-1])
            im = bg

        if im.width > MAX_W:
            im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)

        dest = f"{OUT}/{slug}.jpg"
        im.save(dest, format="JPEG", quality=QUALITY, optimize=True, progressive=True)
        lqip(im, f"{OUT}/{slug}-lqip.jpg")
        manifest[slug] = {
            "src": f"assets/projects/{slug}.jpg",
            "lqip": f"assets/projects/{slug}-lqip.jpg",
            "alt": alt,
            "w": im.width,
            "h": im.height,
        }
        print(f"{os.path.getsize(dest) // 1024:>4} Ko  {im.width}x{im.height}  {slug}.jpg")

    with open(f"{OUT}/lqip.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\nlqip.json : {len(manifest)} captures")


if __name__ == "__main__":
    main()
