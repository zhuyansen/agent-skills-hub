"""Subtitles for a ranking video, from the captions burned into it.

The video pipeline (~/ship2market/sitedata/viral-clone/<slug>-A3/) writes its
captions with their timings to codevid/timeline.json. YouTube and Google cannot
read burned-in text, so the same lines go up as subtitle files.

  python ops/youtube/captions_to_srt.py cues <timeline.json> <out.json>
      merged cues, to translate: [{"start", "end", "zh"}]; fill in "en"
  python ops/youtube/captions_to_srt.py srt <cues.json> <out-prefix>
      writes <out-prefix>.zh.srt and, where every cue has "en", <out-prefix>.en.srt
"""
import json
import sys
from pathlib import Path

MIN_CUE = 1.2     # seconds: a shorter caption ("第九") is joined to the next
MAX_CHARS = 24    # but not into a line longer than this


def merged(captions: list[dict]) -> list[dict]:
    cues = []
    for c in captions:
        last = cues[-1] if cues else None
        short = last and last["end"] - last["start"] < MIN_CUE
        same = last and last["item"] == c.get("item")   # never join two ranked items
        if short and same and len(last["zh"]) + len(c["text"]) < MAX_CHARS:
            last["zh"] += "，" + c["text"]
            last["end"] = c["until"]
        else:
            cues.append({"start": c["start"], "end": c["until"], "item": c.get("item"), "zh": c["text"]})
    return cues


def stamp(t: float) -> str:
    ms = round(t * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def srt(cues: list[dict], lang: str) -> str:
    blocks = [f"{i}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c[lang]}\n" for i, c in enumerate(cues, 1)]
    return "\n".join(blocks)


def main() -> None:
    step, src, out = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
    if step == "cues":
        captions = json.loads(src.read_text())["captions"]
        Path(out).write_text(json.dumps(merged(captions), ensure_ascii=False, indent=1) + "\n")
        return
    cues = json.loads(src.read_text())
    Path(f"{out}.zh.srt").write_text(srt(cues, "zh"))
    if all(c.get("en") for c in cues):
        Path(f"{out}.en.srt").write_text(srt(cues, "en"))
    print(f"{len(cues)} cues -> {out}.*.srt")


if __name__ == "__main__":
    main()
