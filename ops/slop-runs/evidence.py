"""Evidence pages for the anti-slop page: the original and each skill's rewrite side by side.

  python ops/slop-runs/evidence.py

Writes frontend/public/best-runs/slop/<owner__repo>.html (noindex) for every run that
delivered something, and frontend/scripts/scenario-runs.json's "anti-slop" entry from
results.json. A page shows, per input file, the original and the rewrite, the judge's
verdict (layer reached, how human it reads, which AI-leaning structure features are left)
and, for detectors, the report the skill wrote.
"""
import html
from collections import Counter
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
    "SummerRiversound/human-readable-reports": ("Turns a post into a report with headings and bullet lists: the English post read better (4 of 5), the Chinese one more like AI (2 of 5), with an added \"three things\" opening and a closing summary",
                                                "把文章改成带小标题和列表的报告：英文稿读着更好（4/5），中文稿更像 AI（2/5），还加了「三件事」开头和「结语」"),
}
REASON_ZH = {
    "iniwap/AIWriteX": "桌面应用，从热点生成新文章发公众号，不能改写给定的文件。",
    "alexgreensh/attention-span": "改的是 Claude 自己的回话方式，而且只能由人手动敲命令启动。",
    "lynote-ai/humanize-text": "除 LLM key 外还要 Niutrans 翻译 key，且只输出英文。",
    "jinhuoooo/dsh-prompt-polish": "是另一个聊天应用（DSH）的插件，现在只压缩提示词、不改写文章；还会用写在代码里的智谱 key 或作者自己的代理发送原文。",
    "IT-Shelter-Labs/Shelter-Humanizer": "只支持俄语：规则全是俄语编辑规范，测试稿是英文和中文。",
}
# The answer the test section opens with: which one, by what you are cleaning up.
VERDICT = {
    "rule": ["Rewriters are ranked by how human the rewrite read to the judge (1-5); detectors by how many structure issues they flag.",
             "排名规则：改写类按改写稿读起来像人写的程度（1–5 分）排；检测类按报出多少结构问题排。"],
    "picks": [
        {"repo": "seyedehsanhadi/sloptrim", "role": ["For English text", "英文文本"],
         "why": ["The best-reading rewrites in the test (4.5 of 5) with every fact kept. Like the rest, it changes wording, not structure.",
                 "实测里读起来最像人写的改写（4.5/5），事实全保留。和其他工具一样，它改的是措辞，不是结构。"]},
        {"repo": "zkrun/academic-humanizer-zh", "role": ["For Chinese text", "中文文本"],
         "why": ["4 of 5 on the Chinese post with every fact kept, the best of the Chinese tools (added on 2026-11-08). op7418/Humanizer-zh, the most used, scored 3 and left the closing \"not X but Y\" (不是……而是……) line as it was.",
                 "中文稿 4/5，事实全保留，中文类里最好（2026-11-08 补测）。用的人最多的 op7418/Humanizer-zh 得 3 分，结尾那句「不是……而是……」原样留着。"]},
        {"repo": "Aboudjem/humanizer-skill", "role": ["To check a text, not rewrite it", "只检查不改写"],
         "why": ["The only detector that flags structure in earnest: 8 of its 38 flags were about stated lessons, tidy endings and the like.",
                 "唯一认真查结构的检测器：报出的 38 处里有 8 处是讲明的道理、整齐的结尾这类结构问题。"]},
    ],
    "avoid_label": ["Skip:", "别用："],
    "avoid": [{"repo": "DadaNanjesha/AI-Text-Humanizer-App", "why": ["it prepends stock transitions and reads more like AI (1 of 5)", "在句首硬加连接词，越改越像 AI（1/5）"]}],
    # "caveat" is written by main() from the runs (CAVEAT), so its counts follow the data.
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
<h1>{esc(row['repo'])}: test run, {row.get('date', DATE)}</h1>
<p class="mute">Claude Code (Claude Opus 5.5) used this skill on three texts written by gpt-6-astra, asked to make them read as
human-written and keep every fact. Judge: gpt-6-astra, comparing original and rewrite on StoryScope's structure features
(<a href="https://arxiv.org/abs/2604.03136">COLM 2026</a>). Repo commit {esc(row.get('commit') or '')}.
<a href="{REPO_URL}RESULTS.md">All results</a> · <a href="{REPO_URL}in/prompt.txt">Prompt</a></p>
{note_html}{''.join(parts)}</main></body></html>"""


LANG_ZH = {"Indonesian": "印尼语", "Korean": "韩语", "French": "法语", "Japanese": "日语", "Turkish": "土耳其语"}


def reason_zh(row: dict) -> str:
    return REASON_ZH.get(row["repo"], row["reason"])


def also(other: list[dict]) -> list[str]:
    """The intro's line on the humanizers for other languages: how many, for which languages, and why not tested."""
    by = Counter(r["lang"] for r in other)
    many = sorted(x for x in by if by[x] > 1)
    one = sorted(x for x in by if by[x] == 1)
    each = (", ".join(one[:-1]) + " and " + one[-1]) if len(one) > 1 else "".join(one)
    en = ", ".join([f"{by[x]} for {x}" for x in many] + ([f"one each for {each}"] if one else []))
    zh = "，".join([f"{LANG_ZH[x]} {by[x]} 个" for x in many] + (["、".join(LANG_ZH[x] for x in one) + "各 1 个"] if one else []))
    return [f"Not tested: {len(other)} humanizers added since for other languages ({en}); the test texts are English and Chinese.",
            f"未测：之后新增的 {len(other)} 个其他语言去 AI 味工具（{zh}）；测试稿是英文和中文。"]


CAVEAT = ("No tool rewrote the structure away: across {rewrites} rewrites the stated lesson survived {theme} of {theme_n} times "
          "and the tidy ending {ending} of {ending_n}. Cut the moral, leave the ending open and name specifics yourself.",
          "没有一个工具改掉结构上的 AI 味：{rewrites} 份改写里，讲明的道理 {theme}/{theme_n} 留着，整齐的结尾 {ending}/{ending_n} 留着。"
          "删道理、留结尾、把泛指换成具体名字，得自己动手。")
# The GitHub list's finding (ops/awesome/list_tested.py reads run["list_finding"]).
LIST_FINDING = ("**What we found:** none rewrote the structure away. Across {rewrites} rewrites the stated lesson survived "
                "{theme}/{theme_n}, the tidy ending {ending}/{ending_n}, the single track {track}/{track_n}; {wording} of {rewriters} "
                "changed wording, not structure. {lost_line}",
                "**发现:** 没有一个把结构上的 AI 味改掉。{rewrites} 份改写里,讲明的道理 {theme}/{theme_n} 留着,整齐的结尾 "
                "{ending}/{ending_n} 留着,单线论证 {track}/{track_n} 没动;{rewriters} 个改写类里 {wording} 个只改了措辞。{lost_line_zh}")
SURVIVAL = {"theme": "stated_theme", "ending": "tidy_ending", "track": "single_track"}


def survival(rows: list[dict]) -> dict:
    """Across every rewrite: how often an AI-leaning structure feature of the original was still there after."""
    out = {"rewrites": 0, **{k: 0 for k in SURVIVAL}, **{f"{k}_n": 0 for k in SURVIVAL}}
    for r in (r for r in rows if r["ran"]):
        for v in json.loads((OUT / r["repo"].replace("/", "__") / "score.json").read_text())["files"].values():
            o, w = (v.get("judge") or v).get("original") or {}, (v.get("judge") or v).get("rewrite") or {}
            out["rewrites"] += bool(o)
            for k, feature in SURVIVAL.items():
                out[f"{k}_n"] += o.get(feature) is True
                out[k] += o.get(feature) is True and w.get(feature) is True
    rewriters = [r for r in rows if r["ran"] and r.get("files")]
    lost = sum(1 for r in rewriters if not all(a == b for a, b in (f["facts"].split("/") for f in r["files"] if f.get("facts"))))
    return {**out, "rewriters": len(rewriters), "wording": sum(1 for r in rewriters if r.get("deepest") != "structure"),
            "lost_line": "No fact was lost." if not lost else f"{lost} lost a fact.",
            "lost_line_zh": "没有一份改丢事实。" if not lost else f"{lost} 个改丢了事实。"}


def dated(row: dict) -> dict:
    """A run after the main test carries its own date (the skill page says when it was tested)."""
    return {"date": row["date"]} if row.get("date") else {}


def card(row: dict) -> dict:
    if not row["ran"]:
        return {"ran": False, "stars": row["stars"], "reason": row["reason"], "reason_zh": reason_zh(row), **dated(row)}
    files = row["files"]
    out = {"ran": True, "stars": row["stars"], "minutes": row["minutes"], "sheet": row["repo"].replace("/", "__") + ".html",
           **dated(row)}
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
    other = [r for r in rows if r.get("lang")]   # humanizers for a language the test texts are not in: named, not counted
    counts = survival(rows)
    runs["anti-slop"] = {"verdict": {**VERDICT, "caveat": [CAVEAT[0].format(**counts), CAVEAT[1].format(**counts)]}, "type": "slop",
                         "list_finding": [LIST_FINDING[0].format(**counts), LIST_FINDING[1].format(**counts)], "date": DATE, "agent": "Claude Code (Claude Opus 5.5)", "judge": "gpt-6-astra",
                         "brief": REPO_URL + "in/prompt.txt", "results": REPO_URL + "RESULTS.md", "dir": "/best-runs/slop/",
                         **({"also": also(other)} if other else {}),
                         "runs": {r["repo"]: card(r) for r in rows if not r.get("lang")}}
    RUNS_JSON.write_text(json.dumps(runs, indent=1, ensure_ascii=False) + "\n")
    print(f"{sum(r['ran'] for r in rows)} evidence pages in {PUBLIC.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
