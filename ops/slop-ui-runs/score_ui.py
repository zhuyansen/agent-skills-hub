"""Score the UI de-slop runs (ops/slop-ui-runs/out/<owner__repo>/): the page each tool returned, beside the AI-looking
page it was given (in/input/index.html, measured once into before/).

  python3 ops/slop-ui-runs/score_ui.py                 # every finished run without score.json
  python3 ops/slop-ui-runs/score_ui.py owner/repo ...  # these again

Measured in the sandbox's browser (measure_ui.py): the AI tells the page still shows (purple gradients, gradient text,
frosted-glass blur, blurred colour blobs, coloured glows, emoji), whether the headline is centred and set in a stock
font, whether the phone layout scrolls sideways, and the page's text, from which the product's facts are checked and
the stock marketing words counted. A vision judge (gpt-6-astra through FlatRouter, FLATROUTER_* in ~/.claude/.env)
sees the first screen before and after and rates how designed the new one looks; it is a second opinion, not the score.
"""
import base64
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT, BEFORE = HERE / "out", HERE / "before"
IMAGE = "pptrun:1"
FACTS = {"name": r"Ledgerly", "price": r"\$\s?12(?!\d)", "trial": r"14[-\s]?day",
         "no card": r"no (credit )?card|without (a )?(credit )?card|card (isn.t|is not|not) (needed|required)|no card needed",
         "a minute": r"(under|less than|within|in) (a|one) minute|60 seconds", "reminders": r"reminder", "accountant": r"accountant",
         "Maya Okafor": r"Maya Okafor", "illustrator": r"illustrator", "Lisbon": r"Lisbon", "three weeks": r"three weeks|3 weeks"}
BUZZWORDS = ("supercharge", "unlock", "seamless", "elevate", "cutting-edge", "revolutioni", "game-changer", "game changer",
             "effortless", "transform", "powerful", "next-level", "ai-powered", "ai-driven", "lightning")
STOCK_FONTS = {"inter", "system-ui", "-apple-system", "segoe ui", "roboto", "helvetica neue", "arial", "sans-serif"}
TELLS = ("purpleGradient", "gradientText", "blurEls", "blurBlobs", "glowEls", "emoji")
FONT_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com", "use.typekit.net", "fonts.bunny.net", "rsms.me", "api.fontshare.com", "cdn.fontshare.com")
JUDGE_Q = ("Image 1 is a landing page that looks AI-generated. Image 2 is the same page after a redesign. Judge only image 2. "
           "Rate how much it looks designed by a person, with its own character, from 1 (still looks AI-generated: purple or "
           "neon gradients, glows, frosted glass, emoji icons, a generic centred hero and three cards) to 5 (looks deliberately "
           "designed). Name the AI-generated tells you still see in image 2, if any. Be strict; do not reward change for its own "
           "sake. Reply with JSON only: {\"designed\": 1-5, \"tells_left\": [short strings], \"note\": short}.")


def env() -> dict:
    vals = {}
    for line in (Path.home() / ".claude/.env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip().strip('"')
    return vals


def measure(folder: Path) -> dict | None:
    """measure_ui.py on folder/index.html in the sandbox's browser; its measure.json, or None."""
    subprocess.run(["docker", "run", "--rm", "--entrypoint", "python3", "-v", f"{folder}:/run", "-v", f"{HERE}:/tool:ro", IMAGE,
                    "/tool/measure_ui.py", "/run"], capture_output=True, timeout=300)
    path = folder / "measure.json"
    return json.loads(path.read_text()) if path.exists() else None


def page_facts(m: dict) -> dict:
    d, text = m["desktop"], m["desktop"]["text"]
    lower = text.lower()
    return {"tells": {t: d[t] for t in TELLS}, "hero_centred": d["heroCentered"], "h1_font": d["h1Font"],
            "stock_font": (d["h1Font"] or "").lower() in STOCK_FONTS, "buzzwords": sum(lower.count(w) for w in BUZZWORDS),
            "facts": {k: bool(re.search(v, text, re.I)) for k, v in FACTS.items()},
            "sideways": m["mobile"]["scrollWidth"] > m["mobile"]["innerWidth"] + 1, "errors": m["errors"][:5],
            "outside": sorted({u.split("/")[2] for u in m["requests"] if u.startswith("http") and u.split("/")[2] not in FONT_HOSTS})}


LOCAL_REF = re.compile(r"""<(?:link|script|img|source)\b[^>]*?(?:href|src)=["']([^"'#?]+)""", re.I)


def local_files(page: Path) -> list[str]:
    """Files beside index.html that the page loads: the brief asked for one self-contained file."""
    refs = {r for r in LOCAL_REF.findall(page.read_text(errors="ignore")) if not re.match(r"(https?:|data:|//|mailto:)", r)}
    return sorted(r for r in refs if (page.parent / r).exists())


def ask(e: dict, before: Path, after: Path) -> dict:
    uri = lambda p: "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()  # noqa: E731
    content = [{"type": "text", "text": JUDGE_Q}, {"type": "image_url", "image_url": {"url": uri(before)}},
               {"type": "image_url", "image_url": {"url": uri(after)}}]
    body = {"model": e.get("FLATROUTER_MODEL", "gpt-6-astra"), "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_object"}, "temperature": 0}
    req = urllib.request.Request(e["FLATROUTER_BASE_URL"] + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + e["FLATROUTER_API_KEY"], "Content-Type": "application/json"})
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=300) as r:
        return json.loads(json.load(r)["choices"][0]["message"]["content"])


def score(run: Path, e: dict) -> dict:
    meta = json.loads((run / "run.json").read_text())
    page = run / "deliverables" / "index.html"
    result = {"run": meta, "page": page.exists()}
    if page.exists():
        folder = run / "measure"   # the whole delivery: a page may load its own CSS and images (taste-skill did)
        shutil.rmtree(folder, ignore_errors=True)
        shutil.copytree(run / "deliverables", folder, ignore=shutil.ignore_patterns(".*", "Singleton*"))   # not the tool's own browser profile
        m = measure(folder)
        if m:
            result["after"] = {**page_facts(m), "local_files": local_files(page)}
            result["judge"] = ask(e, BEFORE / "fold.png", folder / "fold.png")
    (run / "score.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    return result


def main() -> None:
    e = env()
    if not (BEFORE / "facts.json").exists():
        BEFORE.mkdir(exist_ok=True)
        shutil.copy2(HERE / "in" / "input" / "index.html", BEFORE / "index.html")
        (BEFORE / "facts.json").write_text(json.dumps(page_facts(measure(BEFORE)), indent=1))
    names = [a.replace("/", "__") for a in sys.argv[1:]]
    runs = [OUT / n for n in names] or [p for p in sorted(OUT.iterdir()) if (p / "run.json").exists() and not (p / "score.json").exists()]
    for run in runs:
        try:
            r = score(run, e)
        except Exception as err:   # one run's judge timeout must not leave the rest unscored
            print(run.name, "not scored:", repr(err)[:300], flush=True)
            continue
        a = r.get("after") or {}
        print(run.name, r["run"]["status"], "page" if r["page"] else "no page", a.get("tells"), sum((a.get("facts") or {}).values()),
              (r.get("judge") or {}).get("designed"), flush=True)


if __name__ == "__main__":
    main()
