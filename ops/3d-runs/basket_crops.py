"""Crops of the basket in each render, for counting the croissants by hand (review.json): the judge reads what
it expects and said 3 for 8 of 9 renders (11-09). The judge only finds the basket here; a person counts.

  python3 ops/3d-runs/basket_crops.py <sheet.jpg> [owner/repo ...]   # default: every run with a render
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "image-runs"))
from score_image import ask, env  # noqa: E402 (the judge call)

OUT = HERE / "out"
BOX_Q = ("Find the basket (the one holding croissants or pastries) in this render. Return {\"box\": [x0, y0, x1, y1]} "
         "in pixels of this 1600 x 1200 image, with a margin of about 40 pixels around the basket, or {\"box\": null}. ")
CROP = (420, 300)   # each crop on the sheet
MARGIN = 40


def box(e: dict, render: Path) -> list[int] | None:
    b = ask(e, BOX_Q, [render]).get("box")
    return [int(v) for v in b] if b and len(b) == 4 else None


def main() -> None:
    e, sheet_path = env(), Path(sys.argv[1])
    names = [a.replace("/", "__") for a in sys.argv[2:]]
    runs = [OUT / n for n in names] if names else sorted(p.parent.parent for p in OUT.glob("*/deliverables/render.png"))
    crops = []
    for run in runs:
        render = run / "deliverables" / "render.png"
        b = box(e, render)
        im = Image.open(render).convert("RGB")
        crop = im.crop((max(0, b[0] - MARGIN), max(0, b[1] - MARGIN), min(im.width, b[2] + MARGIN), min(im.height, b[3] + MARGIN))) if b else im
        crop.thumbnail(CROP)
        crops.append((run.name, crop))
        print(run.name, b, flush=True)
    cols = 3
    sheet = Image.new("RGB", (cols * CROP[0], -(-len(crops) // cols) * (CROP[1] + 20)), "white")
    d = ImageDraw.Draw(sheet)
    for i, (name, c) in enumerate(crops):
        x, y = (i % cols) * CROP[0], (i // cols) * (CROP[1] + 20)
        sheet.paste(c, (x, y + 20))
        d.text((x + 3, y + 3), name[:56], fill="black")
    sheet.save(sheet_path, quality=88)


if __name__ == "__main__":
    main()
