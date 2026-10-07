"""Evidence pages for the anti-slop page: the original and each skill's rewrite side by side.

  python ops/slop-runs/evidence.py

Writes frontend/public/best-runs/slop/<owner__repo>.html (noindex) for every run that
delivered something, and frontend/scripts/scenario-runs.json's "anti-slop" entry from
results.json. A page shows, per input file, the original and the rewrite, the judge's
verdict (layer reached, how human it reads, which AI-leaning structure features are left)
and, for detectors, the report the skill wrote.
"""
import html
import json
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
OUT, INPUT = HERE / "out", HERE / "in" / "input"
PUBLIC = ROOT / "frontend" / "public" / "best-runs" / "slop"
RUNS_JSON = ROOT / "frontend" / "scripts" / "scenario-runs.json"
DATE = "2026-10-07"
REPO_URL = "https://github.com/zhuyansen/agent-skills-hub/blob/main/ops/slop-runs/"
FEATURES = {"stated_theme": "States its lesson", "tidy_ending": "Tidy ending", "vague_references": "Vague references",
            "body_emotion": "Emotion through the body", "no_reader_address": "Never addresses the reader",
            "single_track": "One single track"}
TITLES = {"post_en.md": "English post", "post_zh.md": "Chinese post", "story_en.md": "English short story"}
# Readings our checks cannot make on their own, written after reading the output.
NOTES = {
    "DadaNanjesha/AI-Text-Humanizer-App": ("Prepends stock transitions (\"Nonetheless, Every morning…\"): reads more like AI, not less",
                                           "在句首硬加连接词（\"Nonetheless, Every morning…\"）：越改越像 AI"),
    "Nanako0129/sepia": ("Restructured the Chinese post into a numbered list with a firmer summary: more AI-like structure, not less",
                         "把中文文章改成编号清单、总结更重：结构反而更像 AI"),
    "Raymondhou0917/speak-human-tw": ("Rewrites into Traditional Chinese (Taiwan usage)", "改写成繁体中文（台湾用语）"),
}
REASON_ZH = {
    "iniwap/AIWriteX": "桌面应用，从热点生成新文章发公众号，不能改写给定的文件。",
    "alexgreensh/attention-span": "改的是 Claude 自己的回话方式，而且只能由人手动敲命令启动。",
    "lynote-ai/humanize-text": "除 LLM key 外还要 Niutrans 翻译 key，且只输出英文。",
}
STYLE = """:root{--bg:#fff;--fg:#1f2328;--mute:#59636e;--line:#d0d7de;--card:#f6f8fa;--ok:#1a7f37;--bad:#cf222e}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--mute:#9198a1;--line:#30363d;--card:#161b22;--ok:#3fb950;--bad:#f85149}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,'PingFang SC',sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 48px}a{color:#0969da}
h1{font-size:22px;margin:0 0 4px}h2{font-size:18px;margin:32px 0 8px}.mute{color:var(--mute);font-size:13px}
.verdict{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:8px 0 12px;font-size:14px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media (max-width:760px){.cols{grid-template-columns:1fr}}
.col h3{font-size:13px;margin:0 0 6px;color:var(--mute);text-transform:uppercase;letter-spacing:.04em}
pre{white-space:pre-wrap;word-wrap:break-word;margin:0;padding:12px;border:1px solid var(--line);border-radius:8px;
background:var(--card);font:14px/1.6 -apple-system,'PingFang SC',sans-serif;max-height:640px;overflow:auto}
.tag{display:inline-block;font-size:12px;border:1px solid var(--line);border-radius:999px;padding:0 8px;margin:2px 4px 2px 0}
.left{border-color:var(--bad);color:var(--bad)}.gone{border-color:var(--ok);color:var(--ok);text-decoration:line-through}"""


def esc(s) -> str:
    return html.escape(str(s))


def features_html(judge: dict) -> str:
    o, r = judge.get("original") or {}, judge.get("rewrite") or {}
    tags = []
    for k, label in FEATURES.items():
        if o.get(k) is True and r.get(k) is False:
            tags.append(f'<span class="tag gone">{esc(label)}</span>')
        elif r.get(k) is True:
            tags.append(f'<span class="tag left">{esc(label)}</span>')
    return "".join(tags) or '<span class="mute">none</span>'


def rewrite_section(name: str, v: dict, rewrite: str) -> str:
    j = v["judge"]
    facts = f" · facts kept {v['facts']}" if v.get("facts") else ""
    return f"""<h2>{esc(TITLES.get(name, name))}</h2>
<div class="verdict"><b>Layer reached:</b> {esc(j.get('layer'))} · <b>Reads human:</b> {esc(j.get('reads_human'))}/5 · <b>Meaning kept:</b> {esc(j.get('meaning_kept'))}{facts}
 · AI tells {v['before']['tells']}→{v['after']['tells']} · em-dashes {v['before']['em_dashes']}→{v['after']['em_dashes']}<br>
<b>AI-leaning structure</b> (red: still there, struck: removed): {features_html(j)}<br>
<span class="mute">Judge: {esc(j.get('evidence'))}</span></div>
<div class="cols"><div class="col"><h3>Original</h3><pre>{esc((INPUT / name).read_text())}</pre></div>
<div class="col"><h3>Rewrite</h3><pre>{esc(rewrite)}</pre></div></div>"""


def report_section(name: str, r: dict, text: str) -> str:
    return f"""<h2>Report on the {esc(TITLES.get(name, name)).lower()}</h2>
<div class="verdict"><b>Flags:</b> {esc(r.get('flags'))} · surface {esc(r.get('surface'))} · phrasing {esc(r.get('phrasing'))} · structure {esc(r.get('structure'))}</div>
<pre>{esc(text)}</pre>"""


def page(row: dict, score: dict, run: Path) -> str:
    deliver = run / "deliverables"
    parts = [rewrite_section(n, v, (deliver / n).read_text()) for n, v in score["files"].items()]
    parts += [report_section(n, r, (deliver / f"{n}.report.md").read_text()) for n, r in score["reports"].items()]
    note = NOTES.get(row["repo"])
    note_html = f'<p class="verdict">{esc(note[0])}</p>' if note else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>{esc(row['repo'])}: humanizer test</title><style>{STYLE}</style></head><body><main>
<p class="mute"><a href="/best/anti-slop/">← Humanizer &amp; anti-slop skills</a></p>
<h1>{esc(row['repo'])}: test run, {DATE}</h1>
<p class="mute">Claude Code (Claude Opus 5.5) used this skill on three texts written by gpt-6-astra, asked to make them read as
human-written and keep every fact. Judge: gpt-6-astra, comparing original and rewrite on StoryScope's structure features
(<a href="https://arxiv.org/abs/2604.03136">COLM 2026</a>). Repo commit {esc(row.get('commit') or '')}.
<a href="{REPO_URL}RESULTS.md">All results</a> · <a href="{REPO_URL}in/prompt.txt">Prompt</a></p>
{note_html}{''.join(parts)}</main></body></html>"""


def card(row: dict) -> dict:
    if not row["ran"]:
        return {"ran": False, "stars": row["stars"], "reason": row["reason"], "reason_zh": REASON_ZH.get(row["repo"], row["reason"])}
    files = row["files"]
    out = {"ran": True, "stars": row["stars"], "minutes": row["minutes"], "sheet": row["repo"].replace("/", "__") + ".html"}
    if files:
        facts = [f["facts"] for f in files if f["facts"]]
        out.update(reads_human=row["reads_human"], deepest=row["deepest"], structure_removed=row["structure_removed"],
                   facts_kept=all(a == b for a, b in (x.split("/") for x in facts)))
    if row["reports"]:
        out["flags"] = {k: sum(r[k] or 0 for r in row["reports"]) for k in ("flags", "surface", "phrasing", "structure")}
    note = NOTES.get(row["repo"])
    if note:
        out.update(note=note[0], note_zh=note[1])
    return out


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    rows = json.loads((HERE / "results.json").read_text())
    for row in rows:
        if row["ran"]:
            run = OUT / row["repo"].replace("/", "__")
            (PUBLIC / (row["repo"].replace("/", "__") + ".html")).write_text(page(row, json.loads((run / "score.json").read_text()), run))
    runs = json.loads(RUNS_JSON.read_text())
    runs["anti-slop"] = {"type": "slop", "date": DATE, "agent": "Claude Code (Claude Opus 5.5)", "judge": "gpt-6-astra",
                         "brief": REPO_URL + "in/prompt.txt", "results": REPO_URL + "RESULTS.md", "dir": "/best-runs/slop/",
                         "runs": {r["repo"]: card(r) for r in rows}}
    RUNS_JSON.write_text(json.dumps(runs, indent=1, ensure_ascii=False) + "\n")
    print(f"{sum(r['ran'] for r in rows)} evidence pages in {PUBLIC.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
