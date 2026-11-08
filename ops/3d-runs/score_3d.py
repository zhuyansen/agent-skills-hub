"""Score finished 3D runs (ops/3d-runs/out/<owner__repo>/): what the judge sees in the render, and what is counted.

  python3 ops/3d-runs/score_3d.py [owner/repo ...]     # default: every run without score.json
  python3 ops/3d-runs/score_3d.py --usage [owner/repo ...]   # minutes, turns and cost again, judge kept

Counted here: the render's size, the scene files written, minutes, the agent's turns and cost (the
transcript's result lines: what the run would cost at API prices), and its last words. The sign's text
is decided by OCR (ops/image-runs/text_check.py): the judge reads what it expects. Judged by
gpt-6-astra through FlatRouter, one call per render, each item of the brief answered separately so a
miss is named: the wooden counter, the round loaf, the wicker basket and how many croissants are in
it, the hanging sign, light from the left, the view from slightly above at three-quarters.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "image-runs"))
from score_image import ask, env, last_words  # noqa: E402 (the judge call and the agent's last words)
from text_check import check  # noqa: E402 (OCR: the literal text check)

OUT = HERE / "out"
SIZE = (1600, 1200)
SIGN = "Morning Loaf"
SCENE_EXT = (".blend", ".scad", ".html", ".glb", ".gltf", ".py", ".stl", ".step", ".obj")
MS_PER_MINUTE = 60_000
SECONDS_PER_MINUTE = 60
SCENE_Q = ("This should be a render of a small 3D scene for a bakery called Morning Loaf: a wooden shop counter; on "
           "the counter a round loaf of bread and a wicker basket holding three croissants; behind the counter a "
           "hanging sign that reads \"Morning Loaf\"; warm morning light from the left (shadows fall to the right); "
           "seen from slightly above, at three-quarters (the counter at an angle, not straight on). Answer each item "
           "separately. Return {\"counter_wooden\": bool, \"loaf_round_on_counter\": bool, \"basket_wicker_on_counter\": "
           "bool, \"croissants_in_basket\": int (0 if none or unclear), \"sign_hanging_behind\": bool, \"sign_read\": "
           "text, \"light_from_left\": bool, \"view_above_three_quarter\": bool, \"glitches\": [short: objects floating, "
           "passing through each other, cut off or missing], \"follows_brief\": 1-5, \"looks\": 1-5, \"note\": short}. ")


def render_of(folder: Path) -> Path | None:
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (folder / f"render{ext}").exists():
            return folder / f"render{ext}"
    return None


def scene_files(folder: Path) -> list[str]:
    """The scene in the tool's own format (the brief asks for one next to the render): files in the output folder,
    or a project folder one level down (lhlGitHub saved a whole Vite project, morning-loaf/index.html)."""
    if not folder.exists():
        return []
    top = sorted(p.name for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SCENE_EXT)
    if top:
        return top
    return sorted(f"{d.name}/{p.name}" for d in folder.iterdir() if d.is_dir() and d.name != "node_modules"
                  for p in d.iterdir() if p.is_file() and p.suffix.lower() in SCENE_EXT)


def results(run: Path) -> list[dict]:
    """The transcript's result lines: one per stretch of work (a session woken by its own background
    jobs, e.g. a long download it watches, writes one each time it goes idle)."""
    log = run / "transcript.jsonl"
    rows = []
    for line in (log.read_text(errors="ignore").splitlines() if log.exists() else []):
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "result":
            rows.append(ev)
    return rows


def usage(run: Path) -> dict:
    """Minutes (the whole run, installing the tool included, as on the other test pages), turns, and the
    cost at API prices. total_cost_usd is the session's running total, so the last stretch carries it."""
    rows, meta = results(run), json.loads((run / "run.json").read_text())
    return {"minutes": round(meta["seconds"] / SECONDS_PER_MINUTE, 1), "turns": sum(r.get("num_turns") or 0 for r in rows),
            "agent_minutes": round(sum(r.get("duration_ms") or 0 for r in rows) / MS_PER_MINUTE, 1),
            "cost": round(max((r.get("total_cost_usd") or 0 for r in rows), default=0), 2)}


def size_of(render: Path) -> list[int]:
    from PIL import Image   # only needed here
    with Image.open(render) as im:
        return list(im.size)


def score(run: Path, e: dict) -> dict:
    folder = run / "deliverables"
    render = render_of(folder)
    result = {"run": json.loads((run / "run.json").read_text()), "render": bool(render),
              "size": size_of(render) if render else None, "scene": scene_files(folder),
              "usage": usage(run), "last_words": last_words(run)}
    if render:
        c = check(render, (SIGN,))
        result["ocr"] = {"sign": c["found"][0], "distance": c["distance"][0]}
        result["judge"] = ask(e, SCENE_Q, [render])
    (run / "score.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    return result


def refresh_usage(runs: list[Path]) -> None:
    """The counted parts again (minutes, cost, scene files); the judge's answers and the OCR are kept."""
    for run in runs:
        s = json.loads((run / "score.json").read_text())
        s["usage"], s["scene"] = usage(run), scene_files(run / "deliverables")
        (run / "score.json").write_text(json.dumps(s, indent=1, ensure_ascii=False))
        print(run.name, s["usage"], flush=True)


def main() -> None:
    e, names = env(), [a.replace("/", "__") for a in sys.argv[1:] if not a.startswith("--")]
    if "--usage" in sys.argv:   # the counted part again (no judge call), for runs already scored
        refresh_usage([OUT / n for n in names] or sorted(p.parent for p in OUT.glob("*/score.json")))
        return
    runs = [OUT / n for n in names] if names else sorted(
        p for p in OUT.iterdir() if (p / "run.json").exists() and not (p / "score.json").exists())
    for run in runs:
        try:
            r = score(run, e)
        except Exception as err:   # a judge timeout must not leave the rest unscored
            print(run.name, "not scored:", repr(err)[:300], flush=True)
            continue
        j = r.get("judge", {})
        print(run.name, r["run"]["status"], r["size"], r.get("ocr"), j.get("croissants_in_basket"),
              j.get("follows_brief"), j.get("looks"), r["usage"], flush=True)


if __name__ == "__main__":
    main()
