"""Evidence for the animation page's test (/best/animation-skills/): each run's recording of the same brief, what was
checked in it, and the test's entry in frontend/scripts/scenario-runs.json ("animation-skills").

  python3 ops/animation-runs/evidence_animation.py

Writes frontend/public/best-runs/animation/ (a small copy of each preview.mp4 with its poster and frame sheet, one
noindex page per run) and ops/animation-runs/RESULTS.md. Each brief's items come from the judge's answers
(score_animation.py), the deliverable's own file (a Lottie file's fields, the web page's reduced-motion rule) and the
corrections in review.json, made by hand on the full recording where 8 sampled frames missed a short event.
"""
import html
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runs_common import shell  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEST = ROOT / "frontend" / "public" / "best-runs" / "animation"
RUNS_JSON = ROOT / "frontend" / "scripts" / "scenario-runs.json"
KEY, DIR, DATE = "animation-skills", "/best-runs/animation/", "2026-11-18"
URL = "https://github.com/zhuyansen/agent-skills-hub/blob/main/ops/animation-runs/"
CLIP_W, CRF = 640, 30
REVIEW = json.loads((HERE / "review.json").read_text())
esc = html.escape

KINDS = {   # in the page's order: its label, the brief in one line, and each item checked
    "web": (("Web & UI motion", "网页与界面动效"),
            ("A bakery landing page: the logo draws in, the headline comes in word by word, three cards rise in turn, a button pulses, a croissant turns with the scroll, and nothing moves for reduced motion.",
             "面包店落地页：logo 描线出现，标题逐词进入，三张卡片依次升起，按钮跳一下，往下滚时牛角包跟着转，开了减少动态时不动。"),
            {"logo_draws_in": ("logo draws in", "logo 描线出现"), "headline_word_by_word": ("headline word by word", "标题逐词进入"),
             "headline_text_right": ("headline text", "标题文字"), "three_cards_staggered": ("cards in turn", "卡片依次出现"),
             "card_names_right": ("card names", "卡片名称"), "button_shown": ("button", "按钮"),
             "scroll_section_shown": ("scroll section", "滚动区块"), "croissant_turns_with_scroll": ("croissant turns with scroll", "牛角包随滚动转"),
             "reduced_motion": ("reduced motion respected", "支持减少动态")}),
    "lottie": (("Lottie, SVG & animated icons", "Lottie、SVG 与动态图标"),
               ("Animate the bakery's logo as a 2-second Lottie loop: the loaf drops in and squashes, the steam rises line by line, the name fades in, and it loops without a jump.",
                "把面包店 logo 做成 2 秒循环的 Lottie：面包落下并压扁一下，热气一条条升起，店名淡入，首尾无缝循环。"),
               {"loaf_drops_and_squashes": ("loaf drops and squashes", "面包落下并压扁"), "steam_rises_in_turn": ("steam in turn", "热气依次升起"),
                "words_fade_in": ("name fades in", "店名淡入"), "logo_kept": ("logo kept", "保留原 logo"), "lottie_file": ("a Lottie file", "交付 Lottie 文件")}),
    "sprite": (("Game sprites & pixel art", "游戏精灵图与像素动画"),
               ("Pixel-art sprite sheets of the bread mascot: an 8-frame walk to the right and a 4-frame idle, 128 px frames, transparent, the same character in every frame.",
                "面包吉祥物的像素风精灵图：8 帧向右走、4 帧待机呼吸，每帧 128 px、透明背景、每帧角色一致。"),
               {"pixel_art": ("pixel art", "像素风"), "is_the_mascot": ("the mascot", "是这个吉祥物"), "walk_cycle_reads": ("walk cycle", "走路循环"),
                "faces_right": ("walks to the right", "朝右走"), "idle_breathes": ("idle breathes", "待机呼吸"),
                "consistent_across_frames": ("same in every frame", "每帧一致"), "same_ground_line": ("same ground line", "脚落在同一条线"),
                "sheets_right": ("sheet sizes and transparency", "图集尺寸和透明背景")}),
    "rig": (("Characters, rigging & 3D", "角色、骨骼与 3D 动画"),
            ("Make the bread mascot wave: the right arm rises and waves twice, the body bobs, the eyes blink once, and it ends where it started.",
             "让面包吉祥物挥手：右臂抬起挥两下，身体轻轻起伏，眨一次眼，回到起始姿势。"),
            {"is_the_mascot": ("the mascot", "是这个吉祥物"), "right_arm_waves": ("right arm waves", "右臂挥手"), "body_bobs": ("body bobs", "身体起伏"),
             "blink_seen": ("blinks", "眨眼"), "ends_in_start_pose": ("ends in the start pose", "回到起始姿势")}),
    "diagram": (("Animated diagrams", "动态图解"),
                ("An animated diagram of an online order: seven steps from customer to courier in order, a dot travelling along each arrow, and a failed-payment branch that loops back.",
                 "一张网店下单流程的动态图：从顾客到快递的七步按顺序出现，每条箭头上有点在走，还有一条支付失败后重试的回环。"),
                {"steps_present": ("all 7 steps", "7 个步骤齐全"), "order_right": ("in order", "顺序正确"), "dots_travel": ("dots travel", "点沿箭头移动"),
                 "retry_branch": ("retry branch", "重试分支"), "retry_loops_back": ("loops back", "回到支付"), "labels_readable": ("labels readable", "标签可读")}),
    "art": (("Code art & math animation (Manim)", "代码艺术与数学动画 (Manim)"),
            ("A 12-second explainer: dough doubles every hour, with a clock and a growing curve beside it, ending on \"Size doubles every hour\".",
             "12 秒讲解动画：面团每小时翻倍，旁边有时钟和一条随之增长的曲线，最后落在\"Size doubles every hour\"。"),
            {"dough_grows_doubling": ("dough doubles", "面团翻倍"), "clock_shows_hours": ("clock", "时钟"), "curve_plots_growth": ("curve", "曲线"),
             "curve_is_exponential": ("curve is exponential", "曲线是指数型"), "end_line_right": ("closing line", "结尾那句")}),
}
NOT_RUN = {
    "shinshin86/mesh-avatar-studio": ("Its runtime only moves small parts near the face, so it cannot raise and wave an arm; the agent stopped and said so rather than change the tool.",
                                      "它的运行时只能动脸附近的小部件，抬不起手臂挥手；agent 说明原因后停下，没有去改这个工具。"),
}
VERDICT = {   # owner-facing picks, one per kind, from the table and the recordings (ranked by nothing: one each)
    "web": ("greensock/gsap-skills", ("For web motion you will keep building on", "要接着往下做的网页动效"),
            ("Every item of the brief in 1.9 minutes, written with GSAP's own ScrollTrigger, SplitText and DrawSVG, so the next animation uses the same tools.",
             "1.9 分钟做到测试题全部要求，用的是 GSAP 自己的 ScrollTrigger、SplitText 和 DrawSVG，下一个动效可以接着用同一套。")),
    "lottie": ("diffusionstudio/lottie", ("For a Lottie file", "要一个 Lottie 文件"),
               ("A valid 512 x 512 Lottie loop with every item of the brief, the squash included. pixel2motion made an animated SVG instead.",
                "交付了合规的 512 x 512 Lottie 循环，测试题全部做到，压扁也有。pixel2motion 交的是动态 SVG。")),
    "sprite": ("aldegad/sprite-gen", ("For game sprites", "做游戏精灵图"),
               ("A side-on walk to the right and a breathing idle, the right sizes and transparent, in 6.2 minutes; agent-sprite-forge did as well in 7.7. Claude Code with no tool drew the mascot walking towards the viewer.",
                "侧身向右走、待机呼吸，尺寸和透明背景都对，用时 6.2 分钟；agent-sprite-forge 同样全对，用了 7.7 分钟。不装工具的 Claude Code 画成了面朝镜头走。")),
    "rig": ("img2threejs/img2threejs", ("For a character that moves", "让角色动起来"),
            ("Every item of the brief in 2.4 minutes, and the judge's 5 of 5 for looks. Claude Code with no tool did the same in 0.9 minutes.",
             "2.4 分钟做到全部要求，评审观感 5/5。不装工具的 Claude Code 0.9 分钟也做到了。")),
    "diagram": ("Aryanutkarsh/SeeCode", ("For an animated diagram", "做动态图解"),
                ("All seven steps, the travelling dots and the retry loop, the judge's 5 of 5 for looks, in 2.7 minutes.",
                 "七个步骤、移动的点和重试回环都有，评审观感 5/5，用时 2.7 分钟。")),
    "art": ("alexgreensh/anidoodle", ("For an explainer animation", "做讲解动画"),
            ("Every item of the brief and the judge's 5 of 5 for looks, in a hand-drawn style. huashu-art-motion made the richest scene (a bowl on a counter) in 7.6 minutes.",
             "做到全部要求，评审观感 5/5，手绘风格。huashu-art-motion 的画面最丰富（台面上的一碗面团），用了 7.6 分钟。")),
}


def items(kind: str, run: Path, s: dict) -> dict:
    """Each item of the kind's brief: True when it is there."""
    j, c = s.get("judge") or {}, s.get("checks") or {}
    out = {k: (j.get(k) == 7 if k == "steps_present" else j.get(k) is True) for k in KINDS[kind][2] if k in j}
    if kind == "web":
        out["reduced_motion"] = c.get("reduced_motion") is True
    if kind == "lottie":
        out["lottie_file"] = c.get("lottie_valid") is True and c.get("lottie_size") == [512, 512]
    if kind == "sprite":
        out["sheets_right"] = all((c.get(n) or {}).get("size_right") and (c.get(n) or {}).get("transparent") for n in ("walk", "idle"))
    fix = REVIEW.get(f"{kind}/{run.name}", {})
    out.update({k: v for k, v in fix.items() if k in KINDS[kind][2]})
    return {k: out.get(k, False) for k in KINDS[kind][2]}


def clip(kind: str, run: Path) -> tuple[str, str]:
    """A small copy of the recording and its poster (a frame 60% in)."""
    name = f"{kind}-{run.name}"
    src = run / "deliverables" / "preview.mp4"
    DEST.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-an", "-vf", f"scale={CLIP_W}:-2", "-c:v", "libx264",
                    "-crf", str(CRF), "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(DEST / f"{name}.mp4")], check=True)
    secs = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)],
                                capture_output=True, text=True).stdout or 1)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{secs * 0.6:.2f}", "-i", str(src), "-frames:v", "1", "-vf", f"scale={CLIP_W}:-2",
                    "-q:v", "4", str(DEST / f"{name}.jpg")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(run / "sheet.png"), "-q:v", "4", str(DEST / f"{name}-frames.jpg")], check=True)
    return f"{name}.mp4", f"{name}.jpg"


def delivered(kind: str, s: dict) -> tuple[str, str]:
    c = s.get("checks") or {}
    if kind == "lottie":
        return ("Lottie (.json)", "Lottie（.json）") if c.get("format") == "lottie" else ("Animated SVG", "动态 SVG")
    if kind == "sprite":
        return ("Two PNG sheets", "两张 PNG 图集")
    # Top-level files and folders, the recording and data files left out: a folder shows as "name/".
    tops = []
    for f in c.get("files", []):
        t = f.split("/")[0] + ("/" if "/" in f else "")
        if t not in tops and not t.endswith((".mp4", ".json")):
            tops.append(t)
    shown = ", ".join(tops[:2]) or "-"
    return (shown, shown)


def row(kind: str, cand: dict) -> dict | None:
    run = HERE / kind / "out" / cand["repo"].replace("/", "__")
    if not (run / "score.json").exists():
        return None
    s = json.loads((run / "score.json").read_text())
    if not s.get("preview"):
        return None
    ok = items(kind, run, s)
    return {"kind": kind, "repo": cand["repo"], "run": run, "score": s, "items": ok, "missed": [k for k, v in ok.items() if not v],
            "usage": s["usage"], "judge": s.get("judge") or {}, "stars": stars(cand["repo"])}


_STARS: dict = {}


def stars(repo: str) -> int:
    """GitHub stars on the day the evidence is written (gh api), 0 for the control."""
    if repo == "control":
        return 0
    if repo not in _STARS:
        out = subprocess.run(["gh", "api", f"repos/{repo}", "--jq", ".stargazers_count"], capture_output=True, text=True).stdout.strip()
        _STARS[repo] = int(out) if out.isdigit() else 0
    return _STARS[repo]


def met(r: dict) -> tuple[str, str]:
    n, t = len(r["items"]) - len(r["missed"]), len(r["items"])
    return f"{n}/{t}", f"{n}/{t}"


def cells(r: dict) -> list:
    u, looks = r["usage"], r["judge"].get("looks")
    n = met(r)
    return [[n[0], n[1], "touch-ups" if not r["missed"] else "one round"], [*delivered(r["kind"], r["score"]), ""],
            [f"{looks}/5" if looks else "-", f"{looks}/5" if looks else "-", "num"],
            [f"{u['minutes']} min", f"{u['minutes']} 分钟", "num"], [f"${u['cost']:.2f}", f"${u['cost']:.2f}", "num"]]


def bits(r: dict) -> list:
    labels = KINDS[r["kind"]][2]
    head = ["every item of the brief", "测试题要求全部做到"] if not r["missed"] else [
        "missed: " + ", ".join(labels[k][0] for k in r["missed"]), "没做到：" + "、".join(labels[k][1] for k in r["missed"])]
    u = r["usage"]
    return [head, [f"{u['minutes']} min", f"{u['minutes']} 分钟"], [f"${u['cost']:.2f} at API prices", f"按 API 价 ${u['cost']:.2f}"]]


def page(r: dict, video: str, poster: str) -> str:
    kind, s = r["kind"], r["score"]
    (label_en, _), (brief_en, _), labels = KINDS[kind]
    who = "Claude Code with no animation tool (the control)" if r["repo"] == "control" else r["repo"]
    li = "".join(f"<li class=\"{'ok' if v else 'no'}\">{'✓' if v else '✗'} {esc(labels[k][0])}</li>" for k, v in r["items"].items())
    fix = REVIEW.get(f"{kind}/{r['run'].name}", {}).get("why")
    j = r["judge"]
    v = s.get("video") or {}
    body = f"""<h1>{esc(who)}</h1>
<p class="mute">Animation test, {DATE} · {esc(label_en)} · driven by Claude Code (Claude Opus 5.5) in a throwaway sandbox</p>
<p><b>The brief:</b> {esc(brief_en)} <a href="{URL}{kind}/in/brief.md">Full brief →</a></p>
<video controls playsinline preload="metadata" poster="{esc(poster)}" style="width:100%;max-width:960px;border-radius:8px"><source src="{esc(video)}" type="video/mp4"></video>
<h2>What was checked</h2><ul style="list-style:none;padding:0">{li}</ul>
{f'<p class="mute">Checked by hand on the full recording: {esc(fix)}</p>' if fix else ''}
<p class="mute">The recording: {v.get('width')} x {v.get('height')}, {v.get('fps')} fps, {v.get('seconds')} s. Judge (gpt-6-astra, 8 frames): follows the brief {j.get('follows_brief')}/5, looks {j.get('looks')}/5{('; noted: ' + esc('; '.join(j.get('glitches') or []))) if j.get('glitches') else ''}.</p>
<p class="mute">Time {r['usage']['minutes']} min (installing the tool included) · {r['usage']['turns']} turns · ${r['usage']['cost']:.2f} at API prices · files: {esc(', '.join((s.get('checks') or {}).get('files', [])[:12]))}</p>
<h2>The 8 frames the judge saw</h2><img src="{esc(video.replace('.mp4', '-frames.jpg'))}" alt="8 frames from the recording" loading="lazy">
<h2>The agent's last words</h2><pre>{esc(s.get('last_words') or '')}</pre>"""
    return shell(f"{who}: animation test", ("/best/animation-skills/#test-results", "Animation skills"), body)


def results_md(rows: dict, missing: list) -> str:
    out = [f"# Animation test, {DATE}\n", "Generated by evidence_animation.py. One brief per kind (in each <kind>/in/brief.md), the top 2 tools of each kind on "
           "/best/animation-skills/ and a control (Claude Code with no tool). Items from the judge (gpt-6-astra on 8 frames), the files, "
           "and review.json (by hand on the full recording).\n"]
    for kind, rs in rows.items():
        out.append(f"\n## {KINDS[kind][0][0]}\n\n| Run | Items met | Missed | Delivered | Looks | Minutes | Cost (API prices) |\n|---|---|---|---|---|---|---|")
        for r in rs:
            out.append(f"| {r['repo']} | {met(r)[0]} | {', '.join(r['missed']) or '-'} | {delivered(kind, r['score'])[0]} | "
                       f"{r['judge'].get('looks')}/5 | {r['usage']['minutes']} | ${r['usage']['cost']:.2f} |")
    out.append("\n## No recording\n\n" + "\n".join(f"- {m}: {NOT_RUN[m][0]}" for m in missing))
    return "\n".join(out) + "\n"


def main() -> None:
    rows, tools, controls, missing, gallery = {}, {}, {}, [], []
    for kind in KINDS:
        cands = json.loads((HERE / kind / "candidates.json").read_text())
        rs = [x for x in (row(kind, c) for c in cands) if x]
        missing += [c["repo"] for c in cands if c["repo"] in NOT_RUN]
        rs.sort(key=lambda r: (r["repo"] != "control", len(r["missed"]), -(r["judge"].get("looks") or 0), r["usage"]["minutes"]))
        rows[kind] = rs
        for r in rs:
            video, poster = clip(kind, r["run"])
            sheet = f"{kind}-{r['run'].name}.html"
            (DEST / sheet).write_text(page(r, video, poster))
            name = "No tool (control)" if r["repo"] == "control" else r["repo"].split("/")[1]
            gallery.append({"name": name, "src": video, "poster": poster, "group": kind,
                            "caption": [f"{met(r)[0]} · {r['usage']['minutes']} min", f"{met(r)[0]} · {r['usage']['minutes']} 分钟"]})
            if r["repo"] == "control":
                controls[kind] = r
            else:
                tools[r["repo"]] = {"ran": True, "stars": r["stars"], "minutes": r["usage"]["minutes"], "sheet": sheet, "group": kind,
                                    "cells": cells(r), "bits": bits(r)}
    for m in missing:
        en, zh = NOT_RUN[m]
        tools[m] = {"ran": False, "stars": stars(m), "reason": en, "reason_zh": zh}
    ran = [r for rs in rows.values() for r in rs if r["repo"] != "control"]
    full_controls = [k for k, r in controls.items() if not r["missed"]]
    entry = {
        "type": "table", "date": DATE, "dir": DIR, "results": URL + "RESULTS.md", "agent": "Claude Code (Claude Opus 5.5)", "judge": "gpt-6-astra",
        "title": ["Animation skills tested: six briefs, the top tools of each kind", "实测：六类动画，每类头部工具做同一道题"],
        "intro": [f"On {DATE} we gave the two most-starred tools of each kind on this page one brief for their kind, and gave Claude Code with no animation tool the same briefs as a control: "
                  "a landing page's motion, an animated logo, game sprite sheets, a waving mascot, an animated diagram and an explainer, all for a made-up bakery, Morning Loaf. "
                  f"Each ran in a throwaway Linux sandbox, driven by Claude Code (Claude Opus 5.5), and recorded its animation. {len(ran)} of the 12 tools made one. "
                  "Each item of a brief was checked from the recording by gpt-6-astra, from the file itself where a file can say (a Lottie file's fields, a sheet's size, the page's reduced-motion rule), "
                  "and by hand on the full recording where 8 sampled frames could miss a short event such as a blink.",
                  f"{DATE}，我们给本页每一类星数最高的两个工具各出一道本类的题，并让不装动画工具的 Claude Code 做同样的题作为对照："
                  "落地页动效、动态 logo、游戏精灵图、挥手的吉祥物、动态流程图和讲解动画，都围绕一家虚构的面包店 Morning Loaf。"
                  f"每个都在用完即删的 Linux 沙箱里由 Claude Code（Claude Opus 5.5）调用，并录下做出的动画。12 个工具里 {len(ran)} 个做出来了。"
                  "测试题的每一项由 gpt-6-astra 看录像判断；文件本身能回答的（Lottie 字段、图集尺寸、页面的减少动态规则）直接查文件；"
                  "8 帧抽样可能漏掉的短动作（比如眨眼），我们在完整录像上人工核对。"],
        "finding": [f"Claude Code with no animation tool met every item of the brief in {len(full_controls)} of 6 kinds, in 0.9 to 4 minutes. "
                    "The tools mattered in two places: sprites, where both sprite tools drew a side-on walk to the right and the no-tool run drew the mascot walking towards the viewer; "
                    "and format, where pixel2motion delivered animated SVG instead of Lottie and mesh-avatar-studio could not wave an arm at all. "
                    "Otherwise pick a tool for its look and the code it leaves you: gsap-skills writes GSAP, the Lottie skill writes a real Lottie file.",
                    f"不装动画工具的 Claude Code 在 6 类里有 {len(full_controls)} 类把测试题全部做到，每次 0.9 到 4 分钟。"
                    "工具真正拉开差距的地方有两处：精灵图，两个精灵图工具都画出了侧身向右走，不装工具的画成了面朝镜头走；"
                    "以及格式，pixel2motion 交的是动态 SVG 而不是 Lottie，mesh-avatar-studio 根本做不了挥手。"
                    "除此之外，按观感和它留给你的代码来选：gsap-skills 写的是 GSAP，Lottie skill 交的是真正的 Lottie 文件。"],
        "gallery": {"width": CLIP_W, "height": 360, "note": ["Every recording, the control first in each kind. They play on the page.", "每一段录像，每类第一个是对照组。可以直接在页面上播放。"],
                    "groups": [{"id": k, "title": list(KINDS[k][0])} for k in KINDS], "items": gallery},
        "groups": [{"id": k, "title": list(KINDS[k][0])} for k in KINDS],
        "name_col": ["Tool", "工具"],
        "columns": [["Brief items met", "做到的要求"], ["Delivered", "交付"], ["Looks (judge)", "观感（评审）"], ["Time", "耗时"], ["Cost at API prices", "按 API 价"]],
        "see": ["Watch it and see what was checked →", "看录像和检查结果 →"], "evidence": ["The recording", "录像"],
        "line_label": [f"Animation test, {DATE}:", f"{DATE} 动画实测："],
        "not_run_label": ["No animation", "没做出来"], "not_run_line": ["Tried in our animation test, no animation:", "动画实测时没做出来："],
        "control": {"sheet": "web-control.html", "label": ["See the landing page Claude Code made with no tool →", "看不装工具做的落地页 →"]},
        "verdict": {"title": ["Which one to use", "用哪个"], "ranked": False,
                    "picks": [{"repo": repo, "role": list(role), "why": list(why)} for repo, role, why in VERDICT.values()],
                    "caveat": ["Claude Code alone met the brief in most kinds, so a tool earns its place by its look, its format or the code it leaves, not by getting the job done.",
                               "多数类别里只用 Claude Code 也能做到测试题要求，所以工具的价值在观感、格式和留下的代码，而不是能不能做成。"],
                    "rule": ["One pick per kind, from these runs: every item of the brief first, then the judge's looks, then time.",
                             "每类选一个，依据这次实测：先看测试题是否全部做到，再看评审观感，最后看耗时。"]},
        "runs": tools,
    }
    runs = json.loads(RUNS_JSON.read_text())
    runs[KEY] = entry
    RUNS_JSON.write_text(json.dumps(runs, indent=1, ensure_ascii=False) + "\n")
    (HERE / "RESULTS.md").write_text(results_md(rows, missing))
    print(f"{len(ran)} tools recorded, {len(missing)} without; controls with every item: {full_controls}")
    for kind, rs in rows.items():
        print(kind, [(r["repo"].split("/")[-1], met(r)[0], r["missed"]) for r in rs])


if __name__ == "__main__":
    main()
