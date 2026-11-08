"""Literal check of a picture's text with OCR (bin/ocr, macOS Vision without language correction).

  python3 ops/image-runs/text_check.py <image> [...] [-v]
  swiftc -O ops/image-runs/ocr.swift -o ops/image-runs/bin/ocr      # once: bin/ is not committed

The vision judge reads what it expects: it passed "周云上午" for 周六上午 and "Bristel" for Bristol
(2026-11-07, the model line-up). OCR reads letter by letter, so a line OCR finds is there as written:
OCR does not invent a correct line. It does misread some correct glyphs (晨 as 展, Elm as Eim, a
serif f as t or r, the middle dot as 。), so it is read five times (three languages, then twice at
double size, which fixed both bags it misread on 11-07) and the glyphs it confuses are folded on
both sides before comparing. A line OCR does not find exactly is not yet wrong: line_verdict() sends
a near miss (one or two edits away) or a line the judge passed to a look by hand (text_review.json).
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OCR = HERE / "bin" / "ocr"
LINES = ("Morning Loaf", "Grand opening · Saturday 9 am", "晨光面包 · 周六上午九点开业", "Sourdough £4.50 · Croissant £2.20",
         "12 Elm Street, Bristol", "前一百位顾客送一个可颂")
# Look-alikes OCR swaps in Latin text, folded after lower-casing on both sides (I, l, 1 and | are one glyph).
LATIN_FOLD = str.maketrans({"i": "l", "1": "l", "|": "l", "í": "l", "0": "o"})
DOTS = re.compile(r"[·•・･‧∙⋅◦●。.\-‐–—]")
PASSES = ("zh-Hans,en-US", "en-US", "zh-Hans")   # an English-only pass reads Latin text far better
UPSCALED = ("en-US", "zh-Hans,en-US")            # the same picture at double size
NEAR = 2   # edits: a line this close is either a one-letter mistake or an OCR misread, so it is looked at


def ocr_lines(image: Path, languages: str) -> list[str]:
    out = subprocess.run([str(OCR), str(image), languages], capture_output=True, text=True, timeout=120)
    return [l for l in out.stdout.splitlines() if l.strip()]


def norm(text: str) -> str:
    """Spaces and separator dots dropped; Latin text lower-cased and its look-alikes folded."""
    text = DOTS.sub("", re.sub(r"\s+", "", text)).replace("，", ",").replace("：", ":")
    return "".join(ch.lower().translate(LATIN_FOLD) if ord(ch) < 0x250 else ch for ch in text)


def found(line: str, text: str) -> bool:
    return norm(line) in text


def distance(line: str, text: str) -> int:
    """The fewest edits that turn some stretch of text into line (0: the line is there as written)."""
    prev = [0] * (len(text) + 1)
    for i, a in enumerate(line, 1):
        cur = [i] + [0] * len(text)
        for j, b in enumerate(text, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a != b))
        prev = cur
    return min(prev)


def read_all(image: Path) -> dict[str, list[str]]:
    """Every OCR pass: the picture as it is, then at double size."""
    from PIL import Image   # only needed here; the CLI above works without it
    passes = {lang: ocr_lines(image, lang) for lang in PASSES}
    with tempfile.TemporaryDirectory() as tmp:
        big = Path(tmp) / "x2.png"
        im = Image.open(image).convert("RGB")
        im.resize((im.width * 2, im.height * 2), Image.LANCZOS).save(big)
        passes.update({f"x2:{lang}": ocr_lines(big, lang) for lang in UPSCALED})
    return passes


def check(image: Path, lines: tuple[str, ...] = LINES) -> dict:
    """Per line: found as written in any pass, and how close the nearest reading came."""
    passes = read_all(image)
    texts = [norm("".join(p)) for p in passes.values()]
    dist = [min(distance(norm(l), t) for t in texts) for l in lines]
    hits = [d == 0 for d in dist]
    return {"ocr": passes, "found": hits, "distance": dist, "exact": sum(hits)}


def line_verdict(hit: bool, dist: int, judge_exact: bool | None, hand: bool | None) -> str:
    """"ok", "wrong" or "review". A look by hand decides; OCR finding the line decides; a near miss, or a
    line the judge passed that OCR did not find, waits for a look; the rest is wrong."""
    if hand is not None:
        return "ok" if hand else "wrong"
    if hit:
        return "ok"
    return "review" if dist <= NEAR or judge_exact else "wrong"


if __name__ == "__main__":
    for arg in [a for a in sys.argv[1:] if a != "-v"]:
        r = check(Path(arg))
        print(f"{Path(arg).name}: {r['exact']}/6 {['✓' if h else '✗' for h in r['found']]} distance {r['distance']}")
        if "-v" in sys.argv:
            print("   ", json.dumps(r["ocr"], ensure_ascii=False))
