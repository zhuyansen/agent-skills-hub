"""Editability level of a delivered deck, after SlidesGen-Bench's PEI (Yang et al.,
arXiv 2601.09487): L0 static image, L1 text editable, L2 vector graphics, L3 structural,
L4 parametric (native charts or tables), L5 cinematic (animations or transitions).

  python ops/ppt-runs/pei.py [run_dir ...]     # prints the level of each run's best file

The paper names the levels and says they are found by parsing the file; the rules below
are ours, written to that hierarchy, and a level counts only when the ones below it hold:
- L1: the slides carry editable text (any text frame or table cell with text).
- L2: drawn shapes, not only pictures: on average at least one vector shape per slide
  (autoshape that is not a plain text box, freeform, connector or inline SVG).
- L3: structure a colleague can work with: titles in layout placeholders on at least half
  the slides, or grouped elements.
- L4: at least one native chart or table.
- L5: at least one animation or slide transition.
HTML decks get the same tests on the DOM (text in the page, inline SVG or CSS shapes,
repeated slide sections, <table> or a chart library, CSS animation or transitions).
A PDF, or a deck whose text is all inside pictures, is L0.
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
VECTOR_PER_SLIDE = 1.0
PLACEHOLDER_SHARE = 0.5
CHART_LIBS = re.compile(r"chart\.js|echarts|d3(\.v\d)?\.js|highcharts|apexcharts|plotly|vega", re.I)


def _slides(z: zipfile.ZipFile) -> list[str]:
    names = [n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
    return [z.read(n).decode("utf-8", "ignore") for n in sorted(names, key=lambda n: int(re.findall(r"\d+", n)[-1]))]


def _text_chars(xml: str) -> int:
    return sum(len(t) for t in re.findall(r"<a:t>([^<]*)</a:t>", xml))


def _vectors(xml: str) -> int:
    shapes = re.findall(r"<p:sp>.*?</p:sp>", xml, re.S)
    drawn = [s for s in shapes if 'txBox="1"' not in s and "<p:ph" not in s
             and ("<a:custGeom" in s or re.search(r'<a:prstGeom prst="(?!rect")', s) or "<a:solidFill" in s.split("<p:txBody")[0])]
    return len(drawn) + xml.count("<p:cxnSp") + xml.count("svgBlip")


def pptx_flags(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        slides = _slides(z)
    n = max(len(slides), 1)
    return {"slides": len(slides), "text_chars": sum(_text_chars(s) for s in slides),
            "vectors_per_slide": round(sum(_vectors(s) for s in slides) / n, 1),
            "placeholder_title_share": round(sum(bool(re.search(r'<p:ph[^>]*type="(ctrTitle|title)"', s)) for s in slides) / n, 2),
            "groups": sum(s.count("<p:grpSp>") for s in slides),
            "charts_or_tables": sum(s.count("drawingml/2006/chart") + s.count("<a:tbl>") for s in slides),
            "motion": sum(("<p:transition" in s) + ("<p:timing" in s) for s in slides)}


def html_flags(path: Path) -> dict:
    page = path.read_text(errors="ignore")
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", body)
    # A slide is a <section> or an element whose class list has the word "slide" itself
    # (not slide-number, slide-object-text and the like).
    classed = len(re.findall(r"class=\"(?:[^\"]*\s)?slide(?:\s[^\"]*)?\"", page, re.I))
    sections = classed or len(re.findall(r"<section\b", page, re.I))   # one or the other, not both
    return {"slides": sections, "text_chars": len(" ".join(text.split())),
            "vectors_per_slide": round((page.count("<svg") + len(re.findall(r"border-radius|clip-path|linear-gradient", page))) / max(sections, 1), 1),
            "placeholder_title_share": 1.0 if sections >= 2 else 0.0, "groups": 0,
            "charts_or_tables": page.lower().count("<table") + len(CHART_LIBS.findall(page)) + page.count("<canvas"),
            "motion": len(re.findall(r"@keyframes|transition\s*:|data-transition|animation\s*:", page))}


def level(f: dict) -> int:
    checks = [f["text_chars"] > 0, f["vectors_per_slide"] >= VECTOR_PER_SLIDE,
              f["placeholder_title_share"] >= PLACEHOLDER_SHARE or f["groups"] > 0,
              f["charts_or_tables"] > 0, f["motion"] > 0]
    lv = 0
    for ok in checks:
        if not ok:
            break
        lv += 1
    return lv


def find(run: Path, name: str) -> Path | None:
    hits = [p for p in run.rglob(name) if "input" not in p.parts and ".claude" not in p.parts]
    return min(hits, key=lambda p: len(p.parts)) if hits else None


def run_pei(run: Path) -> dict:
    """The best level among the run's delivered decks (a skill may ship an image deck and an editable one)."""
    render = json.loads((run / "render.json").read_text()) if (run / "render.json").exists() else {}
    files = [*(render.get("pptx") or {})]
    main = render.get("rendered_from") or ""
    if main.endswith(".html"):
        files.append(main.split("/")[-1])
    best = {"level": 0, "file": main.split("/")[-1] or None, "flags": None}
    for name in files:
        path = find(run, name)
        if not path:
            continue
        f = html_flags(path) if name.endswith(".html") else pptx_flags(path)
        lv = level(f)
        if best["flags"] is None or lv > best["level"]:
            best = {"level": lv, "file": name, "flags": f}
    return best


if __name__ == "__main__":
    for d in sys.argv[1:] or sorted(str(p) for p in (Path(__file__).parent / "out").iterdir()):
        r = run_pei(Path(d))
        print(f"L{r['level']}", Path(d).name, r["file"], r["flags"])
