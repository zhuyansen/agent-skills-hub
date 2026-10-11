"""Evidence pages, the videos themselves and page data for the video test.

  python ops/video-runs/evidence.py      # after score_video.py

Writes frontend/public/best-runs/video/: <owner__repo>.mp4 (960 wide), a poster and the
sampled-frame sheet for each, <owner__repo>.html (noindex), and the "claude-video-skills" entry
of frontend/scripts/scenario-runs.json (type "table", with a gallery: the page plays the videos
side by side). Every run passed all four checks, so the page does not rank them: it groups
them by look, which is a judgement made by eye and labelled as one.
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from runs_common import PUBLIC, REPO_URL, esc, final_message, key, pair, shell, update_method, write_runs  # noqa: E402

SLUG, DATE, CONTROL = "claude-video-skills", "2026-10-11", "octocat/Hello-World"
URL = REPO_URL + "video-runs/"
OUT = HERE / "out"
DEST = PUBLIC / "video"
POSTER_WIDTH, CLIP = 640, (960, 540)
# How each film looks beside the one Claude Code made with no skill (deep teal water, waves, white centred type).
# Judged by eye from the sampled frames on 2026-10-11; the evidence pages show them.
LOOK = {
    "default": ["remotion-dev/skills", "diffusionstudio/lottie", "digitalsamba/claude-code-video-toolkit", "wshuyi/remotion-video-skill",
                "charlie947/motion-graphics-skills", "hypit-ai/hypit"],
    "own": ["heygen-com/hyperframes", "Barty-Bart/motion-graphics", "feitangyuan/onetake", "echris6/motion-video-kit", "iart-ai/motion-skills",
            "calesthio/OpenMontage", "vincentsch/explainroo", "vibe-motion/skills", "op7418/guizang-product-video-skill", "howseen-ai/claude-motion-design"],
}
LOOK_CELL = {"default": ["Close to the no-skill film", "接近不装 skill 的成片", ""], "own": ["A look of its own", "有自己的样子", "touch-ups"]}
NOTES = {
    "heygen-com/hyperframes": ("Cream paper and thin lines: the sparest film here, and the slowest to make at 23.5 minutes.", "米白底、细线条：这里最克制的一条，也是做得最慢的，23.5 分钟。"),
    "Barty-Bart/motion-graphics": ("Made for adding motion graphics to talking-head footage; with no footage it built a full-frame film of interface cards.", "本来是给真人出镜视频加动效的；没有素材时它做了一条全屏的界面卡片动画。"),
    "feitangyuan/onetake": ("One drop of water carries the whole film from line to line, with no cuts.", "一滴水贯穿全片，从一句带到下一句，没有切镜。"),
    "echris6/motion-video-kit": ("The fullest picture here, with drawn scenes and a phone mock-up; it took 21.8 minutes.", "这里画面最满的一条，有手绘场景和手机样机；用了 21.8 分钟。"),
    "iart-ai/motion-skills": ("A drawn beach scene whose weather changes with the copy; music made in code.", "一个手绘海滩场景，天气随文案变化；配乐用代码生成。"),
    "calesthio/OpenMontage": ("Runs a whole production pipeline and still needed no paid model for this brief; bold colour blocks.", "跑的是一整条制作流水线，这条需求仍然没用到付费模型；大色块风格。"),
    "vincentsch/explainroo": ("The fastest: a finished film with sound in 2 minutes.", "最快：2 分钟出一条带声音的成片。"),
    "hypit-ai/hypit": ("Drew everything in code on this machine; no paid model or account was needed for this brief.", "全部在本机用代码绘制；这条需求不需要付费模型或账号。"),
    "remotion-dev/skills": ("Remotion's own skills: a solid film in 4.5 minutes, no sound.", "Remotion 官方的 skill：4.5 分钟出一条扎实的成片，没有声音。"),
}
VERDICT = {
    "title": ["Which one to install", "到底装哪个"],
    "basis": ["after having each make the same film", "让每个都做同一条片子之后"], "more": ["Watch the films →", "看成片 →"],
    "rule": ["Not ranked: all {n} skills, and Claude Code with no skill, passed the same four checks (a playable file, the length and size asked for, all five lines of copy readable, a picture that moves). The table is in order of time taken. Whether a film looks like the default or has a look of its own was judged by eye; watch them and judge for yourself.",
             "不排名次：全部 {n} 个 skill，以及不装 skill 的 Claude Code，都通过了同样的四项检查（能播放的文件、时长和尺寸符合要求、五句文案都读得到、画面在动）。表格按耗时排列。成片是接近默认风格还是有自己的样子，是我们看图判断的；请自己看成片来判断。"],
    "picks": [
        {"repo": "vincentsch/explainroo", "role": ["For a finished film fast", "想尽快出一条成片"],
         "why": ["Two minutes from brief to a film with sound, the quickest of the sixteen, and it does not look like the default.",
                 "从需求到带声音的成片只用了 2 分钟，16 个里最快，而且看起来不像默认风格。"]},
        {"repo": "feitangyuan/onetake", "role": ["For a film with one idea running through it", "想要一个贯穿全片的创意"],
         "why": ["A single drop of water carries all five lines with no cuts. For a fuller, illustrated picture the one to watch is motion-video-kit, if you can wait 22 minutes.",
                 "一滴水不切镜地带出全部五句。想要画面更满的插画风，可以看 motion-video-kit，前提是你能等 22 分钟。"]},
        {"repo": "remotion-dev/skills", "role": ["To build your own design in Remotion", "想用 Remotion 做自己的设计"],
         "why": ["Remotion's own skills: reliable rendering in 4.5 minutes. The film it makes unprompted is close to the default, so bring your own design direction.",
                 "Remotion 官方的 skill：渲染稳定，4.5 分钟。不给方向时它做出的片子接近默认风格，所以设计方向要你自己给。"]},
    ],
    "avoid_label": ["Know before you pick:", "选之前要知道："],
    "avoid": [
        {"repo": "heygen-com/hyperframes", "why": ["the most-starred renderer here took 23.5 minutes on a 15-second brief", "这里星数最高的渲染器，15 秒的需求做了 23.5 分钟"]},
        {"repo": "Barty-Bart/motion-graphics", "why": ["built for talking-head footage, which this brief did not have", "是为真人出镜素材做的，而这条需求没有素材"]},
    ],
    "caveat": ["Whichever you pick: you may not need one for a simple promo. Claude Code with no skill made a film that passed every check in 4.4 minutes. A skill earns its place with a look, a workflow, or footage to edit.",
               "不管选哪个：简单的宣传片可能根本不需要 skill。不装 skill 的 Claude Code 用 4.4 分钟做出了一条通过全部检查的成片。skill 的价值在于风格、流程，或者处理你已有的素材。"],
}
GROUPS = [{"id": "control", "title": ["No skill installed (the control)", "不装 skill（对照）"]},
          {"id": "own", "title": ["A look of their own", "有自己的样子"]},
          {"id": "default", "title": ["Close to the no-skill film", "接近不装 skill 的成片"]}]


def look(repo: str) -> str:
    return "control" if repo == CONTROL else next(k for k, v in LOOK.items() if repo in v)


def publish_media(r: dict) -> None:
    run, k = OUT / key(r["repo"]), key(r["repo"])
    shutil.copy2(run / "web.mp4", DEST / f"{k}.mp4")
    shutil.copy2(run / "sheet.jpg", DEST / f"{k}-frames.jpg")
    frames = json.loads((run / "copy.json").read_text())["frames"]["1"]
    first = Image.open(run / "frames" / f"f-{frames[len(frames) // 2]:02d}.jpg").convert("RGB")
    first.resize((POSTER_WIDTH, round(first.height * POSTER_WIDTH / first.width))).save(DEST / f"{k}.jpg", quality=80)


def films_grid(rows: list[dict]) -> None:
    """One picture of every film's opening line, for places that cannot play video (the GitHub list)."""
    from PIL import ImageDraw, ImageFont
    cols, w, h, label = 4, 480, 270, 26
    grid = Image.new("RGB", (w * cols, (h + label) * -(-len(rows) // cols)), "white")
    draw, font = ImageDraw.Draw(grid), ImageFont.load_default(size=15)
    for i, r in enumerate(rows):
        x, y = (i % cols) * w, (i // cols) * (h + label)
        grid.paste(Image.open(DEST / f"{key(r['repo'])}.jpg").convert("RGB").resize((w, h)), (x, y + label))
        name = "no skill (control)" if r["repo"] == CONTROL else r["repo"].split("/")[1]
        draw.text((x + 8, y + 5), f"{name} · {r['minutes']} min", fill="black", font=font)
    grid.save(DEST / "films.jpg", quality=82)


def page(r: dict, name: str) -> str:
    k, run = key(r["repo"]), OUT / key(r["repo"])
    checks = "".join(f"<tr><th>{esc(label)}</th><td>{'<span class=ok>pass</span>' if r['checks'][c] else '<span class=no>fail</span>'}</td><td>{esc(detail)}</td></tr>" for c, label, detail in (
        ("playable", "Renders to a playable file", "H.264"), ("spec", "Length, size and frame rate as asked", f"{r['seconds']} s, {r['size']}, {r['fps']} fps"),
        ("copy", "All five lines readable", f"{r['lines_readable']} of 5"), ("moves", "The picture moves", f"{round(r['still_share'] * 100)}% of sampled frame pairs held still")))
    note = f"<p>{esc(NOTES[r['repo']][0])}</p>" if r["repo"] in NOTES else ""
    return shell(f"{name}: video test", ("/best/claude-video-skills/", "Claude Code video skills"), f"""<h1>{esc(name)}: test run, {DATE}</h1>
<p class="mute">The same brief for every skill: a 15-second promo for a made-up app, five fixed lines of on-screen copy, 1920 x 1080 at 30 frames per second. Claude Code (Claude Opus 5.5) made it with the skill
in a throwaway sandbox with no API keys for video, image or voice models. {r['minutes']} minutes; sound: {'yes' if r['audio'] else 'no'}.
<a href="{URL}RESULTS.md">All results</a> · <a href="{URL}in/brief.md">The brief</a> · <a href="{URL}score_video.py">How it is checked</a></p>{note}
<video controls preload="metadata" poster="{k}.jpg" style="width:100%;border-radius:8px;border:1px solid var(--line)"><source src="{k}.mp4" type="video/mp4"></video>
<h2>The four checks</h2><table>{checks}</table>
<h2>Frames sampled twice a second</h2><a href="{k}-frames.jpg"><img src="{k}-frames.jpg" alt="{esc(name)}: frames sampled at two per second"></a>
<h2>How it was made (the session's closing message)</h2><pre>{esc(final_message(run / 'transcript.jsonl')[:4000])}</pre>""")


def card(r: dict) -> dict:
    lk = LOOK_CELL[look(r["repo"])]
    cells = [[f"{r['passed']}/4", None, "touch-ups"], [f"{r['lines_readable']}/5", None], ["Yes", "有"] if r["audio"] else ["No", "无"], lk,
             [f"{r['minutes']} min", f"{r['minutes']} 分钟", "substantial" if r["minutes"] > 15 else "num"]]
    bits = [[f"made the 15-second test film in {r['minutes']} min", f"{r['minutes']} 分钟做出 15 秒测试片"], ["all four checks passed", "四项检查全部通过"],
            ["with sound", "带声音"] if r["audio"] else ["no sound", "没有声音"], [lk[0].lower(), lk[1]]]
    out = {"ran": True, "stars": r["stars"], "sheet": key(r["repo"]) + ".html", "cells": cells, "bits": bits}
    if r["repo"] in NOTES:
        out.update(note=NOTES[r["repo"]][0], note_zh=NOTES[r["repo"]][1])
    return out


def clip(r: dict) -> dict:
    k = key(r["repo"])
    name = "No skill" if r["repo"] == CONTROL else r["repo"].split("/")[1]
    return {"name": name, "src": f"{k}.mp4", "poster": f"{k}.jpg", "group": look(r["repo"]),
            "caption": [f"{r['minutes']} min · {'sound' if r['audio'] else 'no sound'}", f"{r['minutes']} 分钟 · {'有声音' if r['audio'] else '无声音'}"]}


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    rows = [r for r in json.loads((HERE / "results.json").read_text()) if r["ran"]]
    assert all(r["passed"] == 4 for r in rows), "a run failed a check: the page's text says every one passed"
    control = next(r for r in rows if r["repo"] == CONTROL)
    skills = sorted((r for r in rows if r["repo"] != CONTROL), key=lambda r: r["minutes"])
    for r in rows:
        publish_media(r)
        (DEST / (key(r["repo"]) + ".html")).write_text(page(r, "Control: Claude Code with no video skill" if r is control else r["repo"]))
    films_grid([control, *skills])
    n, sound = len(skills), sum(r["audio"] for r in skills)
    fast, slow = skills[0]["minutes"], skills[-1]["minutes"]
    verdict = {**VERDICT, "rule": [x.format(n=n) for x in VERDICT["rule"]]}
    write_runs(SLUG, {
        "type": "table", "date": DATE, "dir": "/best-runs/video/", "results": URL + "RESULTS.md",
        "title": ["Remotion skills and Claude Code video tools tested: the same 15-second film", "实测对比：同一条 15 秒片子"],
        "intro": [f"On {DATE} we had {n} of these skills make the same film in a throwaway sandbox, driven by Claude Code (Claude Opus 5.5): a 15-second promo for a made-up app, with five fixed lines of on-screen copy, at 1920 x 1080 and 30 frames per second, on a machine with no API keys for video, image or voice models. Claude Code with no skill made it too. Four things were checked from each file: it plays, it is the length and size asked for, every line of copy can be read in frames sampled twice a second, and the picture moves. How good a film looks is not scored. The films are below.",
                  f"{DATE} 我们让其中 {n} 个 skill 在用完即删的沙箱里由 Claude Code（Claude Opus 5.5）调用，做同一条片子：给一个虚构应用做 15 秒宣传片，五句固定的画面文案，1920 x 1080、每秒 30 帧，机器上没有任何视频、图像或语音模型的密钥。不装 skill 的 Claude Code 也做了一条。每个文件查四件事：能播放、时长和尺寸符合要求、每句文案在每秒抽两帧的画面里都读得到、画面在动。片子好不好看不打分，成片就在下面。"],
        "finding": [f"All {n} rendered a film that passed all four checks, with no line of copy missing and nothing added, and so did Claude Code with no skill, in {control['minutes']} minutes. None needed a paid model for this brief. What differs is time ({fast} to {slow} minutes), sound ({sound} of {n} added it), and the look: {len(LOOK['default'])} came out close to the no-skill film (deep teal water, waves, white centred type) and {len(LOOK['own'])} have a look of their own, by our eye.",
                    f"{n} 个全部渲染出了通过四项检查的成片，文案一句没少、也没有多加内容；不装 skill 的 Claude Code 也一样，用了 {control['minutes']} 分钟。这条需求没有一个用到付费模型。差别在耗时（{fast} 到 {slow} 分钟）、声音（{n} 个里 {sound} 个加了声音）和观感：按我们的眼睛看，{len(LOOK['default'])} 个做出来接近不装 skill 的成片（深青色水面、波浪、白字居中），{len(LOOK['own'])} 个有自己的样子。"],
        "gallery": {"width": CLIP[0], "height": CLIP[1], "groups": GROUPS, "items": [clip(control), *[clip(r) for r in skills]],
                    "note": ["The films, side by side. Press play on any of them; each is 15 seconds.", "成片并排放在这里。点任意一条播放，每条 15 秒。"]},
        "list_images": [{"src": "films.jpg", "en": "The opening line of every film; the one made with no skill is top left. The films play on the page.",
                         "zh": "每条成片的第一句画面;左上角是不装 skill 做的。成片可以在页面上播放。"}],
        "name_col": ["Skill", "Skill"],
        "columns": [["Checks passed (of 4)", "通过检查（共 4 项）"], ["Lines of copy readable (of 5)", "读得到的文案（共 5 句）"], ["Sound", "声音"],
                    ["Look, by eye", "观感（肉眼判断）"], ["Time to make", "制作耗时"]],
        "see": ["Watch it and see the frames →", "看成片和抽帧 →"], "evidence": ["The film", "成片"],
        "line_label": [f"Remotion and video skill test, {DATE}:", f"{DATE} 实测："], "control": {"sheet": key(CONTROL) + ".html"},
        "verdict": verdict, "runs": {r["repo"]: card(r) for r in skills}})
    update_method(SLUG, [
        pair(f"Rendering was not the hurdle here. All {n} skills, and Claude Code with no skill, produced a playable 15-second film of the right size with every line of copy readable and nothing added; none needed a paid model.",
             f"这次渲染不是门槛。{n} 个 skill 和不装 skill 的 Claude Code 全都做出了可播放、尺寸正确的 15 秒成片，每句文案都读得到，也没有多加内容；没有一个用到付费模型。"),
        pair(f"A skill changes the look and the time, not whether a film comes out. Time ran from {fast} to {slow} minutes; by eye, {len(LOOK['own'])} of {n} films have a look of their own and {len(LOOK['default'])} sit close to what Claude Code makes unprompted.",
             f"skill 改变的是观感和耗时，不是能不能出片。耗时从 {fast} 到 {slow} 分钟；按肉眼判断，{n} 条里 {len(LOOK['own'])} 条有自己的样子，{len(LOOK['default'])} 条接近 Claude Code 不给方向时做出来的东西。")],
        pair(f"Had {n} of the skills make the same 15-second film in a throwaway sandbox, with Claude Code and no skill as the control, and checked every file four ways. The films are in the test section above and on each card.",
             f"让其中 {n} 个 skill 在用完即删的沙箱里做同一条 15 秒片子，用不装 skill 的 Claude Code 做对照，每个文件查四项。成片在上面的实测区和每张卡片上。"),
        pair("The brief is short and simple, so it cannot separate these skills on reliability: every one passed. One run per skill; a second run would look different. The look is our judgement by eye, not a measurement, and nobody rated the films for quality. The copy was read off the frames by a model, whose frame numbers we found to be off by one in places, so we report whether a line was readable, not for how long. Editing, avatar and story skills that need footage, an account or a paid model were not in this test.",
             "这条需求又短又简单，分不出这些 skill 谁更可靠：全部通过。每个 skill 只跑一次，再跑一次画面会不同。观感是我们肉眼的判断，不是测量，也没有人给片子的质量打分。文案是模型从画面帧上读的，我们发现它报的帧号有的地方差一帧，所以只报告某句是否读得到，不报告显示了多久。需要素材、账号或付费模型的剪辑、数字人和故事类 skill 不在这次测试里。"),
        "Rendering was not the hurdle")
    print(f"{n} skills, control {control['minutes']} min, {fast}-{slow} min, sound {sound}/{n}")


if __name__ == "__main__":
    main()
