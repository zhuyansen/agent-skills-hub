"""Summary table of the humanizer runs: results.json (for the anti-slop page) and RESULTS.md.

  python ops/slop-runs/table_slop.py

One row per candidate. Rewriters: per file the deepest layer changed, how human the
judge found it (1-5), facts kept, AI tells and em-dashes left, and how many of
StoryScope's AI-leaning structure features the rewrite removed. Detectors: how many
flags their reports raised, and how many of those are about structure.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
LAYERS = ["none", "surface", "phrasing", "structure"]
# AI-leaning when true (StoryScope); body_emotion only counts for fiction.
AI_FEATURES = ["stated_theme", "tidy_ending", "vague_references", "body_emotion", "no_reader_address", "single_track"]
NOT_RUN = {
    "iniwap/AIWriteX": ("not a fit", "A desktop app that writes new articles from trending topics and posts them to WeChat; it cannot rewrite a given file."),
    "alexgreensh/attention-span": ("not a fit", "Changes how Claude writes its own replies; its skills start only when a person types the command."),
    "lynote-ai/humanize-text": ("not run", "Needs a Niutrans translation key besides an LLM key, and always outputs English."),
}


def removed(judge: dict) -> int:
    """AI-leaning structure features present in the original and gone in the rewrite."""
    o, r = judge.get("original") or {}, judge.get("rewrite") or {}
    return sum(1 for k in AI_FEATURES if o.get(k) is True and r.get(k) is False)


def file_row(name: str, v: dict) -> dict:
    j = v["judge"]
    return {"file": name, "layer": j.get("layer"), "reads_human": j.get("reads_human"), "meaning_kept": j.get("meaning_kept"),
            "facts": v.get("facts"), "tells": f"{v['before']['tells']}→{v['after']['tells']}",
            "em_dashes": f"{v['before']['em_dashes']}→{v['after']['em_dashes']}", "structure_removed": removed(j),
            "evidence": j.get("evidence")}


def row(c: dict) -> dict:
    run = OUT / c["repo"].replace("/", "__")
    base = {"repo": c["repo"], "kind": c["kind"], "stars": c["stars"], "grade": c.get("grade")}
    if c["repo"] in NOT_RUN:
        status, reason = NOT_RUN[c["repo"]]
        return {**base, "ran": False, "status": status, "reason": reason}
    if not (run / "score.json").exists():
        return {**base, "ran": False, "status": "not run", "reason": "no score"}
    s = json.loads((run / "score.json").read_text())
    files = [file_row(n, v) for n, v in s["files"].items()]
    reports = [{"file": n, **{k: r.get(k) for k in ("flags", "surface", "phrasing", "structure", "score", "structure_examples")}}
               for n, r in s["reports"].items()]
    if not files and not reports:
        return {**base, "ran": False, "status": "not run", "reason": "delivered nothing"}
    return {**base, "ran": True, "minutes": round(s["run"]["seconds"] / 60, 1), "files": files, "reports": reports,
            "deepest": max((f["layer"] for f in files), key=lambda l: LAYERS.index(l) if l in LAYERS else -1, default=None),
            "reads_human": round(sum(f["reads_human"] or 0 for f in files) / len(files), 1) if files else None,
            "structure_removed": sum(f["structure_removed"] for f in files),
            "commit": (run / "commit.txt").read_text().strip()[:12] if (run / "commit.txt").exists() else None}


def markdown(rows: list[dict]) -> str:
    out = ["## Rewriters", "", "| Skill | ★ | Kind | Files | Deepest layer | Human (1-5) | Structure features removed | Facts | Tells | Em-dashes | Min |",
           "|---|---:|---|---|---|---:|---:|---|---|---|---:|"]
    for r in sorted((r for r in rows if r["ran"] and r["files"]), key=lambda r: (-(r["reads_human"] or 0), -r["stars"])):
        fs = r["files"]
        cell = lambda k: " ".join(str(f[k]) for f in fs if f[k] is not None) or "-"   # noqa: E731
        out.append(f"| {r['repo']} | {r['stars']} | {r['kind']} | {' '.join(f['file'].split('.')[0] for f in fs)} | {r['deepest']} | "
                   f"{r['reads_human']} | {r['structure_removed']} | {cell('facts')} | {cell('tells')} | {cell('em_dashes')} | {r['minutes']} |")
    out += ["", "## Detectors", "", "| Skill | ★ | Files | Flags | Surface / Phrasing / Structure |", "|---|---:|---|---:|---|"]
    for r in (r for r in rows if r["ran"] and r["reports"]):
        rep = r["reports"]
        out.append(f"| {r['repo']} | {r['stars']} | {len(rep)} | {sum(x['flags'] or 0 for x in rep)} | "
                   f"{sum(x['surface'] or 0 for x in rep)} / {sum(x['phrasing'] or 0 for x in rep)} / {sum(x['structure'] or 0 for x in rep)} |")
    out += ["", "## Not run", ""] + [f"- {r['repo']} ({r['status']}): {r['reason']}" for r in rows if not r["ran"]]
    return "\n".join(out) + "\n"


def main() -> None:
    rows = [row(c) for c in json.loads((HERE / "candidates.json").read_text())]
    (HERE / "results.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    (HERE / "RESULTS.md").write_text(markdown(rows))
    ran = [r for r in rows if r["ran"]]
    print(f"{len(rows)} candidates, {len(ran)} ran, {sum(1 for r in ran if r['deepest'] == 'structure')} reached structure")


if __name__ == "__main__":
    main()
