"""One line per scored image run (ops/image-runs/out/*/score.json), the control first.

  python3 ops/image-runs/summary.py            # table
  python3 ops/image-runs/summary.py --json     # the same rows as JSON
  python3 ops/image-runs/summary.py --review   # the text still waiting for a look by hand

Text: text_check.line_verdict() per line, from OCR, the judge and the looks by hand in text_review.json
("6" = six lines right; "5 1?" = five right, one waiting for a look). fmt: how many of the six files have
the brief's shape (poster 3:4 portrait, the rest square). oth: the judge saw other text on the poster.
The mascot set is the judge's (same character 1-5, poses right of 4, hat and scarf in all, text on any),
except where text_review.json overrides "text on any" (Zzz sleep marks are a symbol, not text).
Cost is what the image calls cost on APIMart; the agent's own tokens (Claude subscription) are not counted.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
sys.path.insert(0, str(HERE))
from text_check import LINES, line_verdict  # noqa: E402

REVIEWS = json.loads((HERE / "text_review.json").read_text())


def text_verdicts(repo: str, ocr: dict, judge: dict) -> dict:
    """{"poster": [verdict per line] or None, "bag": verdict or None}."""
    hand = REVIEWS.get(repo, {})
    out = {"poster": None, "bag": None}
    if ocr.get("poster_found") is not None:
        jl = (judge.get("poster") or {}).get("lines") or []
        jx = [bool(jl[i].get("exact")) if i < len(jl) else None for i in range(len(LINES))]
        out["poster"] = [line_verdict(h, d, jx[i], hand.get("poster", {}).get(str(i)))
                         for i, (h, d) in enumerate(zip(ocr["poster_found"], ocr.get("poster_distance") or [99] * 6))]
    if ocr.get("bag_name") is not None:
        out["bag"] = line_verdict(ocr["bag_name"], ocr.get("bag_distance", 99),
                                  (judge.get("product") or {}).get("name_exact"), hand.get("bag"))
    return out


RATIO_TOLERANCE = 0.03   # 768x1024 and 896x1200 are both 3:4; 1024x1536 (2:3) is not


def shape(run: Path) -> dict:
    """The brief's formats, from the files: the poster portrait 3:4, the other five square."""
    from PIL import Image
    out = {}
    for stem, want in (("poster", 4 / 3), ("product", 1.0), ("mascot-1", 1.0), ("mascot-2", 1.0), ("mascot-3", 1.0), ("mascot-4", 1.0)):
        files = sorted((run / "deliverables").glob(stem + ".*")) if (run / "deliverables").exists() else []
        if files:
            w, h = Image.open(files[0]).size
            out[stem] = {"size": f"{w}x{h}", "ok": abs(h / w - want) <= RATIO_TOLERANCE * want}
    return out


def row(run: Path) -> dict:
    s = json.loads((run / "score.json").read_text())
    j, m = s.get("judge") or {}, (s.get("judge") or {}).get("mascot") or {}
    poster = j.get("poster") or {}
    v = text_verdicts(s["run"]["repo"], s.get("ocr") or {}, j)
    hand = REVIEWS.get(s["run"]["repo"], {})
    fmt = shape(run)
    return {"repo": s["run"]["repo"], "status": s["run"]["status"], "minutes": round(s["run"]["seconds"] / 60, 1),
            "format_ok": sum(f["ok"] for f in fmt.values()), "poster_size": (fmt.get("poster") or {}).get("size"),
            "files": sum(s["files"].values()), "calls": s["images"]["calls"], "cost": s["images"]["cost"],
            "poster_lines": v["poster"], "bag": v["bag"],
            "same_character": m.get("same_character"), "poses": sum(bool(p) for p in m.get("poses") or []),
            "hat_scarf": m.get("hat_and_scarf_all"), "mascot_text": hand.get("mascot_text", m.get("has_text")),
            "poster_other_text": poster.get("other_text"), "poster_looks": poster.get("looks"), "mascot_looks": m.get("looks")}


def text_cell(lines: list[str] | None) -> str:
    if lines is None:
        return "-"
    ok, rv = lines.count("ok"), lines.count("review")
    return f"{ok} {rv}?" if rv else str(ok)


def table(rows: list[dict]) -> None:
    flag = lambda v: "-" if v is None else ("y" if v else "n")   # noqa: E731
    bag = {"ok": "y", "wrong": "n", "review": "?", None: "-"}
    print(f"{'repo':44} {'status':7} {'min':>5} {'f':>2} {'fmt':>3} {'poster':>9} {'calls':>5} {'$':>6}  text bag oth  same poses hat txt")
    for r in rows:
        print(f"{r['repo'][:44]:44} {r['status'][:7]:7} {r['minutes']:>5} {r['files']:>2} {r['format_ok']:>3} {r['poster_size'] or '-':>9} "
              f"{r['calls']:>5} {r['cost']:>6.3f}  {text_cell(r['poster_lines']):>4} {bag[r['bag']]:>3} {flag(r['poster_other_text']):>3}  "
              f"{str(r['same_character'] or '-'):>4} {r['poses']:>5} {flag(r['hat_scarf']):>3} {flag(r['mascot_text']):>3}")


def main() -> None:
    runs = sorted((p for p in OUT.iterdir() if (p / "score.json").exists()), key=lambda p: (p.name != "control", p.name))
    rows = [row(p) for p in runs]
    if "--json" in sys.argv:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    elif "--review" in sys.argv:
        for r in rows:
            todo = [LINES[i] for i, v in enumerate(r["poster_lines"] or []) if v == "review"] + (["bag"] if r["bag"] == "review" else [])
            if todo:
                print(r["repo"], todo)
    else:
        table(rows)


if __name__ == "__main__":
    main()
