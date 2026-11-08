"""Evidence for the 3D page's test (/best/3d-mcp/): each tool's render of the same bakery scene, what was checked
in it, and the test's entry in frontend/scripts/scenario-runs.json ("3d-mcp").

  python3 ops/3d-runs/evidence_3d.py

Writes frontend/public/best-runs/3d/ (WebP copies of the renders, a mosaic of them all, one noindex page per run)
and ops/3d-runs/RESULTS.md. Checked: the sign's text by OCR (score_3d.py), the croissants by counting them in the
scene file (count_objects.py), the size from the file; the counter, loaf, basket, sign, light and view by the judge.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runs_common import WEBP_QUALITY, webp_copy  # noqa: E402 (shared with the other tests' evidence)
from evidence_3d_copy import (CHECKS, COLUMNS, DATE, KIND, NOT_RUN, entry_copy, page, result_cell)  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "out"
DEST = ROOT / "frontend" / "public" / "best-runs" / "3d"
RUNS_JSON = ROOT / "frontend" / "scripts" / "scenario-runs.json"
KEY, DIR = "3d-mcp", "/best-runs/3d/"
URL = "https://github.com/zhuyansen/agent-skills-hub/blob/main/ops/3d-runs/"
SIZE = [1600, 1200]
CROISSANTS = 3
FULL_W, THUMB_W, THUMB_H = 1200, 160, 120     # the render on its page; in the table at this size, from a copy twice as big
TILE_W, TILE_H, LABEL_H, COLS = 320, 240, 18, 5
OUTLINE = "#0969da"                            # the render made with no 3D tool, in the mosaic


def checks(s: dict, croissants: int | None) -> dict:
    """Each item of the brief: True when it is in the render (or the file), False when not."""
    j = s.get("judge") or {}
    return {"counter": j.get("counter_wooden") is True, "loaf": j.get("loaf_round_on_counter") is True,
            "basket": j.get("basket_wicker_on_counter") is True, "croissants": croissants == CROISSANTS,
            "sign": j.get("sign_hanging_behind") is True and (s.get("ocr") or {}).get("sign") is True,
            "light": j.get("light_from_left") is True, "view": j.get("view_above_three_quarter") is True,
            "size": s.get("size") == SIZE, "scene": bool(s.get("scene"))}


def row(c: dict, counts: dict) -> dict | None:
    run = OUT / c["repo"].replace("/", "__")
    if not (run / "score.json").exists():
        return None
    s = json.loads((run / "score.json").read_text())
    if not s.get("render"):
        return None
    ok = checks(s, counts.get(c["repo"]))
    return {"repo": c["repo"], "kind": c["kind"], "stars": c["stars"], "score": s, "checks": ok,
            "missed": [k for k, v in ok.items() if not v], "usage": s["usage"], "judge": s.get("judge") or {},
            "croissants": counts.get(c["repo"]), "commit": (run / "commit.txt").read_text().strip()[:12] if (run / "commit.txt").exists() else ""}


def ordered(rows: list[dict]) -> list[dict]:
    """Every item right first, then fewer misses, the judge's looks, minutes."""
    return sorted(rows, key=lambda r: (len(r["missed"]), -(r["judge"].get("looks") or 0), r["usage"]["minutes"]))


def cells(r: dict) -> list:
    u, looks = r["usage"], r["judge"].get("looks")
    return [result_cell(r["missed"]), [r["judge"].get("sign_read") or "-", r["judge"].get("sign_read") or "-", "" if r["checks"]["sign"] else "substantial"],
            [f"{looks}/5" if looks else "-", f"{looks}/5" if looks else "-", "num"],
            [f"{u['minutes']} min", f"{u['minutes']} 分钟", "num"], [f"${u['cost']:.2f}", f"${u['cost']:.2f}", "num"],
            [", ".join(r["score"]["scene"]) or "-", ", ".join(r["score"]["scene"]) or "-", ""]]


def bits(r: dict) -> list:
    """The card's "Tested" line."""
    head = ["every item of the brief in the render", "测试题里的东西全做出来了"] if not r["missed"] else [
        "missed: " + ", ".join(CHECKS[k][0] for k in r["missed"]), "没做到：" + "、".join(CHECKS[k][1] for k in r["missed"])]
    u = r["usage"]
    return [head, [f"{u['minutes']} min", f"{u['minutes']} 分钟"], [f"${u['cost']:.2f} at API prices", f"按 API 价 ${u['cost']:.2f}"]]


def publish(r: dict) -> dict:
    name = r["repo"].replace("/", "__")
    render = OUT / name / "deliverables" / "render.png"
    w, h = webp_copy(render, DEST / f"{name}.webp", FULL_W)
    webp_copy(render, DEST / f"{name}-thumb.webp", THUMB_W * 2)
    return {"src": f"{name}.webp", "w": w, "h": h}


def card(r: dict) -> dict:
    name = r["repo"].replace("/", "__")
    return {"ran": True, "stars": r["stars"], "minutes": r["usage"]["minutes"], "sheet": f"{name}.html", "group": r["kind"],
            "look": "", "cells": cells(r), "bits": bits(r), "strip": {"src": f"{name}-thumb.webp", "w": THUMB_W, "h": THUMB_H}}


def mosaic(rows: list[dict]) -> dict:
    """Every render in one picture, the one made with no 3D tool first (outlined)."""
    grid = Image.new("RGB", (COLS * TILE_W, -(-len(rows) // COLS) * (TILE_H + LABEL_H)), "white")
    draw = ImageDraw.Draw(grid)
    for i, r in enumerate(rows):
        x, y = (i % COLS) * TILE_W, (i // COLS) * (TILE_H + LABEL_H)
        im = Image.open(OUT / r["repo"].replace("/", "__") / "deliverables" / "render.png").convert("RGB")
        grid.paste(im.resize((TILE_W - 4, TILE_H - 4), Image.LANCZOS), (x + 2, y + LABEL_H + 2))
        draw.text((x + 3, y + 3), ("Claude Code, no 3D tool" if r["repo"] == "control" else r["repo"].split("/")[1])[:44], fill="#1f2328")
        if r["repo"] == "control":
            draw.rectangle((x, y + LABEL_H, x + TILE_W - 1, y + LABEL_H + TILE_H - 1), outline=OUTLINE, width=3)
    grid.save(DEST / "renders.webp", "WEBP", quality=WEBP_QUALITY)
    return {"src": "renders.webp", "w": grid.width, "h": grid.height, "count": len(rows) - 1}


def not_run(c: dict) -> dict:
    en, zh = NOT_RUN[c["repo"]]
    return {"ran": False, "stars": c["stars"], "reason": en, "reason_zh": zh}


def results_md(rows: list[dict], missing: list[dict]) -> str:
    head = (f"# 3D test, {DATE}\n\nGenerated by evidence_3d.py. Brief: in/brief.md. Croissants counted in each scene file "
            "(count_objects.py); the sign read by OCR; the rest checked by gpt-6-astra.\n\n"
            "| Tool | Kind | Missed | Sign read | Looks | Minutes | Cost (API prices) | Scene file |\n|---|---|---|---|---|---|---|---|\n")
    line = lambda r: (f"| {r['repo']} | {KIND.get(r['kind'], ('No 3D tool',))[0]} | {', '.join(r['missed']) or '-'} | {r['judge'].get('sign_read')} | "  # noqa: E731
                      f"{r['judge'].get('looks')}/5 | {r['usage']['minutes']} | ${r['usage']['cost']:.2f} | {', '.join(r['score']['scene'])} |")
    tail = "\n\n## No render\n\n" + "\n".join(f"- {m['repo']}: {NOT_RUN[m['repo']][0]}" for m in missing)
    return head + "\n".join(line(r) for r in rows) + tail + "\n"


def main() -> None:
    cands = json.loads((HERE / "candidates.json").read_text())
    counts = json.loads((HERE / "counts.json").read_text())
    rows = {c["repo"]: row(c, counts) for c in cands}
    missing = [c for c in cands if not rows[c["repo"]] and c["repo"] in NOT_RUN]
    waiting = [c["repo"] for c in cands if not rows[c["repo"]] and c["repo"] not in NOT_RUN]
    control = rows.pop("control")
    tools = ordered([r for r in rows.values() if r])
    for r in [control, *tools]:
        (DEST / f"{r['repo'].replace('/', '__')}.html").write_text(page(r, publish(r)))
    runs = json.loads(RUNS_JSON.read_text())
    runs[KEY] = {**entry_copy(control, tools, len(cands) - 1, mosaic([control, *tools])), "type": "table", "date": DATE, "dir": DIR,
                 "results": URL + "RESULTS.md", "agent": "Claude Code (Claude Opus 5.5)", "judge": "gpt-6-astra",
                 "columns": [list(x) for x in COLUMNS],
                 "runs": {**{r["repo"]: card(r) for r in tools}, **{m["repo"]: not_run(m) for m in missing}}}
    RUNS_JSON.write_text(json.dumps(runs, indent=1, ensure_ascii=False) + "\n")
    (HERE / "RESULTS.md").write_text(results_md([control, *tools], missing))
    print(f"{len(tools)} renders, {len(missing)} without, waiting: {waiting or 'none'}; "
          f"all right: {sum(1 for r in tools if not r['missed'])}")


if __name__ == "__main__":
    main()
