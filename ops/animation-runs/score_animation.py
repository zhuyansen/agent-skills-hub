"""Score finished animation runs (ops/animation-runs/<kind>/out/<owner__repo>/).

  python3 ops/animation-runs/score_animation.py [kind ...]      # default: every kind, runs without score.json
  python3 ops/animation-runs/score_animation.py --again [kind ...]   # score every run again

Counted here, from the files: preview.mp4's size, frame rate and length (ffprobe); how much of it holds still
(frames that barely differ from the one before, sampled at 10 per second); whether it ends where it starts (the
lottie and rig briefs ask for a loop); the deliverable the brief names and the checks a file can answer (a Lottie
file's fields, the sprite sheets' sizes and transparency, reduced motion in the web page's code); minutes and the
cost at API prices (ops/3d-runs/score_3d.usage). Judged by gpt-6-astra through FlatRouter, one call per run, on a
sheet of 8 frames from preview.mp4 (and for sprites, the two sheets themselves), each item of the brief answered
separately so a miss is named.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "image-runs"))
sys.path.insert(0, str(HERE.parent / "3d-runs"))
from score_image import ask, env, last_words  # noqa: E402
from score_3d import usage  # noqa: E402

KINDS = ["web", "lottie", "sprite", "rig", "diagram", "art"]
SHEET_FRAMES = 8
SAMPLE_FPS = 10
STILL = 0.4          # mean absolute difference (0-255) under which a sampled frame counts as held
LOOP_MATCH = 6.0     # first vs last frame: under this the animation ends where it starts
SPEC = {   # what preview.mp4 should be: width, height, seconds
    "web": (1280, 720, 10), "lottie": (512, 512, 4), "sprite": (1024, 512, 4),
    "rig": (1080, 1080, 3), "diagram": (1920, 1080, 12), "art": (1920, 1080, 12),
}
COMMON = (" Answer each item separately from what the frames show. Also return \"glitches\": [short: things cut off, "
          "overlapping text, broken shapes, empty frames], \"follows_brief\": 1-5, \"looks\": 1-5 (how good the animation "
          "looks, as a designer would judge it), \"note\": short.")
QUESTIONS = {
    "web": ("These are 8 frames, in order, from a 10-second recording of a bakery landing page loading and then scrolling. "
            "The brief: the Morning Loaf logo draws itself in; the headline \"Fresh at 7 a.m.\" comes in word by word; three "
            "product cards \"Sourdough loaf\", \"Butter croissant\", \"Cinnamon bun\" rise in one after another; a button "
            "\"Order for tomorrow\"; further down a section \"Baked overnight\" with a croissant drawing that turns as the page "
            "scrolls. Return {\"logo_draws_in\": bool, \"headline_word_by_word\": bool, \"headline_text_right\": bool, "
            "\"three_cards_staggered\": bool, \"card_names_right\": bool, \"button_shown\": bool, \"scroll_section_shown\": "
            "bool, \"croissant_turns_with_scroll\": bool}."),
    "lottie": ("These are 8 frames, in order, from 4 seconds (a 2-second loop played twice) of an animated bakery logo: a "
               "loaf, three steam lines and the words \"Morning Loaf\". The brief: the loaf drops in and squashes a little as "
               "it lands; the three steam lines rise and fade one after another; the words fade in; it keeps the logo's shapes "
               "and colours. Return {\"loaf_drops_and_squashes\": bool, \"steam_rises_in_turn\": bool, \"words_fade_in\": bool, "
               "\"logo_kept\": bool}."),
    "sprite": ("The first image is the reference mascot. The next two are sprite sheets: a walk (8 frames of 128x128 in a "
               "row) and an idle (4 frames). The last is 8 frames from a recording of the walk playing. The brief: pixel-art "
               "style; the walk is a full cycle to the right; the idle is standing and breathing; the mascot looks the same in "
               "every frame (size, colours, baker's hat, face) and stands on the same ground line. Return {\"pixel_art\": bool, "
               "\"is_the_mascot\": bool, \"walk_cycle_reads\": bool, \"faces_right\": bool, \"idle_breathes\": bool, "
               "\"consistent_across_frames\": bool, \"same_ground_line\": bool}."),
    "rig": ("The first image is a bread mascot. The second is 8 frames, in order, from a 3-second animation of it. The "
            "brief: its right arm (on the viewer's right) rises and waves twice; the body bobs gently; the eyes blink once; it "
            "ends back in the starting pose; it keeps the mascot's look. Return {\"is_the_mascot\": bool, \"right_arm_waves\": "
            "bool, \"body_bobs\": bool, \"blink_seen\": bool, \"ends_in_start_pose\": bool}."),
    "diagram": ("These are 8 frames, in order, from a 12-second animated diagram. The brief: Customer -> Website -> Payment "
                "(Stripe) -> Order queue -> Oven (bakes at 4 a.m.) -> Courier -> Customer, the steps appearing in this order "
                "with a dot travelling along each arrow; from Payment a second path to \"Email: retry payment\" and back to "
                "Payment; every label readable. Return {\"steps_present\": int (of the 7 boxes in the main path), "
                "\"order_right\": bool, \"dots_travel\": bool, \"retry_branch\": bool, \"retry_loops_back\": bool, "
                "\"labels_readable\": bool}."),
    "art": ("These are 8 frames, in order, from a 12-second explainer. The brief: a ball of dough grows from 1x to 2x to 4x "
            "to 8x over three hours; a clock shows the hours passing (0 h to 3 h); a curve plots size against time as it "
            "grows; it ends on the line \"Size doubles every hour\". Return {\"dough_grows_doubling\": bool, \"clock_shows_hours\": "
            "bool, \"curve_plots_growth\": bool, \"curve_is_exponential\": bool, \"end_line_right\": bool}."),
}


def probe(mp4: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,codec_name,r_frame_rate:format=duration", "-of", "json", str(mp4)],
                         capture_output=True, text=True).stdout
    j = json.loads(out or "{}")
    s = (j.get("streams") or [{}])[0]
    num, _, den = (s.get("r_frame_rate") or "0/1").partition("/")
    return {"width": s.get("width"), "height": s.get("height"), "codec": s.get("codec_name"),
            "fps": round(int(num) / int(den or 1), 2) if num else None,
            "seconds": round(float((j.get("format") or {}).get("duration") or 0), 2)}


def frames(mp4: Path, tmp: Path) -> list[Path]:
    """The recording sampled at SAMPLE_FPS, scaled to 480 px wide."""
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vf", f"fps={SAMPLE_FPS},scale=480:-2", str(tmp / "f%04d.png")],
                   check=True)
    return sorted(tmp.glob("f*.png"))


def motion(paths: list[Path]) -> dict:
    import numpy as np
    from PIL import Image
    arr = [np.asarray(Image.open(p).convert("L"), dtype=np.float32) for p in paths]
    diffs = [float(np.abs(a - b).mean()) for a, b in zip(arr, arr[1:])]
    return {"held_share": round(sum(d < STILL for d in diffs) / len(diffs), 2) if diffs else None,
            "first_last_diff": round(float(np.abs(arr[0] - arr[-1]).mean()), 2) if len(arr) > 1 else None}


def sheet(paths: list[Path], dest: Path) -> Path:
    """SHEET_FRAMES frames evenly spread over the recording, in a 4x2 grid with their times."""
    from PIL import Image, ImageDraw
    pick = [paths[round(i * (len(paths) - 1) / (SHEET_FRAMES - 1))] for i in range(SHEET_FRAMES)]
    ims = [Image.open(p).convert("RGB") for p in pick]
    w, h = ims[0].size
    out = Image.new("RGB", (w * 4, h * 2), "white")
    for i, (im, p) in enumerate(zip(ims, pick)):
        out.paste(im.resize((w, h)), ((i % 4) * w, (i // 4) * h))
        t = (int(p.stem[1:]) - 1) / SAMPLE_FPS
        ImageDraw.Draw(out).text(((i % 4) * w + 6, (i // 4) * h + 4), f"{i + 1} · {t:.1f}s", fill=(220, 0, 0))
    out.save(dest)
    return dest


def file_checks(kind: str, d: Path) -> dict:
    """What the deliverable's own file can answer."""
    c: dict = {}
    if kind in ("web", "diagram"):
        page = d / "index.html"
        c["page"] = page.exists()
        if page.exists():
            src = page.read_text(errors="ignore")
            if kind == "web":
                c["reduced_motion"] = "prefers-reduced-motion" in src
                c["scroll_linked"] = any(k in src for k in ("ScrollTrigger", "scroll-timeline", "animation-timeline",
                                                              "scrollY", "pageYOffset", "useScroll", "onscroll", "addEventListener('scroll'",
                                                              'addEventListener("scroll"'))
    elif kind == "lottie":
        lj, sv = d / "logo.json", d / "logo.svg"
        c["format"] = "lottie" if lj.exists() else ("svg" if sv.exists() else None)
        if lj.exists():
            try:
                j = json.loads(lj.read_text())
                c["lottie_valid"] = all(k in j for k in ("v", "fr", "ip", "op", "w", "h", "layers"))
                c["lottie_size"] = [j.get("w"), j.get("h")]
                c["lottie_seconds"] = round((j.get("op", 0) - j.get("ip", 0)) / (j.get("fr") or 1), 2)
            except ValueError:
                c["lottie_valid"] = False
    elif kind == "sprite":
        from PIL import Image
        for name, want in (("walk", (1024, 128)), ("idle", (512, 128))):
            p = d / f"{name}.png"
            if not p.exists():
                c[name] = None
                continue
            with Image.open(p) as im:
                a = im.convert("RGBA").getchannel("A")
                c[name] = {"size": list(im.size), "size_right": tuple(im.size) == want,
                           "transparent": a.getextrema()[0] == 0}
    c["files"] = sorted(str(p.relative_to(d)) for p in d.rglob("*") if p.is_file() and "node_modules" not in p.parts)[:40]
    return c


def score(kind: str, run: Path, e: dict) -> dict:
    d = run / "deliverables"
    mp4 = d / "preview.mp4"
    r = {"kind": kind, "run": json.loads((run / "run.json").read_text()), "usage": usage(run),
         "last_words": last_words(run), "checks": file_checks(kind, d) if d.exists() else {}, "preview": mp4.exists()}
    if mp4.exists():
        r["video"] = probe(mp4)
        w, h, s = SPEC[kind]
        v = r["video"]
        r["video"]["spec_right"] = (v["width"], v["height"]) == (w, h) and abs(v["seconds"] - s) <= 0.5
        with tempfile.TemporaryDirectory() as t:
            fs = frames(mp4, Path(t))
            if fs:
                r["motion"] = motion(fs)
                img = sheet(fs, run / "sheet.png")
                refs = {"sprite": [HERE / "_shared/mascot.png", d / "walk.png", d / "idle.png"],
                        "rig": [HERE / "_shared/mascot.png"]}.get(kind, [])
                r["judge"] = ask(e, QUESTIONS[kind] + COMMON, [p for p in refs if p.exists()] + [img])
    (run / "score.json").write_text(json.dumps(r, indent=1, ensure_ascii=False))
    return r


def main() -> None:
    e = env()
    again = "--again" in sys.argv
    kinds = [a for a in sys.argv[1:] if a in KINDS] or KINDS
    for kind in kinds:
        out = HERE / kind / "out"
        if not out.exists():
            continue
        for run in sorted(p for p in out.iterdir() if (p / "run.json").exists()):
            if (run / "score.json").exists() and not again:
                continue
            try:
                r = score(kind, run, e)
            except Exception as err:   # a judge timeout must not leave the rest unscored
                print(kind, run.name, "not scored:", repr(err)[:300], flush=True)
                continue
            j = r.get("judge", {})
            print(kind, run.name, r["run"]["status"], r.get("video"), r.get("motion"), j.get("follows_brief"),
                  j.get("looks"), r["usage"], flush=True)


if __name__ == "__main__":
    main()
