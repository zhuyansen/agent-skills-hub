"""Side-by-side comparison images for the PPT page and the GitHub list: the same slide
from every deck that ran, in the page's order (rework, then editability, then rubric).

  python ops/ppt-runs/compare.py

The routes slide ("205 PPT skills, three routes") is the one piece of the brief every
deck had to show with the same numbers, so it compares like with like; the judge noted
its slide number when answering the rubric (completeness item 5). SLIDE_FIX overrides a
number after looking at the slides. Writes frontend/public/best-runs/ppt/compare-routes.jpg,
compare-covers.jpg and per-deck thumbs/<repo>-routes.jpg (the table's thumbnail).
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
OUT = HERE / "out"
PUBLIC = HERE.parents[1] / "frontend/public/best-runs/ppt"
COLS, TILE_W, TILE_H, CAPTION_H, GAP, MARGIN = 4, 400, 225, 54, 16, 24
REWORK_RANK = {"touch-ups": 0, "one round": 1, "substantial": 2}
REWORK = {"touch-ups": "小修即可交付 · touch-ups", "one round": "要改一轮 · one round", "substantial": "要大改 · substantial"}
REWORK_COLOR = {"touch-ups": (26, 127, 55), "one round": (154, 103, 0), "substantial": (207, 34, 46)}
SLIDE_FIX: dict[str, int] = {}   # repo -> routes slide number, where the judge's number was off
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"   # macOS; any CJK font works


def pages(run: Path) -> list[Path]:
    return sorted(run.glob("pages/p-*.png"), key=lambda p: int("".join(filter(str.isdigit, p.stem))))


def routes_slide(repo: str, run: Path) -> int:
    if repo in SLIDE_FIX:
        return SLIDE_FIX[repo]
    answer = json.loads((run / "checklist.json").read_text())["dimensions"]["completeness"]["answers"][4]
    return int(answer.get("slide") or 6)


def tile(img: Path, row: dict, fonts) -> Image.Image:
    t = Image.new("RGB", (TILE_W, TILE_H + CAPTION_H), "white")
    im = Image.open(img).convert("RGB")
    im.thumbnail((TILE_W, TILE_H))
    t.paste(im, ((TILE_W - im.width) // 2, (TILE_H - im.height) // 2))
    d = ImageDraw.Draw(t)
    d.rectangle([0, 0, TILE_W - 1, TILE_H - 1], outline=(208, 215, 222))
    name = row["repo"].split("/")[1]
    d.text((4, TILE_H + 6), f"{name}  ★{row['stars']:,}", fill=(31, 35, 40), font=fonts[0])
    d.text((4, TILE_H + 30), REWORK[row["rework"]], fill=REWORK_COLOR[row["rework"]], font=fonts[1])
    right = f"L{row['pei']} · {round(row['checklist'] * 100)}%"
    w = d.textlength(right, font=fonts[1])
    d.text((TILE_W - 4 - w, TILE_H + 30), right, fill=(89, 99, 110), font=fonts[1])
    return t


def grid(tiles: list[Image.Image], path: Path) -> None:
    rows = (len(tiles) + COLS - 1) // COLS
    w = MARGIN * 2 + COLS * TILE_W + (COLS - 1) * GAP
    h = MARGIN * 2 + rows * (TILE_H + CAPTION_H) + (rows - 1) * GAP
    sheet = Image.new("RGB", (w, h), "white")
    for i, t in enumerate(tiles):
        sheet.paste(t, (MARGIN + (i % COLS) * (TILE_W + GAP), MARGIN + (i // COLS) * (TILE_H + CAPTION_H + GAP)))
    sheet.save(path, quality=80, optimize=True)


def main() -> None:
    rows = [r for r in json.loads((HERE / "results.json").read_text())
            if r["ran"] and not r["repo"].endswith("image-to-editable-ppt-skill")]   # the converter did another task
    rows.sort(key=lambda r: (REWORK_RANK.get(r["rework"], 9), -(r["pei"] or 0), -(r["checklist"] or 0)))
    fonts = (ImageFont.truetype(FONT, 17), ImageFont.truetype(FONT, 15))
    routes, covers = [], []
    for r in rows:
        run = OUT / r["repo"].replace("/", "__")
        ps = pages(run)
        slide = ps[min(routes_slide(r["repo"], run), len(ps)) - 1]
        routes.append(tile(slide, r, fonts)); covers.append(tile(ps[0], r, fonts))
        th = Image.open(slide).convert("RGB"); th.thumbnail((240, 135))
        th.save(PUBLIC / "thumbs" / (r["repo"].replace("/", "__") + "-routes.jpg"), quality=78, optimize=True)
    grid(routes, PUBLIC / "compare-routes.jpg")
    grid(covers, PUBLIC / "compare-covers.jpg")
    print(f"{len(rows)} decks -> compare-routes.jpg, compare-covers.jpg")


if __name__ == "__main__":
    main()
