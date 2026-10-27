"""One picture per run: the tester's screenshots side by side, each labelled with its check and verdict.

  python3 ops/vibe-coding-runs/sheet.py [t1|t2]      # writes out/<task>/<owner__repo>/sheet.jpg

For reviewing the tester's verdicts by eye (review.json), and for the evidence pages.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
TILE_W, TILE_H, LABEL_H, COLS = 640, 560, 28, 4


def tile(shot: Path) -> Image.Image:
    """The top of a full-page screenshot, scaled to the tile width."""
    im = Image.open(shot).convert("RGB")
    scale = TILE_W / im.width
    im = im.resize((TILE_W, round(im.height * scale)))
    return im.crop((0, 0, TILE_W, min(im.height, TILE_H)))


def sheet(run: Path) -> Path | None:
    report_path = run / "test" / "report.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    items = [(c, run / "test" / c["shot"]) for c in report.get("checks", []) if c.get("shot") and (run / "test" / c["shot"]).exists()]
    if not items:
        return None
    rows = -(-len(items) // COLS)
    grid = Image.new("RGB", (TILE_W * min(COLS, len(items)), (TILE_H + LABEL_H) * rows), "white")
    draw, font = ImageDraw.Draw(grid), ImageFont.load_default(size=16)
    for i, (c, shot) in enumerate(items):
        x, y = (i % COLS) * TILE_W, (i // COLS) * (TILE_H + LABEL_H)
        grid.paste(tile(shot), (x, y + LABEL_H))
        ok = bool(c.get("pass"))
        draw.text((x + 8, y + 5), f"{c.get('id')}: {'pass' if ok else 'FAIL'}", fill="#1a7f37" if ok else "#cf222e", font=font)
    out = run / "sheet.jpg"
    grid.save(out, quality=80)
    return out


def main() -> None:
    for task in sys.argv[1:] or ["t1", "t2"]:
        for run in sorted((HERE / "out" / task).glob("*")) if (HERE / "out" / task).exists() else []:
            made = sheet(run)
            print(f"{task} {run.name}: {made or 'no screenshots'}")


if __name__ == "__main__":
    main()
