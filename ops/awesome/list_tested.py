"""The "Tested" section of a GitHub list: the page's end-to-end test results, from the
same data as the page's test-results section (frontend/scripts/scenario-runs.json).
Lists without a test run get nothing."""
from __future__ import annotations

import json
from pathlib import Path

RUNS = Path(__file__).resolve().parents[2] / "frontend/scripts/scenario-runs.json"
ANCHOR = "tested"
REWORK_RANK = {"touch-ups": 0, "one round": 1, "substantial": 2}
WORDS = {
    "en": {"h": "Tested end to end", "evidence": "evidence", "not_run": "Could not run",
           "all": "All results, prompts and scripts", "ppt_cols": "| Skill | ★ | Before handing over | Editability (PEI) | Content rubric | Min | |",
           "slop_cols": "| Skill | ★ | Reads human | Layer reached | AI structure removed | Facts | Detector flags | |",
           "ppt_intro": ("On {date} we ran {n} of these skills and {ran} ran: each built a deck from the same brief in a "
                         "throwaway sandbox, driven by {agent}. Editability is a level after SlidesGen-Bench's PEI "
                         "([arXiv 2601.09487](https://arxiv.org/abs/2601.09487)), parsed from the file; the content rubric is "
                         "yes/no items after PresentBench ([arXiv 2603.07244](https://arxiv.org/abs/2603.07244)), checked by {judge} "
                         "three times and reviewed by hand. Ranked by rework before handing over, then editability, then the rubric."),
           "slop_intro": ("On {date} we ran {n} of these skills and {ran} ran: each rewrote the same three texts (an "
                          "English post, a Chinese post, a short story) in a throwaway sandbox, driven by {agent}, "
                          "judged by {judge} on StoryScope's structure features "
                          "([COLM 2026](https://arxiv.org/abs/2604.03136)). Most human-reading first."),
           "slop_finding": ("**What we found:** none rewrote the structure away. Across 40 rewrites the stated lesson "
                            "survived 26/26, the tidy ending 28/28, the single track 40/40; 19 of 21 changed wording, "
                            "not structure. No fact was lost."),
           "kept": "all kept", "lost": "some lost", "detector": "detector only"},
    "zh": {"h": "端到端实测", "evidence": "证据", "not_run": "未能实测",
           "all": "全部结果、提示词和脚本", "ppt_cols": "| Skill | ★ | 交付前 | 可编辑性(PEI) | 内容检查单 | 分钟 | |",
           "slop_cols": "| Skill | ★ | 像人写 | 改到哪层 | 去掉的 AI 结构 | 事实 | 检测报出 | |",
           "ppt_intro": "{date} 我们实跑了其中 {n} 个,跑成 {ran} 个:每个在用完即删的沙箱里按同一份测试题做 deck,由 {agent} 调用。按 PresentBench 的是/否检查单打分([arXiv 2603.07244](https://arxiv.org/abs/2603.07244),{judge} 核对),可编辑性按 SlidesGen-Bench 的 PEI 分级([arXiv 2601.09487](https://arxiv.org/abs/2601.09487),解析文件得出)。先按交付前返工程度,再按可编辑性,最后按内容检查单排序。",
           "slop_intro": ("{date} 我们实跑了其中 {n} 个,跑成 {ran} 个:每个在用完即删的沙箱里改写同样的三份文本(英文文章、中文文章、"
                          "短篇小说),由 {agent} 调用,{judge} 按 StoryScope 的结构特征评审([COLM 2026](https://arxiv.org/abs/2604.03136))。"
                          "按像人写的程度排序。"),
           "slop_finding": ("**发现:** 没有一个把结构上的 AI 味改掉。40 份改写里,讲明的道理 26/26 留着,整齐的结尾 28/28 留着,"
                            "单线论证 40/40 没动;21 个改写类里 19 个只改了措辞。没有一份改丢事实。"),
           "kept": "全保留", "lost": "有丢失", "detector": "只检测"},
}
PEI = ["L0 nothing editable", "L1 text", "L2 + shapes", "L3 + structure", "L4 + charts/tables", "L5 + animation"]
PEI_ZH = ["L0 不可编辑", "L1 文字可改", "L2 + 矢量图形", "L3 + 结构化", "L4 + 原生图表/表格", "L5 + 动画"]
EDITABLE = {"native": ("Editable PPTX", "原生可编辑 PPTX"), "hybrid": ("Image layers, editable text", "图片底 + 可编辑文字"),
            "image": ("All images", "整页图片"), "browser": ("Editable in browser", "浏览器里可改"), "pdf": ("PDF", "PDF")}
REWORK = {"touch-ups": ("touch-ups", "小修"), "one round": ("one round", "改一轮"), "substantial": ("substantial", "大改")}
LAYER = {"structure": ("structure", "结构"), "phrasing": ("wording", "措辞"), "surface": ("words only", "只换词")}


def run_for(slug: str) -> dict | None:
    return json.loads(RUNS.read_text()).get(slug) if RUNS.exists() else None


def _name(repo: str) -> str:
    return f"[{repo.split('/')[1]}](https://github.com/{repo})"


def _ppt_line(repo: str, r: dict, i: int, link: str) -> str:
    rework = REWORK.get(r.get("rework"), ("-", "-"))[i]
    rubric = f"{round(r['checklist'] * 100)}%" if r.get("checklist") is not None else "-"
    pei = (PEI_ZH if i else PEI)[r["pei"]] if r.get("pei") is not None else EDITABLE.get(r.get("editable"), ("-", "-"))[i]
    return f"| {_name(repo)} | {r.get('stars', 0):,} | {rework} | {pei} | {rubric} | {r['minutes']} | {link} |"


def _slop_line(repo: str, r: dict, i: int, link: str, w: dict) -> str:
    rewrote = r.get("reads_human") is not None
    human = f"{r['reads_human']}/5" if rewrote else "-"
    layer = LAYER.get(r.get("deepest"), ("-", "-"))[i] if rewrote else w["detector"]
    facts = (w["kept"] if r.get("facts_kept") else w["lost"]) if rewrote else "-"
    flags = f"{r['flags']['flags']} ({r['flags']['structure']})" if r.get("flags") else "-"
    return f"| {_name(repo)} | {r.get('stars', 0):,} | {human} | {layer} | {r.get('structure_removed', '-') if rewrote else '-'} | {facts} | {flags} | {link} |"


def _order(run: dict) -> list[tuple[str, dict]]:
    ran = [(k, v) for k, v in run["runs"].items() if v.get("ran")]
    if run.get("type") == "slop":
        return sorted(ran, key=lambda p: (-(p[1].get("reads_human") or -1), -(p[1].get("flags") or {}).get("structure", 0)))
    return sorted(ran, key=lambda p: (bool(p[1].get("note")), REWORK_RANK.get(p[1].get("rework"), 9),
                                      -(p[1].get("pei") if p[1].get("pei") is not None else -1), -(p[1].get("checklist") or -1)))


def section(slug: str, lang: str, site: str, utm: str) -> list[str]:
    """Markdown lines of the list's Tested section; [] when the page has no test run."""
    run = run_for(slug)
    if not run:
        return []
    w, i, slop = WORDS[lang], 0 if lang == "en" else 1, run.get("type") == "slop"
    ran = _order(run)
    intro = w["slop_intro" if slop else "ppt_intro"].format(date=run["date"], n=len(run["runs"]), ran=len(ran),
                                                            agent=run["agent"], judge=run["judge"])
    out = ["", f'<a id="{ANCHOR}"></a>', f"## 🧪 {w['h']}", "", intro, ""]
    if slop:
        out += [w["slop_finding"], ""]
    cols = w["slop_cols" if slop else "ppt_cols"]
    out += [cols, "|" + "|".join("---" for _ in range(cols.count("|") - 1)) + "|"]
    for repo, r in ran:
        link = f"[{w['evidence']}]({site}{run['dir']}{r['sheet']})"
        out.append(_slop_line(repo, r, i, link, w) if slop else _ppt_line(repo, r, i, link))
    missing = [(k, v) for k, v in run["runs"].items() if not v.get("ran")]
    if missing:
        out += ["", f"**{w['not_run']}:** " + "; ".join(
            f"{k.split('/')[1]} ({v.get('reason_zh' if i else 'reason') or v.get('reason')})" for k, v in missing)]
    out += ["", f"[{w['all']}]({run['results']}) · [{site}/best/{slug}/#test-results]({site}/best/{slug}/{utm}#test-results)"]
    return out
