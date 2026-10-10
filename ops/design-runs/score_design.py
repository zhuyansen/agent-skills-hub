"""Score the design runs: every skill built the same landing page twice (out/, out-b/).

  python ops/design-runs/score_design.py      # measures pages not yet measured, writes results.json and RESULTS.md

Nothing here is a taste score. Three things are counted from the rendered page
(measure_page.py, in the sandbox's browser):
- seven checks a landing page should pass whatever it looks like (the brief's copy all
  there, nothing invented, one h1, the button on the first screen, no sideways scroll on
  a phone, no script errors, no outside requests but fonts);
- seven stock choices that mark the look agents fall into when left alone (purple or
  indigo accent, gradient text, Inter, emoji as icons, centred hero, glass blur, a row of
  rounded shadow cards);
- sameness: how alike the skill's two builds are, and how alike each is to the page
  Claude Code built with no skill (accent hue, main font, light or dark, first screen
  pixels). After Doshi & Hauser (Sci. Adv. 2024): help can raise each result and still
  make the results more alike.
"""
import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

HERE = Path(__file__).parent
RUNS = {"a": HERE / "out", "b": HERE / "out-b"}
CONTROL = "octocat/Hello-World"
IMAGE = "pptrun:1"
BRIEF = (HERE / "in" / "brief.md").read_text()
EXTRA_WORDS_MAX = 40          # nav labels, button repeats and a logo word are fine; a new paragraph is not
FIRST_SCREEN = 900
SENTENCE_WORDS = 4
PURPLE = (235, 320)           # hue range, indigo to magenta
HUE_SAME, PIXEL_SAME = 25, 0.82
ALLOWED_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")
STOCK_FONTS = {"inter", "system-ui", "-apple-system", "segoe ui", "roboto", "helvetica neue", "arial", "sans-serif"}
CHECKS = ["copy_complete", "nothing_added", "one_h1", "button_on_first_screen", "no_sideways_scroll", "no_errors", "self_contained"]
TELLS = ["purple_accent", "gradient_text", "inter", "emoji_icons", "centred_hero", "glass_blur", "shadow_cards"]


def words(s: str) -> list[str]:
    return re.findall(r"[a-z0-9$]+", s.lower().replace("’", "'"))


def copy_lines() -> list[str]:
    """The sentences of the brief's Copy section, without labels and markup."""
    body = BRIEF.split("## Copy")[1].split("## Requirements")[0]
    out = []
    for line in body.splitlines():
        line = re.sub(r"^\s*(\d+\.|-|#+)\s*", "", line).replace("**", "")
        line = re.sub(r"^(Headline|Subhead|Primary button):\s*", "", line).strip()
        out += [part.strip() for part in line.split(" — ") if part.strip()]
    return out


COPY = copy_lines()
COPY_WORDS = set(words(" ".join(COPY))) | {"tidepool"}


def hue(rgb: str) -> float | None:
    m = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", rgb)[:3]]
    if len(m) < 3:
        return None
    r, g, b = (v / 255 for v in m)
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn < 0.08:
        return None
    d = mx - mn
    h = ((g - b) / d) % 6 if mx == r else (b - r) / d + 2 if mx == g else (r - g) / d + 4
    return (h * 60) % 360


def luminance(rgb: str) -> float:
    m = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", rgb)[:3]] or [255, 255, 255]
    return (0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]) / 255


def measure(run: Path) -> dict | None:
    if not (run / "deliverables" / "index.html").exists():
        return None
    if not (run / "measure.json").exists():
        subprocess.run(["docker", "run", "--rm", "--entrypoint", "python3", "-v", f"{run}:/run", "-v", f"{HERE}:/tool:ro", IMAGE,
                        "/tool/measure_page.py", "/run"], capture_output=True, timeout=300)
    return json.loads((run / "measure.json").read_text()) if (run / "measure.json").exists() else None


def facts(m: dict) -> dict:
    """What one build looks like: checks, tells, and the few properties sameness compares."""
    d = m["desktop"]
    page = " ".join(words(d["text"]))
    # Sentences must be there word for word; short labels ("Pricing", "Swimmer, $3 a month") get laid out in pieces.
    missing = [c for c in COPY if len(words(c)) >= SENTENCE_WORDS and " ".join(words(c)) not in page]
    extra = [w for w in words(d["text"]) if w not in COPY_WORDS]
    button = next((b for b in d["buttons"] if "check my beach" in b["text"].lower()), None)
    outside = [u for u in m["requests"] if not any(h in u for h in ALLOWED_HOSTS)]
    font = max(d["fonts"], key=d["fonts"].get).lower() if d["fonts"] else ""
    accent_hue = hue(d["accent"] or "")
    checks = {"copy_complete": not missing, "nothing_added": len(extra) <= EXTRA_WORDS_MAX, "one_h1": d["h1"] == 1,
              "button_on_first_screen": bool(button and button["top"] < FIRST_SCREEN),
              "no_sideways_scroll": m["mobile"]["scrollWidth"] <= m["mobile"]["innerWidth"] + 1,
              "no_errors": not m["errors"], "self_contained": not outside}
    tells = {"purple_accent": d["purpleGradient"] > 0 or (accent_hue is not None and PURPLE[0] <= accent_hue <= PURPLE[1]),
             "gradient_text": d["gradientText"] > 0, "inter": font == "inter", "emoji_icons": d["emoji"] > 0,
             "centred_hero": bool(d["heroCentered"]), "glass_blur": d["blurEls"] > 0, "shadow_cards": d["shadowEls"] >= 3 and d["roundCards"] >= 3}
    return {"checks": checks, "tells": tells, "missing": missing, "extra_words": len(extra), "font": font, "stock_font": font in STOCK_FONTS,
            "accent_hue": accent_hue, "dark": luminance(d["bodyBg"]) < 0.4, "height": d["height"]}


def pixels_alike(a: Path, b: Path) -> float:
    """1.0 for identical first screens, about 0.5 for unrelated ones (small greyscale thumbnails compared)."""
    x, y = (Image.open(p).convert("L").resize((96, 60)) for p in (a / "fold.png", b / "fold.png"))
    return round(1 - ImageStat.Stat(ImageChops.difference(x, y)).mean[0] / 255, 3)


def alike(fa: dict, fb: dict, a: Path, b: Path) -> dict:
    hues = fa["accent_hue"], fb["accent_hue"]
    same_hue = hues[0] is None and hues[1] is None or (None not in hues and min(abs(hues[0] - hues[1]), 360 - abs(hues[0] - hues[1])) <= HUE_SAME)
    px = pixels_alike(a, b)
    same = {"accent": bool(same_hue), "font": fa["font"] == fb["font"], "mode": fa["dark"] == fb["dark"], "first_screen": px >= PIXEL_SAME}
    return {**same, "pixels": px, "count": sum(same.values())}


def row(c: dict, control: dict) -> dict:
    key = c["repo"].replace("/", "__")
    builds = {k: (d / key, measure(d / key)) for k, d in RUNS.items()}
    built = {k: (p, facts(m)) for k, (p, m) in builds.items() if m}
    if not built:
        meta = RUNS["a"] / key / "run.json"
        return {**c, "ran": False, "reason": json.loads(meta.read_text())["status"] if meta.exists() else "not run"}
    fs = [f for _, f in built.values()]
    out = {**c, "ran": True, "builds": len(built), "checks": round(sum(sum(f["checks"].values()) for f in fs) / len(fs), 1),
           "tells": round(sum(sum(f["tells"].values()) for f in fs) / len(fs), 1), "facts": {k: f for k, (_, f) in built.items()},
           "minutes": round(json.loads((built[min(built)][0] / "run.json").read_text())["seconds"] / 60, 1)}
    if len(built) == 2:
        out["self"] = alike(built["a"][1], built["b"][1], built["a"][0], built["b"][0])
    if control and c["repo"] != CONTROL:
        k = min(built)
        out["vs_control"] = alike(built[k][1], control["facts"], built[k][0], control["path"])
    return out


def markdown(rows: list[dict]) -> str:
    out = ["| Skill | ★ | Checks passed (of 7) | Stock choices (of 7) | Which | Two builds alike (of 4) | Like the no-skill page (of 4) | Font | Min |",
           "|---|---:|---:|---:|---|---:|---:|---|---:|"]
    for r in sorted((r for r in rows if r["ran"]), key=lambda r: (r["tells"], -r["checks"])):
        f = r["facts"][min(r["facts"])]
        which = ", ".join(t for t in TELLS if f["tells"][t]) or "-"
        out.append(f"| {r['repo']} | {r['stars']} | {r['checks']} | {r['tells']} | {which} | {(r.get('self') or {}).get('count', '-')} | "
                   f"{(r.get('vs_control') or {}).get('count', '-')} | {f['font']} | {r['minutes']} |")
    out += ["", "Not run:", ""] + [f"- {r['repo']}: {r['reason']}" for r in rows if not r["ran"]]
    return "\n".join(out) + "\n"


def main() -> None:
    cands = json.loads((HERE / "candidates.json").read_text())
    ckey = CONTROL.replace("/", "__")
    cm = measure(RUNS["a"] / ckey)
    control = {"facts": facts(cm), "path": RUNS["a"] / ckey} if cm else {}
    rows = [row({"repo": CONTROL, "kind": "control", "stars": 0, "grade": None}, control), *[row(c, control) for c in cands]]
    (HERE / "results.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    (HERE / "RESULTS.md").write_text(markdown(rows))
    print(markdown(rows))


if __name__ == "__main__":
    main()
