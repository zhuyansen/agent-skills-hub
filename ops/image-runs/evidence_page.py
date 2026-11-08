"""The image test on the page: the counts, the "image-generation" entry of scenario-runs.json, the page's
picks and two FAQ answers in scenario-keywords.json, the model line-up, and RESULTS.md."""
import json
from pathlib import Path

import evidence_media as media
from evidence_copy import DATE, DEST, GROUP, MODEL_NOTES, PICK_LINES, URL
from runs_common import KEYWORDS_JSON

TITLE_YEAR = "2026"
NONE_KINDS = ("own_account", "not_from_scratch", "needs_a_person", "timeout_nothing")


def counts(rows: list, control: dict, not_run: dict) -> dict:
    six = [r for r in rows if r["group"] in ("clean", "broke")]
    by = lambda g: sum(r["group"] == g for r in rows)  # noqa: E731
    kinds = {k: sum(e["kind"] == k for e in not_run.values()) for k in NONE_KINDS}
    return {"tried": len(rows) + len(not_run), "six": len(six), "clean": by("clean"), "broke": by("broke"), "partial": by("partial"),
            "none": len(not_run), "format": sum(r["format_ok"] < 6 for r in six), "mascot_text": sum(bool(r["mascot_text"]) for r in six),
            "own": sum(r["own"] for r in six), "kinds": kinds, "picks": len(PICK_LINES),
            "control_minutes": control["minutes"], "control_cost": control["cost"]}


def intro(c: dict) -> list:
    return [f"On 7 and 8 November 2026 we had {c['tried']} image generation skills make the same six pictures in a throwaway sandbox, driven by Claude Code (Claude Opus 5.5): a 3:4 poster for a made-up bakery with six exact lines of English and Chinese text, a square photo of a kraft-paper bag printed with the shop's name, and four square pictures of one mascot in four poses. Every image call went to the newest model of the family the skill asked for (GPT Image 2.6, Nano Banana 2.1 or FLUX 3) through one provider, so the skills compare on their prompts and workflow, not on the model they default to. Claude Code with no skill made the set too. The text was read by OCR, and by hand where OCR stumbled; the formats were measured; a vision model judged whether the four mascots are one character; the look was judged by eye. Each skill ran once, with 20 minutes.",
            f"2026 年 11 月 7 日到 8 日，我们让 {c['tried']} 个生图 skill 在用完即删的沙箱里由 Claude Code（Claude Opus 5.5）调用，画同一组六张图：给一家虚构面包店做一张 3:4 海报，上面六行中英文要一字不差；一张方形的牛皮纸袋商品图，袋上印店名；同一个吉祥物的四张方图，四个动作。所有出图都换成 skill 所选模型家族里最新的那个（GPT Image 2.6、Nano Banana 2.1 或 FLUX 3），走同一个接口，所以比的是 skill 的提示词和流程，而不是它默认用哪个模型。不装 skill 的 Claude Code 也画了一组。文字用 OCR 逐字读，OCR 读不准的人工核对；尺寸实测；四张吉祥物是不是同一个角色由视觉模型判断；画风靠肉眼判断。每个 skill 跑一次，限时 20 分钟。"]


def finding(c: dict) -> list:
    k = c["kinds"]
    return [f"On the newest models the text is not where skills differ. Claude Code with no skill wrote all six lines and the bag's name correctly, in {c['control_minutes']} minutes for ${c['control_cost']:.2f} of image calls. {c['clean']} skills did as well and none did better. {c['broke']} more made all six pictures but broke a rule, most often the format ({c['format']} drew the poster square, landscape or 2:3, or the square pictures some other shape) or text on the mascots ({c['mascot_text']}). {c['none']} made no picture: {k['own_account']} work only with their own service or account, {k['not_from_scratch']} do another job, {k['needs_a_person']} wait for a person and {k['timeout_nothing']} drew nothing in 20 minutes. By eye, {c['six'] - c['own']} of the {c['six']} complete sets look close to the no-skill set and {c['own']} have a look of their own.",
            f"在最新模型上，skill 之间的差别不在文字。不装 skill 的 Claude Code 六行字和纸袋上的店名全写对了，用了 {c['control_minutes']} 分钟、出图 ${c['control_cost']:.2f}。{c['clean']} 个 skill 做得一样好，没有一个更好。另有 {c['broke']} 个六张都交了但违反了要求，最多的是尺寸（{c['format']} 个把海报画成方的、横的或 2:3，或者该是方图的画成了别的比例）和吉祥物图上加字（{c['mascot_text']} 个）。{c['none']} 个一张没出：{k['own_account']} 个只能接自家的服务或账号，{k['not_from_scratch']} 个是做别的事的，{k['needs_a_person']} 个要等人先操作，{k['timeout_nothing']} 个 20 分钟没画出来。肉眼看，{c['six']} 套完整的图里 {c['six'] - c['own']} 套接近不装 skill 的那套，{c['own']} 套有自己的样子。"]


def answer(c: dict) -> list:
    return [f"We had {c['tried']} image skills make the same six pictures on the newest models. Claude Code with no skill got every line of text right, {c['clean']} skills matched it and none did better, so install one for its look: the {c['picks']} below each have one of their own and still kept every rule of the brief.",
            f"我们让 {c['tried']} 个生图 skill 用最新模型画同一组六张图。不装 skill 的 Claude Code 每行字都写对了，{c['clean']} 个 skill 和它打平，没有一个更好；所以装 skill 是为了画风：下面 {c['picks']} 个各有自己的样子，也做到了测试题的每条要求。"]


def models_block(models_dir: Path) -> dict:
    """The model line-up: one poster per model, the same brief, no skill (models_compare.py)."""
    rows = []
    for r in json.loads((models_dir / "results.json").read_text()):
        e = {"label": r["label"], "lines": r.get("ocr_exact"), "cost": r.get("cost") or None, "seconds": r.get("seconds") or None}
        src = models_dir / r["file"] if r.get("file") else None
        if r["status"] == "completed" and src and src.exists():
            w, h = media.model_images(src, DEST / "models", r["model"])
            e.update(thumb=f"models/{r['model']}-thumb.webp", full=f"models/{r['model']}.webp", w=w, h=h)
        if r["model"] in MODEL_NOTES:
            e["note"] = MODEL_NOTES[r["model"]]
        rows.append(e)
    rows.sort(key=lambda e: (-(e["lines"] if e["lines"] is not None else -1), e["cost"] or 9))
    done = sum(e["lines"] is not None for e in rows)
    return {"title": [f"Which model gets the text right: {done} models, one poster", f"哪个模型能把字写对：{done} 个模型画同一张海报"],
            "note": ["Each model drew the test's poster once, with no skill, through the same provider; the text was read by OCR and checked by hand. One picture each, and a second try can differ: Nano Banana 2.1 misspelt a Chinese line in an earlier try. The skill test on this page sent every image call to GPT Image 2.6, Nano Banana 2.1 or FLUX 3.",
                     "每个模型不装 skill、走同一个接口，把测试题的海报画一次；文字用 OCR 读，再人工核对。每个只画一张，再画一次可能不同：Nano Banana 2.1 在更早的一次试画里写错过一行中文。本页的 skill 实测，所有出图都走 GPT Image 2.6、Nano Banana 2.1 或 FLUX 3。"],
            "columns": [["Model", "模型"], ["Lines right (of 6)", "写对的行（共 6 行）"], ["Per image", "单张价格"], ["Time", "耗时"], ["Poster", "海报"]],
            "rows": rows}


def page_entry(c: dict, control: dict, runs: dict, not_run: dict, models: dict, mosaic: dict) -> dict:
    return {
        "type": "table", "date": DATE, "dir": "/best-runs/image/", "results": URL + "RESULTS.md",
        "title": [f"Image generation skills tested: the same six pictures from {c['tried']} skills", f"实测对比：{c['tried']} 个生图 skill 画同一组六张图"],
        "intro": intro(c), "finding": finding(c), "verdict": {"answer": answer(c), "more": ["See the test →", "看实测 →"]},
        "models": models,
        "compare": [{"src": mosaic["src"], "w": mosaic["w"], "h": mosaic["h"],
                     "en": f"All {mosaic['count']} posters side by side, the one Claude Code made with no skill outlined in red: most are the same warm photo of a loaf.",
                     "zh": f"{mosaic['count']} 张海报放在一起，红框是不装 skill 画的那张：大多数是同一种暖光面包照片。"}],
        "control": {"sheet": "control.html", "label": ["See the six Claude Code made with no skill →", "看不装 skill 画的六张 →"], **control["pics"],
                    "caption": ["For comparison, what Claude Code made with no skill: the poster, a mascot and the bag.", "对照：不装 skill 的 Claude Code 画的海报、吉祥物和纸袋。"]},
        "name_col": ["Skill and what it drew", "Skill 和它画的图"],
        "columns": [["Result", "结果"], ["Text", "文字"], ["Format", "尺寸"], ["Look, by eye", "画风（肉眼判断）"], ["Time", "耗时"], ["Image calls", "出图次数"]],
        "filters": [{"id": "all", "label": ["All", "全部"]}, *({"id": g, "label": GROUP[g][:2]} for g in ("clean", "broke", "partial")),
                    {"id": "own", "label": ["A look of its own", "有自己的样子"]}],
        "see": ["See the six pictures →", "看六张图 →"], "evidence": ["The pictures", "六张图"],
        "line_label": [f"Image test, {DATE}:", f"{DATE} 生图实测："],
        "not_run_label": ["Made no picture", "一张没出"], "not_run_line": ["Tried in our test, no picture.", "实测时没出图。"],
        "runs": {**runs, **not_run}}


def update_keywords(slug: str, c: dict, rows: list) -> None:
    """The page's picks (explainer.top) from the test, and the two FAQ answers it changes."""
    pages = json.loads(KEYWORDS_JSON.read_text())
    p = next(x for x in pages if x["slug"] == slug)
    by = {r["repo"]: r for r in rows}
    vals = lambda r: {"m": r["minutes"], "c": r["calls"], "d": f"{r['cost']:.2f}"}  # noqa: E731
    items = [{"repo": repo, "line": en.format(**vals(by[repo])), "line_zh": zh.format(**vals(by[repo]))} for repo, (en, zh) in PICK_LINES.items()]
    p["explainer"]["top"] = {
        "h2": f"{len(items)} image generation skills with a look of their own (tested {TITLE_YEAR})",
        "h2_zh": f"有自己画风的 {len(items)} 个生图 skill（{TITLE_YEAR} 实测）", "numbered": False, "items": items,
        "note": f"From our {DATE} test of {c['tried']} skills: each of these made all six pictures, wrote every line of text right, kept the formats asked for, added no text and drew one consistent mascot, and its set looks different from what Claude Code made with no skill (top). Not ranked; every result is in the test section below.",
        "note_zh": f"出自 {DATE} 对 {c['tried']} 个 skill 的实测：这几个都交齐六张、每行字都写对、尺寸符合要求、没有多加字、吉祥物前后一致，而且整套图看起来和不装 skill 的（最上面那组）不一样。不分名次；全部结果在下面的实测区。"}
    faq = {f["q"]: f for f in p["extra_faq"]}
    faq["Can Claude generate images?"].update(
        a=f"Claude itself does not output images, but Claude Code can, by calling an image model's API (GPT Image, Nano Banana, FLUX and others) through a skill, an MCP server or directly with your key. In our November 2026 test, Claude Code with no skill and a GPT Image key made a bakery poster with six exact lines of English and Chinese text, a product photo and four matching mascot pictures in {c['control_minutes']} minutes, for ${c['control_cost']:.2f}.",
        aZh=f"Claude 本身不直接输出图片，但 Claude Code 可以调用图像模型的 API（GPT Image、Nano Banana、FLUX 等）出图：通过 skill、MCP 服务，或者直接用你的 key。在我们 2026 年 11 月的实测里，不装 skill 的 Claude Code 只用一把 GPT Image 的 key，{c['control_minutes']} 分钟、花 ${c['control_cost']:.2f}，就画出了一张六行中英文一字不差的面包店海报、一张商品图和四张同一角色的吉祥物图。")
    faq["Where are image generation skills and MCP servers on GitHub?"].update(
        a=f"Everything on this page is in the open-source list zhuyansen/awesome-ai-image-skills on GitHub, grouped by model and use. Our test of {c['tried']} of them, with every picture each one made, is in the test section above; {c['kinds']['own_account']} of those work only with their own service or account, such as Bria, NovelAI, Scenario or Black Forest Labs.",
        aZh=f"本页收录的都在 GitHub 开源合集 zhuyansen/awesome-ai-image-skills 里，按模型和用途分组。我们对其中 {c['tried']} 个的实测，连同每个画出的图，都在上面的实测区；其中 {c['kinds']['own_account']} 个只能接它自家的服务或账号，比如 Bria、NovelAI、Scenario、Black Forest Labs。")
    KEYWORDS_JSON.write_text(json.dumps(pages, indent=1, ensure_ascii=False) + "\n")


def md_row(repo: str, e: dict) -> str:
    cells = " | ".join(cell[0] for cell in e["cells"])
    return f"| [{repo}](https://github.com/{repo}) | {e['stars']:,} | {cells} |"


def results_md(c: dict, runs: dict, not_run: dict, models: dict) -> str:
    out = [f"# Image generation skills: the same six pictures, {c['tried']} skills ({DATE})", "", finding(c)[0], "",
           "Page: https://agentskillshub.top/best/image-generation/ · Brief: [in/brief.md](in/brief.md) · Runs: run_queue.py → ops/ppt-runs/run.py · "
           "Scoring: score_image.py, text_check.py (OCR), text_review.json (by hand) · Tables: summary.py · Page data: evidence.py", "", "## How", "", intro(c)[0], "",
           f"## The model line-up: one poster each, no skill", "", models["note"][0], "", "| Model | Lines right (of 6) | Per image | Time | Note |", "|---|---|---|---|---|"]
    for m in models["rows"]:
        lines = "-" if m["lines"] is None else m["lines"]
        cost = f"${m['cost']:.3f}" if m["cost"] else "-"
        out.append(f"| {m['label']} | {lines} | {cost} | {m['seconds'] or '-'} s | {(m.get('note') or [''])[0]} |")
    out += ["", "## Every skill that made a picture", "", "| Skill | ★ | Result | Text | Format | Look, by eye | Time | Image calls |", "|---|---|---|---|---|---|---|---|"]
    out += [md_row(repo, e) for repo, e in runs.items()]
    out += ["", f"## Made no picture ({len(not_run)})", ""]
    out += [f"- [{repo}](https://github.com/{repo}): {e['reason']}" for repo, e in not_run.items()]
    out += ["", "## Limits", "", "One run per skill, 20 minutes each; a second run would draw different pictures. Every image call was moved to the newest model of its family, so a skill that pins an older model was not tested on it. The look is our judgement by eye. The mascot verdicts are a vision model's, which gave nearly every set 5 of 5 and counted Zzz sleep marks as text on two sets (overridden by hand, see text_review.json). Skills that need their own service, an account, a photo to start from or a person to answer were stopped, not worked around.", ""]
    return "\n".join(out)
