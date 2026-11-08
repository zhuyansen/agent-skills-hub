"""The image test's words: table cells and card phrases (English and Chinese), the evidence page of each
run, the page's scenario-runs.json entry, its picks and two FAQ answers (scenario-keywords.json), and
RESULTS.md. evidence.py does the pictures and the order and calls these."""
import json
from pathlib import Path

import evidence_media as media
from runs_common import KEYWORDS_JSON, PUBLIC, REPO_URL, esc, final_message, key, shell
from summary import REVIEWS
from text_check import LINES

DATE, CONTROL = "2026-11-08", "control"
DEST, URL = PUBLIC / "image", REPO_URL + "image-runs/"
PAGE = ("/best/image-generation/", "Image generation skills")
SLOW_MINUTES = 15
RATIOS = {"1:1": 1, "3:4": 4 / 3, "4:3": 3 / 4, "2:3": 3 / 2, "3:2": 2 / 3, "9:16": 16 / 9, "16:9": 9 / 16, "4:5": 5 / 4, "5:2": 2 / 5}
RATIO_TOLERANCE = 0.03
GROUP = {"clean": ["Followed the brief", "完全照做", "touch-ups"], "broke": ["Broke a rule", "有违规", "substantial"],
         "partial": ["Part of the set", "只交一部分", "substantial"], "special": ["Portrait only", "只画人像", ""]}
LOOK = {"own": ["A look of its own", "有自己的样子", "touch-ups"], "close": ["Close to the no-skill set", "接近不装 skill 的那套", ""]}
NONE_CELL = ["-", "-", ""]
NOTES = {
    "yanliudesign/mono-color-skill": ("Drew 28 times to get its one-colour look, the most of any skill that followed the brief.", "为了单色效果画了 28 次，完全照做的 skill 里最多。"),
    "s1dashu/ip-as-logo-skill": ("Makes the mascot-as-logo only, as its README says: no text on the poster or the bag.", "按 README 说的只做 IP 形象：海报和纸袋上都没写字。"),
    "qhdrl12/mcp-server-gemini-image-generator": ("23 image calls and no text on any picture.", "调用 23 次，所有图上都没写字。"),
    "minilozio/nano-banana-prompting-skill": ("Wrote no text on the poster or the bag.", "海报和纸袋上一个字都没写。"),
    "zhouzhq2021/PaperBanana-AIMSLab": ("48 image calls in 21 minutes, the most here; a 2:3 poster.", "21 分钟调用 48 次，全场最多；海报是 2:3。"),
    "helloianneo/ian-xiaohei-illustrations": ("Draws everything 16:9 in its own style, with its Xiaohei character in place of the bun.", "所有图都是它自己的 16:9 画风，用「小黑」换掉了面包吉祥物。"),
    "helloianneo/ian-xiaohei-scenes": ("Its Xiaohei character in place of the bun, 16:9, and 2 of the 6 lines.", "用「小黑」换掉了面包吉祥物，16:9，海报只写了 2 行。"),
    "chiyolyn/bold-contour-ink-portrait": ("Black ink line art: the red scarf came out black.", "黑色墨线风：红围巾画成了黑色。"),
    "TaiT-tt/tait-crt-interface-skill": ("Frames every picture as a retro computer screen, and printed its own name on the poster.", "每张都做成复古电脑界面，还把自己的名字印在了海报上。"),
    "CaliCastle/skills": ("A chalkboard look; the poster carries the shop name and none of the other five lines.", "黑板风；海报只写了店名，另外五行都没有。"),
    "dacnay816y62-hub/fantasy-qiqiguaiguai-skill": ("Big-type posters; added lines of its own on the poster, the bag and the mascots.", "大字报风；海报、纸袋和吉祥物图上都加了自己写的字。"),
    "JuneYaooo/xhs-writer-skill": ("A social-card layout; left out the price line and the last Chinese line.", "小红书卡片版式；漏了价格那行和最后一行中文。"),
    "moonlin1213/muted-zine-poster-v01": ("A muted zine look on 9:16 pages, with the mascot's name on its pictures.", "低饱和杂志风，9:16 竖版，吉祥物图上写了名字。"),
    "ningzimu/codex-ppt-skill": ("A slide-deck skill: made all six as 16:9 slides, in 20 minutes.", "做幻灯片的 skill：六张都做成 16:9 幻灯片，用了 20 分钟。"),
    "llmsresearch/paperbanana": ("A pipeline for research-paper figures: 1 picture in 20 minutes.", "论文配图流水线：20 分钟只出 1 张。"),
    "mituan-ai/PaperBanana-CN": ("A pipeline for research-paper figures: 3 pictures in 20 minutes.", "论文配图流水线：20 分钟出了 3 张。"),
    "ianlintner/ai-pixel-art-image-generation": ("Despite the name, the same photo and 3D look as Claude Code with no skill; the fastest here at 1.6 minutes.", "名字叫像素画，出来的却和不装 skill 一样是照片和 3D 风；全场最快，1.6 分钟。"),
    "kkoppenhaver/cc-nano-banana": ("17.5 minutes, the slowest of the sets with all six; a square poster.", "17.5 分钟，交齐六张的里面最慢；海报是方的。"),
    "liyue-aigc/female-portrait-director": ("Draws portraits of women only, so it got a portrait brief instead of the bakery set.", "只画女性人像，所以给它的是人像题，不是面包店那组。"),
    "dacnay816y62-hub/photo-revival": ("Built to turn your photos into airy hand-drawn pictures; from the brief alone it drew small subjects in a lot of white space.", "本来是把照片转成留白手绘的；只给需求时，它画出的是大面积留白里的小主体。"),
    "nevertoday/xxd-panel-028": ("Built to turn photos into isometric paper miniatures; from the brief alone it staged the mascot in a tiny bakery stall.", "本来是把照片做成等距纸模型的；只给需求时，它把吉祥物放进了一个迷你面包摊。"),
}
# The picks: a look of their own and every rule of the brief kept. {m}, {c}, {d}: minutes, image calls, dollars.
PICK_LINES = {
    "yanliudesign/mono-color-skill": ("For a one-colour print look. Every picture came out in blue halftone on cream with oversized type, like a risograph poster, and every rule of the brief held. It drew {c} times to get there, the most of any skill that followed the brief ({m} minutes, ${d}).",
                                      "要单色印刷的感觉。每张都是米色底上的蓝色网点和大号字，像孔版印刷海报，测试题的每条要求也都做到了。为此它画了 {c} 次，完全照做的 skill 里最多（{m} 分钟，${d}）。"),
    "tmchow/illo-skill": ("For warm, hand-drawn illustration. It drew the mascot in a cartoon line style and put it on the poster and the bag too, so the six read as one set ({m} minutes, ${d}).",
                          "要温暖的手绘插画。它用卡通线条画吉祥物，还把吉祥物放进了海报和纸袋，六张像一整套（{m} 分钟，${d}）。"),
    "BIAsia/voxel-icon": ("For a voxel (3D pixel-block) look. The loaf, the mascot and even the bag came out as clean voxel art on white, with the text set plainly below ({m} minutes, ${d}).",
                          "要体素（3D 像素块）风格。面包、吉祥物连纸袋都做成了白底体素图，字老老实实排在下面（{m} 分钟，${d}）。"),
    "james20141606/sci-figure-workflow": ("For flat vector graphics. Built for research-paper figures, it drew a sun-and-loaf poster in clean shapes and a line-drawn mascot, closer to an infographic than a photo ({m} minutes, ${d}).",
                                          "要扁平矢量图形。它本来是做论文配图的，画出的是几何形状的太阳和面包海报、线描吉祥物，更像信息图而不是照片（{m} 分钟，${d}）。"),
    "dacnay816y62-hub/regional-culture-poster": ("For posters built on Chinese lettering. It set a giant calligraphic 晨 (morning) behind the loaf; its mascot and bag stay close to the default photo look ({m} minutes, ${d}).",
                                                 "要以中文字为主角的海报。它在面包后面放了一个巨大的书法「晨」字；吉祥物和纸袋仍接近默认的照片风格（{m} 分钟，${d}）。"),
    "nevertoday/xxd-panel-028": ("For little isometric scenes. Built to turn photos into paper miniatures, from the brief alone it stood the mascot in a tiny bakery stall, with props from the same scene on the poster and the bag ({m} minutes, ${d}).",
                                 "要等距视角的小场景。它本来是把照片做成纸模型的，只给需求时，它把吉祥物放进了一个迷你面包摊，海报和纸袋上也摆着同一个场景里的小道具（{m} 分钟，${d}）。"),
    "dacnay816y62-hub/photo-revival": ("For a quiet, minimal look. Built to turn your photos into airy hand-drawn pictures, from the brief alone it drew small subjects in a lot of white space with light type, the opposite of the busy default ({m} minutes, ${d}).",
                                       "要安静、极简的感觉。它本来是把照片转成留白手绘的，只给需求时，画出的是大面积留白里的小主体和细字，和满满当当的默认风格正好相反（{m} 分钟，${d}）。"),
}
MODEL_NOTES = {
    "gpt-image-1": ["The price line and the last Chinese line wrong; the dearest per image here", "价格那行和最后一行中文写错；单张最贵"],
    "gemini-2.5-flash-image-preview": ["Both Chinese lines garbled", "两行中文都写成了乱码"],
    "gemini-3-pro-image-preview": ["Changed the Chinese date and put the last line in English", "改了中文日期，最后一行写成了英文"],
    "flux-2-pro": ["Both Chinese lines wrong (周六 as 周云)", "两行中文写错（周六写成周云）"],
    "mai-image-2.6": ["可颂 as 可谅", "「可颂」写成「可谅」"],
    "z-image-turbo": ["Bristol as Bristel", "Bristol 写成 Bristel"],
    "wan2.7-image-pro": ["All six right, plus a line of its own (Est. 2024)", "六行全对，但多写了一行 Est. 2024"],
    "grok-imagine-image-2.0": ["Only at its own default size", "只能用它自己的默认尺寸"],
    "midjourney": ["Not offered by the provider we used", "我们用的接口没有开放"],
    "imagen-4.0-apimart": ["Failed on the day", "当天调用失败"],
}


def ratio_name(size: str) -> str:
    w, h = (int(x) for x in size.split("x"))
    name = min(RATIOS, key=lambda k: abs(RATIOS[k] - h / w))
    return name if abs(RATIOS[name] - h / w) <= RATIO_TOLERANCE * RATIOS[name] else f"{w}x{h}"


def format_parts(fmt: dict) -> list[tuple]:
    bad = {stem: ratio_name(v["size"]) for stem, v in fmt.items() if not v["ok"]}
    if not bad:
        return []
    if len(bad) == 6 and len(set(bad.values())) == 1:
        r = next(iter(bad.values()))
        return [("format", f"all six {r}", f"六张都是 {r}")]
    parts = [("format", f"poster {bad['poster']}", f"海报 {bad['poster']}")] if "poster" in bad else []
    others = len([s for s in bad if s != "poster"])
    return parts + ([("format", f"{others} not square", f"{others} 张不是方图")] if others else [])


def problems(r: dict) -> list[tuple]:
    """(kind, English, Chinese) for each rule of the brief the set broke; kind is text, format or other."""
    lines, out = r["poster_lines"], []
    if lines is not None and lines.count("ok") < 6:
        out.append(("text", f"{lines.count('ok')} of 6 poster lines right", f"海报 6 行只对 {lines.count('ok')} 行"))
    if r["bag"] not in (None, "ok"):
        out.append(("text", "the shop name on the bag wrong or missing", "纸袋上店名不对或没写"))
    out += format_parts(r["fmt"])
    if r["poster_other_text"]:
        out.append(("other", "extra text on the poster", "海报上多了字"))
    if r["mascot_text"]:
        out.append(("other", "text on the mascot pictures", "吉祥物图上有字"))
    out += mascot_problems(r)
    return out


def mascot_problems(r: dict) -> list[tuple]:
    if r["files"] != 6:
        return []
    out = [("other", f"the mascots less alike (judge {r['same_character']}/5)", f"四张吉祥物不太像同一个（评审 {r['same_character']}/5）")] if (r["same_character"] or 0) < 5 else []
    if r["poses"] < 4:
        out.append(("other", f"{r['poses']} of 4 poses right", f"4 个动作对了 {r['poses']} 个"))
    if r["hat_scarf"] is False:
        out.append(("other", "the hat or scarf missing in some", "有的没戴帽子或围巾"))
    return out


def issues(r: dict, g: str) -> list | None:
    """The rules a set broke that the Text and Format columns do not show, for under the skill's name."""
    other = [p for p in problems(r) if p[0] == "other"] if g == "broke" else []
    if not other:
        return None
    en = "; ".join(p[1] for p in other)
    return [en[0].upper() + en[1:], "；".join(p[2] for p in other)]


def text_cell(r: dict) -> list:
    lines = r["poster_lines"]
    if lines is None:
        return NONE_CELL
    ok, bag = lines.count("ok"), r["bag"] == "ok"
    mark = "✓" if bag else "✗"
    return [f"{ok}/6 · bag {mark}", f"{ok}/6 · 纸袋 {mark}", "touch-ups" if ok == 6 and bag else "substantial"]


def format_cell(r: dict) -> list:
    if not r["fmt"]:
        return NONE_CELL
    parts = format_parts(r["fmt"])
    if not parts:
        return ["As asked", "都对", "touch-ups"]
    en = "; ".join(p[1] for p in parts)
    return [en[0].upper() + en[1:], "；".join(p[2] for p in parts), "substantial"]


def cells(r: dict, g: str, look: str) -> list:
    m = r["minutes"]
    return [GROUP[g], text_cell(r), format_cell(r), LOOK[look] if g in ("clean", "broke") else NONE_CELL,
            [f"{m} min", f"{m} 分钟", "substantial" if m > SLOW_MINUTES else "num"],
            [f"{r['calls']} · ${r['cost']:.2f}", f"{r['calls']} 次 · ${r['cost']:.2f}", "num"]]


def bits(r: dict, g: str, look: str) -> list:
    """The card's "Tested" line."""
    tail = [[f"{r['minutes']} min", f"{r['minutes']} 分钟"], [f"{r['calls']} image calls (${r['cost']:.2f})", f"出图 {r['calls']} 次（${r['cost']:.2f}）"]]
    if g == "special":
        return [["draws portraits of women only; given a portrait brief, it made one", "只画女性人像；给它人像题，交了 1 张"], *tail]
    if g == "partial":
        return [[f"{r['files']} of the 6 pictures in 20 minutes", f"20 分钟只交了 6 张里的 {r['files']} 张"], *tail]
    if g == "clean":
        head = ["followed the brief: all six pictures, all text right, formats as asked", "完全照做：六张都交、字全对、尺寸都对"]
    else:
        ps = problems(r)
        head = ["made all six but broke a rule: " + "; ".join(p[1] for p in ps), "六张都交了但违规：" + "；".join(p[2] for p in ps)]
    return [head, [LOOK[look][0].lower(), LOOK[look][1]], *tail]


# ---- The evidence page of one run ----

EVIDENCE_STYLE = """<style>.pics{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin:8px 0}
.pics figure{margin:0}.pics .big{grid-column:span 2}@media(max-width:520px){.pics .big{grid-column:auto}}
.pics figcaption{font-size:13px;color:var(--mute);margin-top:4px}</style>"""
BRIEF_LINE = ("The same brief for every skill: a 3:4 poster for a made-up bakery with six exact lines of English and Chinese text, "
              "a square photo of a kraft-paper bag printed with the shop's name, and four square pictures of one mascot in four poses. "
              "Claude Code (Claude Opus 5.5) made them with the skill in a throwaway sandbox; every image call went to the newest model "
              "of the family the skill asked for (GPT Image 2.6, Nano Banana 2.1 or FLUX 3).")


def verdict_span(v: str) -> str:
    return '<span class="ok">right</span>' if v == "ok" else '<span class="no">wrong</span>'


def figure(k: str, stem: str, info: dict | None) -> str:
    cap = stem if not info else f"{stem} · {info['size'].replace('x', ' x ')} · {ratio_name(info['size'])} · " + (
        '<span class="ok">as asked</span>' if info["ok"] else f'<span class="no">asked {"3:4" if stem == "poster" else "1:1"}</span>')
    big = ' class="big"' if stem in ("poster", "portrait") else ""
    return f'<figure{big}><a href="{k}-{stem}.webp"><img src="{k}-{stem}.webp" alt="{esc(stem)}" loading="lazy"></a><figcaption>{cap}</figcaption></figure>'


def pictures_html(repo: str, r: dict) -> str:
    k = key(repo)
    if not r["fmt"]:
        figs = figure(k, "portrait", None) if (r["dir"] / "deliverables" / "portrait.png").exists() else ""
    else:
        figs = "".join(figure(k, stem, r["fmt"].get(stem)) for stem in media.FILES if stem in r["fmt"])
    return f"<h2>The pictures</h2><div class=\"pics\">{figs}</div>"


def text_html(repo: str, r: dict) -> str:
    if r["poster_lines"] is None and r["bag"] is None:
        return ""
    hand = REVIEWS.get(repo, {})
    rows = [f"<tr><td>{esc(line)}</td><td>{verdict_span(v)}{' (checked by hand)' if str(i) in (hand.get('poster') or {}) else ''}</td></tr>"
            for i, (line, v) in enumerate(zip(LINES, r["poster_lines"] or []))]
    if r["bag"] is not None:
        rows.append(f"<tr><td>Morning Loaf (on the bag)</td><td>{verdict_span(r['bag'])}{' (checked by hand)' if 'bag' in hand else ''}</td></tr>")
    return ("<h2>The text, read letter by letter</h2><p class=\"mute\">Read by OCR (macOS Vision, five passes); a line OCR could not "
            "find as written was looked at by hand.</p><table><tr><th>Asked for</th><th>Written</th></tr>" + "".join(rows) + "</table>")


def mascot_html(repo: str, r: dict) -> str:
    m = (r["score"].get("judge") or {}).get("mascot")
    if not m:
        return ""
    override = REVIEWS.get(repo, {}).get("note", "") if "mascot_text" in REVIEWS.get(repo, {}) else ""
    yes = lambda v: "yes" if v else "no"  # noqa: E731
    return (f"<h2>The mascots (judged by a vision model)</h2><table><tr><th>Same character in all four (1-5)</th><td>{m.get('same_character')}</td></tr>"
            f"<tr><th>Poses as asked (of 4)</th><td>{r['poses']}</td></tr><tr><th>Chef's hat and red scarf in all four</th><td>{yes(m.get('hat_and_scarf_all'))}</td></tr>"
            f"<tr><th>Text on them</th><td>{yes(r['mascot_text'])}{' (by hand: ' + esc(override) + ')' if override else ''}</td></tr></table>"
            f"<p class=\"mute\">The judge's note: {esc(m.get('note', ''))}</p>")


def page(repo: str, r: dict, g: str, own: bool) -> str:
    name = "Control: Claude Code with no image skill" if repo == CONTROL else repo
    imgs = r["score"]["images"]
    used = ", ".join(imgs["models"]) or "none"
    head = (f"<h1>{esc(name)}: image test, {DATE}</h1><p class=\"mute\">{BRIEF_LINE} {r['minutes']} minutes; {imgs['calls']} image calls "
            f"(${imgs['cost']:.3f}), drawn by {esc(used)}. <a href=\"{URL}RESULTS.md\">All results</a> · <a href=\"{URL}in/brief.md\">The brief</a> · "
            f"<a href=\"{URL}score_image.py\">How it is scored</a></p>")
    note = f"<p>{esc(NOTES[repo][0])}</p>" if repo in NOTES else ""
    ps = "".join(f"<li>{esc(p[1])}</li>" for p in problems(r)) if g == "broke" else ""
    result = f"<h2>Result</h2><p><b>{GROUP[g][0]}</b>{' · a look of its own' if own else ''}</p>{f'<ul>{ps}</ul>' if ps else ''}"
    closing = f"<h2>How it went (the session's closing message)</h2><pre>{esc(final_message(r['dir'] / 'transcript.jsonl')[:4000])}</pre>"
    body = EVIDENCE_STYLE + head + note + result + pictures_html(repo, r) + text_html(repo, r) + mascot_html(repo, r) + closing
    return shell(f"{name}: image test", PAGE, body)
