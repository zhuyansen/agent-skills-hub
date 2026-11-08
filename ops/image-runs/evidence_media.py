"""The pictures the image test publishes (frontend/public/best-runs/image/), from the runs' deliverables.

Web copies for the evidence pages, a strip of all six per run for the results table, a bigger
strip of three for the picks, the model line-up's posters, and one picture of every poster.
Rendered at twice the size they are shown, so they stay sharp on high-density screens.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FILES = ("poster", "product", "mascot-1", "mascot-2", "mascot-3", "mascot-4")
PICK_FILES = ("poster", "mascot-1", "product")
WEB_LONG_SIDE = {"poster": 680}          # the poster's six lines must stay readable
WEB_LONG_SIDE_DEFAULT = 448
STRIP_HEIGHT, PICK_HEIGHT, MODEL_HEIGHT = 44, 150, 60   # as shown on the page, in CSS pixels
STRIP_MAX_WIDTH = 264                                    # the results table's first column is 266px
SCALE = 2
GAP = 4
WEBP_QUALITY = 78
MOSAIC_COLS, MOSAIC_W, MOSAIC_H = 12, 150, 200
MARK = (207, 34, 46)


def find(folder: Path, stem: str) -> Path | None:
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (folder / f"{stem}{ext}").exists():
            return folder / f"{stem}{ext}"
    return None


def load(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def fit_long_side(im: Image.Image, long_side: int) -> Image.Image:
    scale = long_side / max(im.size)
    return im if scale >= 1 else im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)


def fit_height(im: Image.Image, height: int) -> Image.Image:
    return im.resize((max(1, round(im.width * height / im.height)), height), Image.LANCZOS)


def web_copies(folder: Path, dest: Path, key: str) -> dict:
    """<key>-<file>.webp for each picture the run delivered; {file: (width, height)} of the originals."""
    sizes = {}
    for stem in FILES:
        src = find(folder, stem)
        if not src:
            continue
        im = load(src)
        sizes[stem] = im.size
        fit_long_side(im, WEB_LONG_SIDE.get(stem, WEB_LONG_SIDE_DEFAULT)).save(dest / f"{key}-{stem}.webp", quality=WEBP_QUALITY)
    return sizes


def strip(folder: Path, out: Path, stems: tuple, height: int, max_width: int | None = None) -> tuple[int, int] | None:
    """The run's pictures side by side at one height; returns the size to show it at, or None."""
    ims = [fit_height(load(p), height * SCALE) for p in (find(folder, s) for s in stems) if p]
    if not ims:
        return None
    width = sum(im.width for im in ims) + GAP * SCALE * (len(ims) - 1)
    canvas = Image.new("RGB", (width, height * SCALE), "white")
    x = 0
    for im in ims:
        canvas.paste(im, (x, 0))
        x += im.width + GAP * SCALE
    if max_width and width > max_width * SCALE:   # an all-landscape set would widen the table's first column
        canvas = canvas.resize((max_width * SCALE, round(canvas.height * max_width * SCALE / width)), Image.LANCZOS)
    canvas.save(out, quality=WEBP_QUALITY - 6)
    return round(canvas.width / SCALE), round(canvas.height / SCALE)


def model_images(src: Path, dest: Path, stem: str) -> tuple[int, int]:
    """A model's poster: a thumbnail for the table and a web copy to open; returns the thumbnail's shown size."""
    im = load(src)
    fit_long_side(im, WEB_LONG_SIDE["poster"]).save(dest / f"{stem}.webp", quality=WEBP_QUALITY)
    thumb = fit_height(im, MODEL_HEIGHT * SCALE)
    thumb.save(dest / f"{stem}-thumb.webp", quality=WEBP_QUALITY - 6)
    return round(thumb.width / SCALE), MODEL_HEIGHT


def poster_mosaic(posters: list[Path], out: Path, label: str) -> tuple[int, int]:
    """Every poster in one picture, the first (the control) outlined and labelled."""
    rows = -(-len(posters) // MOSAIC_COLS)
    canvas = Image.new("RGB", (MOSAIC_COLS * MOSAIC_W, rows * MOSAIC_H), "white")
    draw = ImageDraw.Draw(canvas)
    for i, p in enumerate(posters):
        im = load(p)
        im.thumbnail((MOSAIC_W - 6, MOSAIC_H - 6))
        x, y = (i % MOSAIC_COLS) * MOSAIC_W, (i // MOSAIC_COLS) * MOSAIC_H
        canvas.paste(im, (x + (MOSAIC_W - im.width) // 2, y + (MOSAIC_H - im.height) // 2))
    draw.rectangle([1, 1, MOSAIC_W - 2, MOSAIC_H - 2], outline=MARK, width=5)
    font = ImageFont.load_default(size=18)
    draw.rectangle([6, MOSAIC_H - 30, 6 + int(draw.textlength(label, font=font)) + 10, MOSAIC_H - 8], fill=MARK)
    draw.text((11, MOSAIC_H - 29), label, fill="white", font=font)
    canvas.save(out, quality=80)
    return canvas.size
