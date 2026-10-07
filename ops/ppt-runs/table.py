"""Summary table of the PPT skill runs: results.json (for the page) and RESULTS.md.

  python ops/ppt-runs/table.py

Facts are recomputed from each run's files (score.facts), so they follow the latest
rules; the judge's answers come from score.json. Runs that could not happen are listed
with the reason the agent gave, in NOT_RUN.
"""
import json
from pathlib import Path

import score

HERE = Path(__file__).parent
OUT = HERE / "out"
# The agent stopped and said why; these are its reasons, condensed.
NOT_RUN = {
    "Binaryify/open-kimi-ppt-skill": "Repository emptied by its author for copyright reasons; only a README is left.",
    "Scott-Du/codex-ppt": "Codex only: needs Codex's built-in image tool.",
    "johnson7788/MultiAgentPPT": "A standalone web app whose agents need their own LLM API key; not a Claude Code skill.",
    "op7418/NanoBanana-PPT-Skills": "Needs a Google Gemini image key; not attempted.",
}


def cost(run: Path) -> float | None:
    log = run / "images.jsonl"
    if not log.exists(): return None
    return round(sum(json.loads(l).get("cost") or 0 for l in log.read_text().splitlines() if l.strip()), 3)


def row(c: dict) -> dict:
    run = OUT / c["repo"].replace("/", "__")
    base = {"repo": c["repo"], "kind": c["kind"], "stars": c["stars"], "grade": c["grade"]}
    if c["repo"] in NOT_RUN or not (run / "run.json").exists():
        return {**base, "ran": False, "reason": NOT_RUN.get(c["repo"], "not run")}
    f = score.facts(run)
    j = (json.loads((run / "score.json").read_text()).get("judge") or {}) if (run / "score.json").exists() else {}
    stats = max((f.get("pptx") or {}).values(), key=lambda v: v.get("text_chars") or 0, default={}) or {}
    return {**base, "ran": True, "minutes": round(f["run"]["seconds"] / 60, 1), "output": f["rendered_from"],
            "editable": f["editability"], "editable_chars": stats.get("text_chars"), "self_check": f["self_check"],
            "tool_used": f["tool_used"], "image_cost": cost(run),
            **{k: (v.get("answer") or v.get("score") or v.get("level")) for k, v in j.items() if isinstance(v, dict)},
            "rework_what": (j.get("rework") or {}).get("what"), "commit": (run / "commit.txt").read_text().strip()[:12]}


def markdown(rows: list[dict]) -> str:
    head = "| Skill | ★ | Route | Output | Editable | Self-check | Story / Layout / Fidelity / Read | Design | Rework | Min |\n|---|---:|---|---|---|---|---|---:|---|---:|"
    lines = [head]
    for r in sorted((r for r in rows if r["ran"]), key=lambda r: (-(r.get("design") or 0), -r["stars"])):
        q = " / ".join(str(r.get(k, "-")) for k in ("story", "layout_system", "fidelity", "readability"))
        lines.append(f"| {r['repo']} | {r['stars']} | {r['kind']} | {r['output']} | {r['editable']} | {'yes' if r['self_check'] else '-'} | {q} | {r.get('design', '-')} | {r.get('rework', '-')} | {r['minutes']} |")
    lines += ["", "Not run:", ""] + [f"- {r['repo']}: {r['reason']}" for r in rows if not r["ran"]]
    return "\n".join(lines) + "\n"


def main() -> None:
    rows = [row(c) for c in json.loads((HERE / "candidates.json").read_text())]
    (HERE / "results.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    (HERE / "RESULTS.md").write_text(markdown(rows))
    ran = [r for r in rows if r["ran"]]
    print(f"{len(rows)} candidates, {len(ran)} ran, {sum(not r['tool_used'] for r in ran)} without using the tool, "
          f"image cost ${sum(r['image_cost'] or 0 for r in ran):.2f}")


if __name__ == "__main__":
    main()
