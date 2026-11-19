"""The test section of /best/claude-motion-alternatives/: the video test's Tidepool brief, for the tools on that page.

  python ops/video-runs/claude_motion.py      # after score_video.py

Owner, 2026-11-19: the Claude Motion page needs OpenMotion (nexu-io/openmotion) tested. It ran the same brief as the
video test (in/brief.md) on 2026-11-19; the other tools here are the video test's own runs of 2026-10-11 that are also
on the Claude Motion page. Claude Motion itself was not run (it is for Team and Enterprise plans only).

Writes OpenMotion's media and evidence page to frontend/public/best-runs/video/ (the 2026-10-11 runs' files are already
there, written by evidence.py) and the "claude-motion-alternatives" entry of frontend/scripts/scenario-runs.json. The page has no
method block, so the entry's intro, finding and verdict carry the method and the limits.
evidence.py is left alone: its page (claude-video-skills) is the 2026-10-11 test of 16 skills.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from evidence import CLIP, CONTROL, DEST, GROUPS, LOOK, LOOK_CELL, NOTES, OUT, URL, publish_media  # noqa: E402
from runs_common import esc, final_message, key, shell, write_runs  # noqa: E402

SLUG, NEW, OLD = "claude-motion-alternatives", "nexu-io/openmotion", "2026-10-11"
NEW_DATE = "2026-11-19"
# The video test's runs that are also on the Claude Motion page (scenario-kinds.json), plus OpenMotion.
ON_PAGE = [NEW, "heygen-com/hyperframes", "remotion-dev/skills", "calesthio/OpenMontage", "digitalsamba/claude-code-video-toolkit",
           "feitangyuan/onetake", "iart-ai/motion-skills", "charlie947/motion-graphics-skills", "echris6/motion-video-kit",
           "howseen-ai/claude-motion-design", "op7418/guizang-product-video-skill", "vibe-motion/skills"]
LOOK_NEW = "own"   # judged by eye from its frames on 2026-11-19: a coastline of beach dots, a status circle under rain, a timer ring
NOTE_NEW = ("Installs a local studio and MCP server; drew a coastline of beach dots, a status circle under rain and a timer ring, with music made in code.",
            "会在本机装一个工作室和 MCP 服务；画了一条亮起的海滩点海岸线、雨中的状态圆和倒计时环，配乐用代码生成。")
SLOW_MINUTES = 15


def look(repo: str) -> str:
    if repo == CONTROL:
        return "control"
    return LOOK_NEW if repo == NEW else next(k for k, v in LOOK.items() if repo in v)


def note(repo: str) -> tuple[str, str] | None:
    return NOTE_NEW if repo == NEW else NOTES.get(repo)


def when(repo: str) -> str:
    return NEW_DATE if repo == NEW else OLD


def page(r: dict) -> str:
    """OpenMotion's evidence page (the 2026-10-11 runs keep the pages evidence.py wrote)."""
    k, run = key(r["repo"]), OUT / key(r["repo"])
    checks = "".join(f"<tr><th>{esc(label)}</th><td>{'<span class=ok>pass</span>' if r['checks'][c] else '<span class=no>fail</span>'}</td><td>{esc(detail)}</td></tr>" for c, label, detail in (
        ("playable", "Renders to a playable file", "H.264"), ("spec", "Length, size and frame rate as asked", f"{r['seconds']} s, {r['size']}, {r['fps']} fps"),
        ("copy", "All five lines readable", f"{r['lines_readable']} of 5"), ("moves", "The picture moves", f"{round(r['still_share'] * 100)}% of sampled frame pairs held still")))
    return shell(f"{r['repo']}: video test", ("/best/claude-motion-alternatives/", "Claude Motion alternatives"), f"""<h1>{esc(r['repo'])}: test run, {NEW_DATE}</h1>
<p class="mute">The video test's brief: a 15-second promo for a made-up app, five fixed lines of on-screen copy, 1920 x 1080 at 30 frames per second. Claude Code (Claude Opus 5.5) made it with the tool
in a throwaway sandbox with no API keys for video, image or voice models. {r['minutes']} minutes; sound: {'yes' if r['audio'] else 'no'}. The other tools ran the same brief on {OLD}.
<a href="{URL}RESULTS.md">All results</a> · <a href="{URL}in/brief.md">The brief</a> · <a href="{URL}score_video.py">How it is checked</a></p><p>{esc(NOTE_NEW[0])}</p>
<video controls preload="metadata" poster="{k}.jpg" style="width:100%;border-radius:8px;border:1px solid var(--line)"><source src="{k}.mp4" type="video/mp4"></video>
<h2>The four checks</h2><table>{checks}</table>
<h2>Frames sampled twice a second</h2><a href="{k}-frames.jpg"><img src="{k}-frames.jpg" alt="{esc(r['repo'])}: frames sampled at two per second"></a>
<h2>How it was made (the session's closing message)</h2><pre>{esc(final_message(run / 'transcript.jsonl')[:4000])}</pre>""")


def card(r: dict) -> dict:
    lk = LOOK_CELL[look(r["repo"])]
    cells = [[f"{r['passed']}/4", None, "touch-ups"], [f"{r['lines_readable']}/5", None], ["Yes", "有"] if r["audio"] else ["No", "无"], lk,
             [f"{r['minutes']} min", f"{r['minutes']} 分钟", "substantial" if r["minutes"] > SLOW_MINUTES else "num"], [when(r["repo"]), None]]
    bits = [[f"made the 15-second test film in {r['minutes']} min ({when(r['repo'])})", f"{r['minutes']} 分钟做出 15 秒测试片（{when(r['repo'])}）"],
            ["all four checks passed", "四项检查全部通过"], ["with sound", "带声音"] if r["audio"] else ["no sound", "没有声音"], [lk[0].lower(), lk[1]]]
    out = {"ran": True, "stars": r["stars"], "sheet": key(r["repo"]) + ".html", "cells": cells, "bits": bits}
    if note(r["repo"]):
        out.update(note=note(r["repo"])[0], note_zh=note(r["repo"])[1])
    return out


def clip(r: dict) -> dict:
    k = key(r["repo"])
    name = "No skill" if r["repo"] == CONTROL else r["repo"].split("/")[1]
    return {"name": name, "src": f"{k}.mp4", "poster": f"{k}.jpg", "group": look(r["repo"]),
            "caption": [f"{r['minutes']} min · {'sound' if r['audio'] else 'no sound'}", f"{r['minutes']} 分钟 · {'有声音' if r['audio'] else '无声音'}"]}


VERDICT = {
    "title": ["Which one to install", "到底装哪个"],
    "basis": ["after having each make the same film", "让每个都做同一条片子之后"], "more": ["Watch the films →", "看成片 →"],
    "rule": ["Not ranked: all {n} tools, and Claude Code with no tool, passed the same four checks (a playable file, the length and size asked for, all five lines of copy readable, a picture that moves). OpenMotion ran on {new}, the rest on {old}. Claude Motion itself was not tested: it is for Team and Enterprise plans only.",
             "不排名次：{n} 个工具和不装工具的 Claude Code 都通过了同样的四项检查（能播放的文件、时长和尺寸符合要求、五句文案都读得到、画面在动）。OpenMotion 是 {new} 跑的，其余是 {old}。Claude Motion 本身没有测：它只开放给 Team 和 Enterprise 套餐。"],
    "picks": [
        {"repo": NEW, "role": ["For a Claude Motion-style studio you run yourself", "想要自己能跑的 Claude Motion 式工作室"],
         "why": ["It passed every check in 12.9 minutes with music made in code and a look of its own, and leaves an editable project in a local studio. It installs a studio and an MCP server, so setup is heavier than a skill.",
                 "12.9 分钟通过全部检查，配乐用代码生成，有自己的样子，还留下一个能在本机工作室里接着改的项目。它要装工作室和 MCP 服务，比装一个 skill 重。"]},
        {"repo": "remotion-dev/skills", "role": ["To build your own design in Remotion", "想用 Remotion 做自己的设计"],
         "why": ["Remotion's own skills: reliable rendering in 4.5 minutes. The film it makes unprompted is close to the default, so bring your own design direction.",
                 "Remotion 官方的 skill：渲染稳定，4.5 分钟。不给方向时它做出的片子接近默认风格，所以设计方向要你自己给。"]},
        {"repo": "feitangyuan/onetake", "role": ["For a film with one idea running through it", "想要一个贯穿全片的创意"],
         "why": ["A single drop of water carries all five lines with no cuts.", "一滴水不切镜地带出全部五句。"]},
    ],
    "avoid_label": ["Know before you pick:", "选之前要知道："],
    "avoid": [{"repo": "heygen-com/hyperframes", "why": ["the most-starred renderer here took 23.5 minutes on a 15-second brief", "这里星数最高的渲染器，15 秒的需求做了 23.5 分钟"]}],
    "caveat": ["Whichever you pick: you may not need one for a simple promo. Claude Code with no tool made a film that passed every check in 4.4 minutes. A tool earns its place with a look, a workflow, or footage to edit.",
               "不管选哪个：简单的宣传片可能根本不需要工具。不装工具的 Claude Code 用 4.4 分钟做出了一条通过全部检查的成片。工具的价值在于风格、流程，或者处理你已有的素材。"],
}


def main() -> None:
    by = {r["repo"]: r for r in json.loads((HERE / "results.json").read_text()) if r["ran"]}
    rows = [by[r] for r in ON_PAGE]
    assert all(r["passed"] == 4 for r in rows), "a run failed a check: the page's text says every one passed"
    control, new = by[CONTROL], by[NEW]
    publish_media(new)
    (DEST / (key(NEW) + ".html")).write_text(page(new))
    tools = sorted(rows, key=lambda r: r["minutes"])
    n, sound = len(tools), sum(r["audio"] for r in tools)
    fast, slow = tools[0]["minutes"], tools[-1]["minutes"]
    own = sum(look(r["repo"]) == "own" for r in tools)
    verdict = {**VERDICT, "rule": [x.format(n=n, new=NEW_DATE, old=OLD) for x in VERDICT["rule"]]}
    write_runs(SLUG, {
        "type": "table", "date": NEW_DATE, "dir": "/best-runs/video/", "results": URL + "RESULTS.md",
        "title": ["Claude Motion alternatives tested: the same 15-second film", "实测对比：同一条 15 秒片子"],
        "intro": [f"We had {n} of these tools make the same film in a throwaway sandbox, driven by Claude Code (Claude Opus 5.5): a 15-second promo for a made-up app, with five fixed lines of on-screen copy, at 1920 x 1080 and 30 frames per second, on a machine with no API keys for video, image or voice models. OpenMotion ran on {NEW_DATE}; the other {n - 1} are from our video skill test of {OLD}, as is the control, Claude Code with no tool. Four things were checked from each file: it plays, it is the length and size asked for, every line of copy can be read in frames sampled twice a second, and the picture moves. How good a film looks is not scored. Claude Motion itself was not run: it is for Team and Enterprise plans only.",
                  f"我们让其中 {n} 个工具在用完即删的沙箱里由 Claude Code（Claude Opus 5.5）调用，做同一条片子：给一个虚构应用做 15 秒宣传片，五句固定的画面文案，1920 x 1080、每秒 30 帧，机器上没有任何视频、图像或语音模型的密钥。OpenMotion 是 {NEW_DATE} 跑的；其余 {n - 1} 个和对照（不装工具的 Claude Code）来自我们 {OLD} 的视频 skill 实测。每个文件查四件事：能播放、时长和尺寸符合要求、每句文案在每秒抽两帧的画面里都读得到、画面在动。片子好不好看不打分。Claude Motion 本身没有跑：它只开放给 Team 和 Enterprise 套餐。"],
        "finding": [f"All {n} rendered a film that passed all four checks, with no line of copy missing and nothing added, and so did Claude Code with no tool, in {control['minutes']} minutes. OpenMotion took {new['minutes']} minutes and added music. Across the {n}, time ran from {fast} to {slow} minutes, {sound} added sound, and {own} have a look of their own, by our eye.",
                    f"{n} 个全部渲染出了通过四项检查的成片，文案一句没少、也没有多加内容；不装工具的 Claude Code 也一样，用了 {control['minutes']} 分钟。OpenMotion 用了 {new['minutes']} 分钟，加了配乐。{n} 个里耗时从 {fast} 到 {slow} 分钟，{sound} 个加了声音，按我们的眼睛看 {own} 个有自己的样子。"],
        "gallery": {"width": CLIP[0], "height": CLIP[1], "groups": GROUPS, "items": [clip(control), *[clip(r) for r in tools]],
                    "note": ["The films, side by side. Press play on any of them; each is 15 seconds.", "成片并排放在这里。点任意一条播放，每条 15 秒。"]},
        "name_col": ["Tool", "工具"],
        "columns": [["Checks passed (of 4)", "通过检查（共 4 项）"], ["Lines of copy readable (of 5)", "读得到的文案（共 5 句）"], ["Sound", "声音"],
                    ["Look, by eye", "观感（肉眼判断）"], ["Time to make", "制作耗时"], ["Tested", "测试日期"]],
        "see": ["Watch it and see the frames →", "看成片和抽帧 →"], "evidence": ["The film", "成片"],
        "line_label": ["Claude Motion alternatives test:", "Claude Motion 平替实测："], "control": {"sheet": key(CONTROL) + ".html"},
        "verdict": verdict, "runs": {r["repo"]: card(r) for r in tools}})
    print(f"{n} tools, control {control['minutes']} min, {fast}-{slow} min, sound {sound}/{n}, OpenMotion {new['minutes']} min")


if __name__ == "__main__":
    main()
