"""Score the design runs: every skill built the same landing page twice (out/, out-b/).

  python ops/design-runs/score_design.py      # measures pages not yet measured, writes results.json and RESULTS.md

Nothing here is a taste score. Three things are counted from the rendered page
(measure_page.py, in the sandbox's browser):
- seven checks a landing page should pass whatever it looks like (the brief's copy all
  there, nothing invented, one h1, the button on the first screen, no sideways scroll on
  a phone, no script errors, no outside requests but fonts);
- four stock choices of the older "AI look" (purple or indigo accent, gradient text,
  emoji as icons, centred hero), kept as a count because none of the 22 builds made one;
- sameness, on four things read from the page: headline font, body font, accent colour
  family, background family. How many of the four a build shares with the two pages
  Claude Code built with no skill (the default look, measured rather than assumed), and
  how many the skill's own two builds share. After Doshi & Hauser (Sci. Adv. 2024):
  help can raise each result and still make the results more alike.
"""
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
RUNS = {"a": HERE / "out", "b": HERE / "out-b"}
CONTROL = "octocat/Hello-World"
IMAGE = "pptrun:1"
BRIEF = (HERE / "in" / "brief.md").read_text()
EXTRA_WORDS_MAX = 40          # nav labels, button repeats and a logo word are fine; a new paragraph is not
FIRST_SCREEN = 900
SENTENCE_WORDS = 5
PURPLE = (232, 320)           # hue range, indigo to magenta
DARK, PALE, WARM = 0.22, 0.85, 6   # lightness below which a colour reads as ink, above which as paper; red over blue for "warm"
ALLOWED_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")
STOCK_FONTS = {"inter", "system-ui", "-apple-system", "segoe ui", "roboto", "helvetica neue", "arial", "sans-serif"}
# Pictures used as icons. The browser's own emoji class also counts ©, ™ and ✓, which are in the brief or are plain type.
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u26FF]")
CHECKS = ["copy_complete", "nothing_added", "one_h1", "button_on_first_screen", "no_sideways_scroll", "no_errors", "self_contained"]
TELLS = ["purple_accent", "gradient_text", "emoji_icons", "centred_hero"]
SIGNATURE = ["headline_font", "body_font", "accent", "background"]


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
    checks = {"copy_complete": not missing, "nothing_added": len(extra) <= EXTRA_WORDS_MAX, "one_h1": d["h1"] == 1,
              "button_on_first_screen": bool(button and button["top"] < FIRST_SCREEN),
              "no_sideways_scroll": m["mobile"]["scrollWidth"] <= m["mobile"]["innerWidth"] + 1,
              "no_errors": not m["errors"], "self_contained": not outside}
    accent_hue = hue(d["accent"] or "")
    purple = accent_hue is not None and PURPLE[0] <= accent_hue <= PURPLE[1] and DARK < luminance(d["accent"]) < PALE
    tells = {"purple_accent": d["purpleGradient"] > 0 or purple, "gradient_text": d["gradientText"] > 0,
             "emoji_icons": bool(EMOJI.search(d["text"])), "centred_hero": bool(d["heroCentered"])}
    sig = {"headline_font": (d.get("h1Font") or font).lower(), "body_font": font, "accent": family(d["accent"] or ""), "background": family(d["bodyBg"])}
    return {"checks": checks, "tells": tells, "missing": missing, "extra_words": len(extra), "signature": sig, "accent_rgb": d["accent"], "background_rgb": d["bodyBg"]}


def family(rgb: str) -> str:
    """A colour as a reader would name it: ink, warm paper, cool paper, or its hue in 30-degree steps."""
    m = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", rgb)[:3]] or [255, 255, 255]
    lum, h = luminance(rgb), hue(rgb)
    if lum < DARK:
        return "ink"
    if lum > PALE:
        return "warm paper" if m[0] - m[2] > WARM else "cool paper" if m[2] - m[0] > WARM else "neutral paper"
    return "grey" if h is None else HUES[int(((h + 15) % 360) // 30)]


HUES = ["red", "orange", "yellow", "lime", "green", "teal-green", "teal", "blue", "indigo", "violet", "magenta", "pink"]


def row(c: dict, default: list[dict]) -> dict:
    key = c["repo"].replace("/", "__")
    built = {k: facts(m) for k, d in RUNS.items() if (m := measure(d / key))}
    if not built:
        meta = RUNS["a"] / key / "run.json"
        return {**c, "ran": False, "reason": json.loads(meta.read_text())["status"] if meta.exists() else "not run"}
    fs = list(built.values())
    like = [sum(f["signature"][k] in {d["signature"][k] for d in default} for k in SIGNATURE) for f in fs]
    out = {**c, "ran": True, "builds": len(built), "checks": round(sum(sum(f["checks"].values()) for f in fs) / len(fs), 1),
           "tells": sum(sum(f["tells"].values()) for f in fs), "like_default": round(sum(like) / len(like), 1), "facts": built,
           "headline_fonts": sorted({f["signature"]["headline_font"] for f in fs}),
           "failed": sorted({k for f in fs for k, ok in f["checks"].items() if not ok}),
           "minutes": round(json.loads((RUNS["a"] / key / "run.json").read_text())["seconds"] / 60, 1)}
    if len(built) == 2:
        out["self_alike"] = sum(built["a"]["signature"][k] == built["b"]["signature"][k] for k in SIGNATURE)
    return out


def markdown(rows: list[dict]) -> str:
    out = ["| Skill | ★ | Shares with the no-skill page (of 4) | Its two builds share (of 4) | Checks passed (of 7) | Failed | Headline font | Min |",
           "|---|---:|---:|---:|---:|---|---|---:|"]
    for r in sorted((r for r in rows if r["ran"]), key=lambda r: (r["repo"] != CONTROL, r["like_default"], -r["checks"])):
        out.append(f"| {r['repo']} | {r['stars']} | {r['like_default']} | {r.get('self_alike', '-')} | {r['checks']} | {', '.join(r['failed']) or '-'} | "
                   f"{' / '.join(r['headline_fonts'])} | {r['minutes']} |")
    out += ["", f"Older stock choices ({', '.join(TELLS)}) across all builds: {sum(r['tells'] for r in rows if r['ran'])}.", "",
            "Not run:", ""] + [f"- {r['repo']}: {r['reason']}" for r in rows if not r["ran"]]
    return "\n".join(out) + "\n"


def main() -> None:
    cands = json.loads((HERE / "candidates.json").read_text())
    ckey = CONTROL.replace("/", "__")
    default = [facts(m) for d in RUNS.values() if (m := measure(d / ckey))]   # the no-skill page, both builds
    rows = [row({"repo": CONTROL, "kind": "control", "stars": 0, "grade": None}, default), *[row(c, default) for c in cands]]
    (HERE / "results.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    (HERE / "RESULTS.md").write_text(markdown(rows))
    print(markdown(rows))


if __name__ == "__main__":
    main()
