"""Evidence pages, pictures and page data for the image test (/best/image-generation/).

  python3 ops/image-runs/evidence.py      # after score_image.py, once summary.py --review prints nothing

Writes frontend/public/best-runs/image/ (the pictures, evidence_media.py, and <owner__repo>.html for
every run that made a picture, noindex), the "image-generation" entry of frontend/scripts/scenario-runs.json,
that page's picks and two FAQ answers in scenario-keywords.json (evidence_copy.py), and RESULTS.md here.
Text is OCR's verdict with the looks by hand (summary.text_verdicts, text_review.json); formats are
measured; the mascot set is the judge's. Which sets have a look of their own was judged by eye on
2026-11-08 (OWN_LOOK): the poster and the mascots beside the set Claude Code made with no skill.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import evidence_copy as copy  # noqa: E402
import evidence_media as media  # noqa: E402
import evidence_page as pagedata  # noqa: E402
from runs_common import key, write_runs  # noqa: E402
from summary import row, shape  # noqa: E402

SLUG, DATE, CONTROL = "image-generation", "2026-11-08", "control"
OUT, DEST = HERE / "out", copy.DEST
PORTRAIT_ONLY = "liyue-aigc/female-portrait-director"
TRUNCATED = {"dreiachse-cyber/image-cockpit-for-codex-work", "dacnay816y62-hub/fantasy-dongfang-jianyuehai"}
GROUP_ORDER = ("clean", "broke", "partial", "special")
# By eye, 2026-11-08: sets whose poster or mascots look unlike the no-skill set (a warm photo of a loaf,
# a stock cute bun, glossy 3D or flat). The rest are "close to the no-skill set".
OWN_LOOK = {
    "BIAsia/voxel-icon", "CaliCastle/skills", "NimaChu/xhs-imagen", "TaiT-tt/tait-crt-interface-skill", "aehyok/generate-article-cover-image",
    "chiyolyn/bold-contour-ink-portrait", "chujianyun/awesome-gpt-image2-ppt-skills", "dacnay816y62-hub/fantasy-qiqiguaiguai-skill",
    "dacnay816y62-hub/photo-revival", "dacnay816y62-hub/regional-culture-poster", "helloianneo/ian-xiaohei-illustrations",
    "helloianneo/ian-xiaohei-scenes", "james20141606/sci-figure-workflow", "moonlin1213/muted-zine-poster-v01", "nevertoday/xxd-panel-028",
    "ningzimu/codex-ppt-skill", "s1dashu/ip-as-logo-skill", "tmchow/illo-skill", "yanliudesign/mono-color-skill"}


def candidates() -> list[str]:
    return [c["repo"] for c in json.loads((HERE / "candidates.json").read_text()) if c["repo"] not in TRUNCATED]


def load(repo: str) -> dict:
    """The run's summary row, the shapes of its pictures and its score file."""
    run = OUT / key(repo)
    return {**row(run), "fmt": shape(run), "score": json.loads((run / "score.json").read_text()), "dir": run}


def clean(r: dict) -> bool:
    lines = r["poster_lines"] or []
    return (r["files"] == 6 and lines.count("ok") == 6 and r["bag"] == "ok" and r["format_ok"] == 6 and not r["poster_other_text"]
            and not r["mascot_text"] and (r["same_character"] or 0) >= 5 and r["poses"] == 4 and bool(r["hat_scarf"]))


def group_of(repo: str, r: dict) -> str | None:
    """clean / broke / partial / special, or None for a run that made no picture."""
    if repo == PORTRAIT_ONLY:
        return "special"
    if r["files"] == 6:
        return "clean" if clean(r) else "broke"
    return "partial" if r["files"] else None


def publish(repo: str, r: dict) -> dict:
    """Web copies, the table strip and (for picks and the control) the bigger strip; returns their paths and sizes."""
    k, folder = key(repo), r["dir"] / "deliverables"
    media.web_copies(folder, DEST, k)
    stems = ("portrait",) if repo == PORTRAIT_ONLY else media.FILES
    out = {"strip": media.strip(folder, DEST / "strips" / f"{k}.webp", stems, media.STRIP_HEIGHT, media.STRIP_MAX_WIDTH)}
    if repo in copy.PICK_LINES or repo == CONTROL:
        out["pick"] = media.strip(folder, DEST / "picks" / f"{k}.webp", media.PICK_FILES, media.PICK_HEIGHT)
    if repo == PORTRAIT_ONLY:
        media.fit_long_side(media.load(folder / "portrait.png"), 680).save(DEST / f"{k}-portrait.webp", quality=media.WEBP_QUALITY)
    return {name: {"src": f"{name}s/{k}.webp", "w": size[0], "h": size[1]} for name, size in out.items() if size}


def entry(repo: str, r: dict, g: str, stars: dict, pics: dict) -> dict:
    look = "own" if repo in OWN_LOOK else "close"
    e = {"ran": True, "stars": stars.get(repo) or 0, "sheet": key(repo) + ".html", "group": g, "look": look,
         "cells": copy.cells(r, g, look), "bits": copy.bits(r, g, look), **pics}
    if repo in copy.NOTES:
        e.update(note=copy.NOTES[repo][0], note_zh=copy.NOTES[repo][1])
    if copy.issues(r, g):
        e["issues"] = copy.issues(r, g)
    return e


def not_run_entries(stars: dict) -> dict:
    """The runs that made no picture, by why (no_output.json), each kind together."""
    out = {}
    for kind, cat in ((k, v) for k, v in json.loads((HERE / "no_output.json").read_text()).items() if not k.startswith("_")):
        for repo, (en, zh) in sorted(cat["repos"].items(), key=lambda kv: kv[0].lower()):
            out[repo] = {"ran": False, "stars": stars.get(repo) or 0, "kind": kind, "name": repo,   # "skills", "mcp": the owner says whose
                         "reason": f"{cat['label'][0]}: {en}.", "reason_zh": f"{cat['label'][1]}：{zh}。"}
    return out


def collect(stars: dict) -> tuple[dict, dict, list]:
    """Every run: published, with its page; the control; and the rows for the counts."""
    runs, rows = {}, []
    for repo in candidates():
        r = load(repo)
        g = group_of(repo, r)
        if g is None:
            continue
        pics = publish(repo, r)
        (DEST / f"{key(repo)}.html").write_text(copy.page(repo, r, g, repo in OWN_LOOK))
        runs[repo] = entry(repo, r, g, stars, pics)
        rows.append({**r, "repo": repo, "group": g, "own": repo in OWN_LOOK})
    control = load(CONTROL)
    (DEST / "control.html").write_text(copy.page(CONTROL, control, "clean", False))
    return runs, {**control, "pics": publish(CONTROL, control)}, rows


def ordered(runs: dict, rows: list) -> dict:
    """By result, then a look of its own first, then time."""
    minutes = {r["repo"]: r["minutes"] for r in rows}
    by = lambda kv: (GROUP_ORDER.index(kv[1]["group"]), kv[1]["look"] != "own", minutes[kv[0]])  # noqa: E731
    return dict(sorted(runs.items(), key=by))


def mosaic(rows: list, control: dict) -> dict:
    posters = [media.find(control["dir"] / "deliverables", "poster")]
    posters += [p for p in (media.find(r["dir"] / "deliverables", "poster") for r in rows) if p]
    w, h = media.poster_mosaic(posters, DEST / "posters.jpg", "No skill")
    return {"src": "posters.jpg", "w": w, "h": h, "count": len(posters)}


def main() -> None:
    for sub in ("strips", "picks", "models"):
        (DEST / sub).mkdir(parents=True, exist_ok=True)
    stars = json.loads((HERE / "stars.json").read_text())
    runs, control, rows = collect(stars)
    assert not any("review" in (r["poster_lines"] or []) or r["bag"] == "review" for r in rows), "text waits for a look: summary.py --review"
    not_run, runs = not_run_entries(stars), ordered(runs, rows)
    counts = pagedata.counts(rows, control, not_run)
    models = pagedata.models_block(HERE / "models")
    write_runs(SLUG, pagedata.page_entry(counts, control, runs, not_run, models, mosaic(rows, control)))
    pagedata.update_keywords(SLUG, counts, rows)
    (HERE / "RESULTS.md").write_text(pagedata.results_md(counts, runs, not_run, models))
    print(json.dumps({k: v for k, v in counts.items() if not isinstance(v, (dict, list))}))


if __name__ == "__main__":
    main()
