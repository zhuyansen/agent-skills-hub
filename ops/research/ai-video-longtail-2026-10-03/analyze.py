"""AI video long-tail keywords, 2026-10-03: rank the DataForSEO suggestions in suggestions.json.gz.

  python analyze.py [toolify snapshot .json.gz]

Long tail = three words or more, 50+ searches a month, keyword difficulty 30 or less.
Each keyword gets a stage from its last 12 months (US, Google Ads volumes):
  new      no volume until the last 6 months, volume now
  rising   last 3 months average 50%+ above the 9 months before
  steady   neither rising nor fading
  fading   last 3 months 30%+ below the 9 months before (hug video: -82% in a year)
Supply: how many toolify tools carry the keyword's distinctive words in their name (from the
radar's toolify snapshot), a rough count of who already built for it. Writes keywords.csv.
"""
from __future__ import annotations

import csv
import gzip
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MIN_WORDS, MIN_VOLUME, MAX_KD = 3, 50, 30
RISE, FADE = 1.5, 0.7
GENERIC = {"ai", "free", "online", "generator", "maker", "app", "best", "video", "videos", "create", "with",
           "the", "a", "to", "for", "of", "and", "no", "sign", "up", "watermark", "tool", "website"}
THEMES = [("模型名", r"seedance|veo|sora|kling|wan |wan$|hailuo|luma|runway|pika|happy ?horse|grok|midjourney|hunyuan|ltx"),
          ("亲密/情感", r"kiss|hug|couple|love|girlfriend|boyfriend|grandma|grandpa|baby|family|old photo|passed away|memorial"),
          ("舞蹈/动作", r"danc|twerk|move|motion|animate|animation"),
          ("换脸/换人", r"face ?swap|deepfake|swap face|replace face|face changer"),
          ("音乐/唱歌", r"music|song|sing|lyric|rap"),
          ("照片开口", r"talking|speak|lip ?sync|avatar"),
          ("图/文转视频", r"image to video|photo to video|picture to video|text to video|pic to video")]


def months(item: dict) -> list[int]:
    """Monthly volumes, oldest first."""
    ms = sorted(item["keyword_info"].get("monthly_searches") or [], key=lambda m: (m["year"], m["month"]))
    return [m["search_volume"] or 0 for m in ms]


def stage(series: list[int]) -> tuple[str, float | None]:
    if len(series) < 6:
        return "unknown", None
    recent, before = series[-3:], series[:-3]
    rb, bb = sum(recent) / 3, sum(before) / max(len(before), 1)
    if sum(series[:-6]) == 0 and rb > 0:
        return "new", None
    ratio = rb / bb if bb else None
    if ratio is None:
        return "new", None
    return ("rising" if ratio >= RISE else "fading" if ratio <= FADE else "steady"), round(ratio, 2)


def theme(kw: str) -> str:
    return next((name for name, pat in THEMES if re.search(pat, kw)), "其他")


def supply(kw: str, slugs: list[set[str]]) -> int | None:
    words = {w for w in kw.split() if w not in GENERIC}
    if not slugs or not words:
        return None
    return sum(1 for s in slugs if words <= s)


def toolify_slugs(path: str | None) -> list[set[str]]:
    if not path or not Path(path).exists():
        return []
    urls = json.loads(gzip.decompress(Path(path).read_bytes()))
    names = {re.sub(r"^.*/tool/", "", u).strip("/").lower() for u in urls if "/tool/" in u}
    return [set(re.split(r"[-_]+", n)) for n in names]   # one entry per tool, not per language


def rows(data: dict, slugs: list[set[str]]) -> list[dict]:
    seen: dict[str, dict] = {}
    for seed, items in data.items():
        for it in items:
            kw = it["keyword"]
            info, props = it["keyword_info"], it.get("keyword_properties") or {}
            if kw in seen:
                seen[kw]["seeds"].append(seed)
                continue
            series = months(it)
            st, ratio = stage(series)
            seen[kw] = {"keyword": kw, "seeds": [seed], "volume": info.get("search_volume") or 0,
                        "kd": props.get("keyword_difficulty"), "cpc": info.get("cpc"),
                        "words": props.get("words_count") or len(kw.split()), "stage": st, "ratio": ratio,
                        "yearly": (info.get("search_volume_trend") or {}).get("yearly"),
                        "intent": (it.get("search_intent_info") or {}).get("main_intent"),
                        "theme": theme(kw), "supply": supply(kw, slugs), "last6": series[-6:]}
    return list(seen.values())


def longtail(r: dict) -> bool:
    return r["words"] >= MIN_WORDS and r["volume"] >= MIN_VOLUME and r["kd"] is not None and r["kd"] <= MAX_KD


def main() -> int:
    data = json.loads(gzip.decompress((HERE / "suggestions.json.gz").read_bytes()))
    all_rows = rows(data, toolify_slugs(sys.argv[1] if len(sys.argv) > 1 else None))
    picked = sorted((r for r in all_rows if longtail(r)), key=lambda r: (-r["volume"]))
    with open(HERE / "keywords.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["keyword", "theme", "stage", "ratio", "yearly", "volume", "kd", "cpc",
                                          "intent", "supply", "last6", "seeds", "words"])
        w.writeheader()
        for r in picked:
            w.writerow({**r, "seeds": "|".join(r["seeds"]), "last6": " ".join(map(str, r["last6"]))})
    print(f"{len(all_rows)} unique keywords, {len(picked)} long tail")
    for st in ("new", "rising", "steady", "fading"):
        group = [r for r in picked if r["stage"] == st]
        print(f"\n== {st}: {len(group)}")
        for r in group[:25]:
            print(f"  {r['keyword'][:48]:48} {r['theme']:8} vol {r['volume']:>6} kd {r['kd']:>3} "
                  f"×{r['ratio'] or '-':<5} y{r['yearly']}% supply {r['supply']} {r['last6']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
