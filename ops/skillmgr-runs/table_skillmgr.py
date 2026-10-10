"""Summary of the skill-manager runs: results.json and RESULTS.md.

  python ops/skillmgr-runs/table_skillmgr.py

Objective columns come from the measure-<label>.json files the run wrote at each
checkpoint (skills on disk per agent folder, Claude Code's context tokens, CLAUDE.md
size, MCP servers); the risky-skill column comes from the tool output the agent copied
into report.json, kept only if that text appears in the transcript.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
KEEP = {"csv-cleaner", "sql-explainer", "git-commit-message", "pr-description", "readme-polisher"}
RISKY = "pdf-tools-pro"
LIBRARY = {p.parent.name for p in (HERE / "in/input/library").rglob("SKILL.md")}
# What the test could not judge fairly, from reading each run (2026-10-09).
NOTES = {
    "knoxgraeme/skillfish": ("github-only", "Installs only from GitHub (owner/repo); the test skills were local folders, so install, prune and sync were not tested."),
    "shanliuling/skills-link": ("github-only", "Adds skills only from GitHub URLs; the test skills were local folders, so install, prune and sync were not tested."),
    "infragate/capa": ("project-scope", "Installs per project (./.claude/skills), never globally; it installed, pruned and synced the project copy, which the home-folder measurement does not see."),
    "egebese/skill-manager": ("different-job", "Not an installer: a skill that analyses installed skills and lists the ones to disable in CLAUDE.md."),
}


def measures(run: Path) -> dict:
    return {p.stem.removeprefix("measure-"): json.loads(p.read_text()) for p in run.glob("measure-*.json")}


def names(entries) -> set:
    """Skill names as installed: tools prefix them (library__x, local__x) and add manifests."""
    return {e.split("__")[-1] for e in entries if not e.startswith(".")}


def claude_skills(m: dict | None) -> set:
    return names((m or {}).get("skills", {}).get(".claude/skills", []))


def risky_handling(report: dict, transcript: str) -> str:
    s2 = report.get("step2") or {}
    quote = (s2.get("tool_output") or "").strip()
    verified = bool(quote) and quote.splitlines()[0][:60].replace('"', '\\"') in transcript
    if not s2.get("done") and not quote:
        return "not tested"
    for key, label in (("blocked", "blocked"), ("asked_confirmation", "warned, asked to confirm"), ("warned", "warned"),
                       ("listed_scripts", "listed the scripts"), ("showed_source", "showed the source only")):
        if s2.get(key):
            return label + ("" if verified else " (unverified)")
    return "installed without a word" + ("" if verified else " (unverified)")


def row(c: dict) -> dict:
    run = OUT / c["repo"].replace("/", "__")
    base = {**c, "ran": False}
    if not (run / "run.json").exists():
        return {**base, "reason": "not run"}
    m = measures(run)
    rep_path = run / "deliverables" / "report.json"
    report = json.loads(rep_path.read_text()) if rep_path.exists() else {}
    if c["repo"] in NOTES:
        kind, text = NOTES[c["repo"]]
        return {**base, "ran": True, "untested": kind, "reason": text, "report": report,
                "risky": risky_handling(report, (run / "transcript.jsonl").read_text(errors="ignore")) if kind == "project-scope" else "-",
                "minutes": round(json.loads((run / "run.json").read_text())["seconds"] / 60, 1)}
    if not report.get("installed_tool"):
        return {**base, "reason": (report.get("step1") or {}).get("note") or "tool could not be installed or run", "report": report}
    transcript = (run / "transcript.jsonl").read_text(errors="ignore")
    b, i, p, s = (m.get(k) for k in ("baseline", "installed-20", "pruned", "synced"))
    tokens = lambda x: (x or {}).get("context_tokens") or None   # noqa: E731
    left = claude_skills(p)
    # Pruned: the five kept, no other test skill left (a tool's own skill may stay).
    pruned_ok = p is not None and KEEP <= left and not (left & (LIBRARY | {RISKY})) - KEEP
    codex = names((s or {}).get("skills", {}).get(".codex/skills", [])) | names((s or {}).get("skills", {}).get(".agents/skills", []))
    return {**base, "ran": True, "minutes": round(json.loads((run / "run.json").read_text())["seconds"] / 60, 1),
            "installed_20": LIBRARY <= claude_skills(i),
            "risky": risky_handling(report, transcript),
            "risky_installed": RISKY in claude_skills(m.get("risky")),
            "pruned_to_5": pruned_ok,
            "synced_to_codex": (KEEP <= codex) if s else None,
            "tokens_baseline": tokens(b), "tokens_20": tokens(i), "tokens_pruned": tokens(p),
            "extra_tokens_20": (tokens(i) - tokens(b)) if tokens(i) and tokens(b) else None,
            "claude_md_added": max(((x or {}).get("claude_md_bytes") or 0) for x in m.values()) if m else 0,
            "mcp_added": any(((x or {}).get("mcp") or "") not in ("", (b or {}).get("mcp", "")) for x in m.values()),
            "on_demand": report.get("loads_on_demand"), "report": report,
            "commit": (run / "commit.txt").read_text().strip()[:12] if (run / "commit.txt").exists() else None}


def yes(v) -> str:
    return "-" if v is None else ("yes" if v else "no")


def markdown(rows: list[dict]) -> str:
    out = ["| Tool | ★ | Kind | Installed 20 | Risky skill | Pruned to 5 | Synced to Codex | +tokens (20 skills) | CLAUDE.md / MCP touched | Min |",
           "|---|---:|---|---|---|---|---|---:|---|---:|"]
    for r in (r for r in rows if r["ran"] and not r.get("untested")):
        touched = ", ".join(x for x, f in (("CLAUDE.md", r["claude_md_added"]), ("MCP", r["mcp_added"])) if f) or "no"
        out.append(f"| {r['repo']} | {r['stars']} | {r['kind']} | {yes(r['installed_20'])} | {r['risky']} | {yes(r['pruned_to_5'])} | "
                   f"{yes(r['synced_to_codex'])} | {r['extra_tokens_20'] if r['extra_tokens_20'] is not None else '-'} | {touched} | {r['minutes']} |")
    out += ["", "Ran, but this test could not judge them:", ""] + [f"- {r['repo']} ({r['untested']}): {r['reason']}" for r in rows if r.get("untested")]
    out += ["", "Not run or could not run:", ""] + [f"- {r['repo']}: {r['reason']}" for r in rows if not r["ran"]]
    return "\n".join(out) + "\n"


def main() -> None:
    rows = [row(c) for c in json.loads((HERE / "candidates.json").read_text())]
    (HERE / "results.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    (HERE / "RESULTS.md").write_text(markdown(rows))
    print(f"{len(rows)} tools, {sum(r['ran'] for r in rows)} ran")


if __name__ == "__main__":
    main()
