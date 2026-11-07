"""The anti-slop page shows what each tool did to the same passage, not only its score
(owner, 2026-11-07: the rewrites were only on separate before/after pages).

  python ops/slop-runs/passages.py      # -> frontend/scripts/scenario-passages.json

Three passages carry the tells the 10-07 test was about: the English post's last paragraph (a
"not X, it is Y" turn and a stated lesson), the Chinese post's last paragraph (不是……而是……
and a tidy moral), and the story's last two lines (a tidy ending). For every tool that rewrote
the file, the paragraph(s) of its rewrite closest to the passage are lined up with it and the
changes marked: [["=", text], ["-", removed], ["+", added], ...]. A rewrite whose end no longer
matches the passage (it was cut or merged) is listed as such rather than given another paragraph.
"""
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

try:   # Traditional Chinese rewrites (speak-human-tw) are lined up in Simplified, shown as written
    import opencc
    try:
        _T2S = opencc.OpenCC("t2s")
    except Exception:  # noqa: BLE001 (the official build wants the config file name)
        _T2S = opencc.OpenCC("t2s.json")
except ImportError:
    _T2S = None

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RUNS = json.loads((ROOT / "frontend/scripts/scenario-runs.json").read_text())["anti-slop"]["runs"]
OUT = ROOT / "frontend/scripts/scenario-passages.json"
MATCH_MIN = 0.4    # below this the end of the rewrite is not a rewrite of the passage: cut or merged
PASSAGES = [
    {"id": "post-en", "file": "post_en.md", "starts": "The goal is not to block experimentation.", "paras": 1,
     "label": ["English post, last paragraph", "英文帖最后一段"],
     "note": ["A \"not X, it is Y\" turn and a stated lesson.", "「不是 X，而是 Y」的句式，加一句讲明的道理。"]},
    {"id": "post-zh", "file": "post_zh.md", "starts": "真正成熟的 Agent 治理", "paras": 1,
     "label": ["Chinese post, last paragraph", "中文帖最后一段"],
     "note": ["「不是……而是……」 and a tidy moral.", "「不是……而是……」，加一句整齐的总结。"]},
    {"id": "story", "file": "story_en.md", "starts": "But whenever storms gathered", "paras": 2,
     "label": ["Story, last two lines", "故事最后两句"],
     "note": ["A tidy ending that spells out the feeling.", "把情绪说满的整齐结尾。"]},
]


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip() and not p.lstrip().startswith("#")]


def passage_of(text: str, starts: str, n: int) -> str:
    paras = paragraphs(text)
    i = next(i for i, p in enumerate(paras) if p.startswith(starts))
    return "\n\n".join(paras[i:i + n])


def tokens(text: str) -> list[str]:
    """Words, spaces and single characters: CJK text diffs by character, Latin by word."""
    return re.findall(r"[A-Za-z0-9’'£.-]+|\s+|.", text)


def simplified(text: str) -> str:
    return _T2S.convert(text) if _T2S else text


def sentences(text: str) -> list[str]:
    body = re.sub(r"^#+\s*", "", text, flags=re.M)   # a run-together text starts with its heading
    return [s.strip() for s in re.split(r"(?<=[.!?。！？”])\s+|(?<=[。！？])", body) if s.strip()]


def best_window(original: str, windows: list[str]) -> tuple[str, float]:
    scored = [(SequenceMatcher(None, tokens(original), tokens(simplified(w)), autojunk=False).ratio(), w) for w in windows]
    ratio, best = max(scored) if scored else (0.0, "")
    return best, ratio


def closest(original: str, rewrite: str, n: int) -> tuple[str, float, bool]:
    """The rewrite's matching window of n paragraphs, and whether it had to be found by sentence.
    All three passages end their text, so only windows at the end count: a close paragraph earlier
    in the rewrite is a different one (humanizer-stack cut the post's last paragraph, and the best
    match anywhere was the second). A rewrite that ran every paragraph into one (StealthHumanizer)
    is searched by its last sentences instead."""
    paras = paragraphs(rewrite)
    starts = range(max(0, len(paras) - n - 1), max(1, len(paras) - n + 1))
    best, ratio = best_window(original, ["\n\n".join(paras[i:i + n]) for i in starts])
    if ratio >= MATCH_MIN or len(paras) > 2:
        return best, ratio, False
    k, sents = len(sentences(original)), sentences(rewrite)
    windows = [" ".join(sents[len(sents) - m:]) for m in (k - 1, k, k + 1) if 0 < m <= len(sents)]
    best, ratio = best_window(original, windows)
    return best, ratio, True


def segments(a: str, b: str) -> list[list[str]]:
    """The changes from a to b, lined up in Simplified Chinese and shown in b's own script."""
    ta, sb = tokens(a), tokens(simplified(b))
    tb = tokens(b) if [len(t) for t in tokens(b)] == [len(t) for t in sb] else sb
    out: list[list[str]] = []
    for op, i1, i2, j1, j2 in SequenceMatcher(None, ta, sb, autojunk=False).get_opcodes():
        parts = [["=", "".join(tb[j1:j2])]] if op == "equal" else []
        if op in ("delete", "replace"):
            parts.append(["-", "".join(ta[i1:i2])])
        if op in ("insert", "replace"):
            parts.append(["+", "".join(tb[j1:j2])])
        for kind, text in parts:
            if out and out[-1][0] == kind:
                out[-1][1] += text
            else:
                out.append([kind, text])
    return out


MERGED = ["Ran the whole text into one paragraph; lined up by sentence.", "把全文并成了一段，按句子对齐。"]


def row(repo: str, run: dict, spec: dict, original: str) -> dict | None:
    path = HERE / "out" / repo.replace("/", "__") / "deliverables" / spec["file"]
    if not run.get("ran") or run.get("reads_human") is None or not path.exists():
        return None
    best, ratio, merged = closest(original, path.read_text(errors="ignore"), spec["paras"])
    base = {"repo": repo, "score": run["reads_human"]}
    if ratio < MATCH_MIN:
        return {**base, "missing": True}
    words = lambda t: re.findall(r"\w+|[^\w\s]", simplified(t))   # noqa: E731
    changed = round(1 - SequenceMatcher(None, words(original), words(best), autojunk=False).ratio(), 2)
    # The run's own note is about the Chinese post (sepia's numbered list, speak-human-tw's Traditional script).
    own = [run["note"], run.get("note_zh", run["note"])] if run.get("note") and spec["file"] == "post_zh.md" else None
    note = MERGED if merged else own
    return {**base, "changed": changed, "segments": segments(original, best), **({"note": note} if note else {})}


def main() -> None:
    out = []
    for spec in PASSAGES:
        original = passage_of((HERE / "in/input" / spec["file"]).read_text(), spec["starts"], spec["paras"])
        rows = [r for repo, run in RUNS.items() if (r := row(repo, run, spec, original))]
        rows.sort(key=lambda r: (-r["score"], r.get("changed", 1)))
        out.append({k: spec[k] for k in ("id", "label", "note")} | {"original": original, "rows": rows})
        same = sum(1 for r in rows if not r.get("missing") and r["changed"] == 0)
        print(f"{spec['id']}: {len(rows)} rewrites, {same} left it unchanged, {sum(1 for r in rows if r.get('missing'))} unmatched")
    OUT.write_text(json.dumps({"anti-slop": out}, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
