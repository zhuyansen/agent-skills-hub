"""Score the humanizer runs by the two-layer method (anti-slop page, StoryScope).

  python ops/slop-runs/score_slop.py [owner/repo ...]   # default: runs without score.json

Per rewritten file (out/<run>/deliverables/<same name as in/input>):
- surface, counted here: English AI vocabulary, Chinese template phrases and em-dashes,
  before and after;
- facts, checked here: the numbers the brief fixed (186,000 / 18.6 万, 11, 8 hours);
- structure and meaning, judged by gpt-6-astra (FlatRouter) on the original and the
  rewrite side by side, using StoryScope's core narrative features;
- layer reached: surface, phrasing or structure.
For a detector, the judge sorts what its report flags into the same three layers.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUT, INPUT = HERE / "out", HERE / "in" / "input"
RETRIES, RETRY_SECONDS = 3, 20
EN_TELLS = ["delve", "tapestry", "testament", "navigate", "landscape", "crucial", "vital", "robust", "seamless",
            "leverage", "foster", "realm", "embark", "beacon", "symphony", "intricate", "pivotal", "ever-evolving",
            "in today's", "it's important to note", "moreover", "furthermore", "ultimately", "not just", "more than just"]
ZH_TELLS = ["值得注意的是", "总而言之", "综上所述", "在当今", "随着", "不仅", "更是", "赋能", "至关重要", "首先", "其次",
            "最后", "让我们", "毋庸置疑", "不可或缺", "深入", "全方位", "一站式", "助力", "打造"]
FACTS = {"en": [r"186,000", r"\b11\b", r"\b8 hours\b|\bevery 8\b|eight hours"], "zh": [r"18\.6\s*[万萬]|186,?000", r"11\s*[类類]|11 ", r"8\s*小[时時]"]}   # Traditional forms too (speak-human-tw)

STRUCTURE = """You compare an original text and a rewrite of it made by an AI "humanizer" tool.
Judge both on the structural features that, per the StoryScope study (COLM 2026), separate AI writing
from human writing regardless of word choice:
- stated_theme: the text spells out its lesson, theme or takeaway instead of leaving it to the reader
- tidy_ending: the ending resolves neatly (acceptance, reconciliation, a closing summary) rather than staying open
- vague_references: gestures at things in general instead of naming specific works, places, people or examples
- body_emotion: (fiction) conveys emotion mainly through bodily sensations and atmosphere
- no_reader_address: never speaks to the reader directly
- single_track: one tidy line of argument or plot, no digressions or loose ends
Return JSON only:
{"original": {"stated_theme": true|false, "tidy_ending": ..., "vague_references": ..., "body_emotion": true|false|null, "no_reader_address": ..., "single_track": ...},
 "rewrite": {same keys},
 "layer": "none|surface|phrasing|structure",   // the deepest layer the rewrite actually changed
 "meaning_kept": "yes|partly|no", "meaning_note": "...",   // facts, names and claims of the original kept?
 "reads_human": 1-5,
 "evidence": "two or three sentences quoting what changed"}"""

DETECTOR = """You read the report an AI-writing detector produced for a text. Sort what it flags into layers:
surface (words, punctuation such as em-dashes, stock phrases), phrasing (clichés, purple prose, hedging,
redundancy, rhythm) and structure (stated morals or takeaways, tidy endings, vague references instead of
named specifics, no reader address, single-track argument). Return JSON only:
{"flags": <int total>, "surface": <int>, "phrasing": <int>, "structure": <int>, "score": "<any overall score it gives, or null>",
 "structure_examples": "quote up to two structural flags, or empty"}"""


def env() -> dict:
    vals = {}
    for line in (Path.home() / ".claude/.env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1); vals[k.strip()] = v.strip().strip('"')
    return vals


def ask(e: dict, system: str, user: str) -> dict:
    body = {"model": e.get("FLATROUTER_MODEL", "gpt-6-astra"), "temperature": 0, "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    req = urllib.request.Request(e["FLATROUTER_BASE_URL"] + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + e["FLATROUTER_API_KEY"], "Content-Type": "application/json"})
    for attempt in range(RETRIES):   # FlatRouter answers an occasional 502; one bad call must not stop the batch
        try:
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=300) as r:
                return json.loads(json.load(r)["choices"][0]["message"]["content"])
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as err:
            if attempt == RETRIES - 1 or (isinstance(err, urllib.error.HTTPError) and err.code < 500):
                raise
            time.sleep(RETRY_SECONDS * (attempt + 1))


def surface(text: str, lang: str) -> dict:
    tells = ZH_TELLS if lang == "zh" else EN_TELLS
    n = sum(len(re.findall(re.escape(w) if lang == "zh" else r"\b" + re.escape(w) + r"\b", text, re.I)) for w in tells)
    return {"tells": n, "em_dashes": text.count("—")}


def facts_kept(text: str, lang: str) -> int:
    return sum(bool(re.search(p, text)) for p in FACTS[lang])


def rewrite_score(e: dict, name: str, original: str, rewrite: str) -> dict:
    lang = "zh" if name.endswith("_zh.md") else "en"
    result = {"before": surface(original, lang), "after": surface(rewrite, lang)}
    if name.startswith("post"):
        result["facts"] = f"{facts_kept(rewrite, lang)}/{facts_kept(original, lang)}"
    result["judge"] = ask(e, STRUCTURE, f"=== ORIGINAL ===\n{original}\n\n=== REWRITE ===\n{rewrite}")
    return result


def score(run: Path, e: dict) -> dict:
    deliver = run / "deliverables"
    out = {"run": json.loads((run / "run.json").read_text()), "files": {}, "reports": {}}
    for src in sorted(INPUT.glob("*.md")):
        rew, rep = deliver / src.name, deliver / f"{src.name}.report.md"
        if rew.exists() and rew.read_text().strip() != src.read_text().strip():
            out["files"][src.name] = rewrite_score(e, src.name, src.read_text(), rew.read_text())
        if rep.exists():
            out["reports"][src.name] = ask(e, DETECTOR, rep.read_text()[:20000])
    (run / "score.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    return out


def main() -> None:
    e = env()
    names = [r.replace("/", "__") for r in sys.argv[1:]]
    runs = [OUT / n for n in names] if names else [p for p in OUT.iterdir() if (p / "run.json").exists() and not (p / "score.json").exists()]
    for run in runs:
        if not (run / "run.json").exists():
            continue
        s = score(run, e)
        layers = {f: v["judge"].get("layer") for f, v in s["files"].items()}
        print(run.name, s["run"]["status"], layers, {f: (r.get("flags"), r.get("structure")) for f, r in s["reports"].items()}, flush=True)


if __name__ == "__main__":
    main()
