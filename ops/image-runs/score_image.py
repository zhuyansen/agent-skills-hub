"""Score finished image runs (ops/image-runs/out/<owner__repo>/): what the judge sees, and what is counted.

  python ops/image-runs/score_image.py [owner/repo ...]     # default: every run without score.json
  python ops/image-runs/score_image.py --text [owner/repo ...]   # the OCR part again, the judge's answers kept

Counted here: which of the four files exist, minutes, the image calls the proxy logged
(images.jsonl: model asked for, model used, cost), and the agent's last line. Judged by
gpt-6-astra through FlatRouter (FLATROUTER_* in ~/.claude/.env), one call per question so each
answer cites what it saw: the poster's six lines letter by letter, the name on the bread bag, and
the four mascot pictures together (same character or not, each pose).
Text is decided by OCR, not by the judge (text_check.py): on the model line-up the judge passed 4 of 16
posters with misspelt lines ("周云上午", "Bristel", "可谅"); three OCR passes matched a careful read on 16 of 16.
"""
import base64
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from text_check import LINES, check  # noqa: E402 (OCR: the literal text check)

HERE = Path(__file__).parent
OUT = HERE / "out"
FILES = ("poster", "product", "mascot-1", "mascot-2", "mascot-3", "mascot-4")
MASCOTS = FILES[2:]
STRICT = ("Be strict and literal. Judge only what is in the picture; the visual style is the maker's choice "
          "and is not marked down. Reply with JSON only.")
POSTER_Q = (f"This should be a portrait poster for a bakery: a loaf of bread in warm morning light, showing exactly "
            f"these six lines of text and no other text: {json.dumps(LINES, ensure_ascii=False)}. "
            "For each line say whether it appears spelled exactly (every letter, the middle dot, the Chinese "
            "characters), and quote what you actually read. Return {\"lines\": [{\"line\", \"exact\": bool, "
            "\"read\"}], \"other_text\": bool, \"follows_brief\": 1-5, \"looks\": 1-5, \"note\": short}. ")
PRODUCT_Q = ("This should be a square product photo: a kraft-paper bread bag standing upright on a plain light-grey "
             "background, soft studio light, a sourdough loaf peeking out of the top, the words \"Morning Loaf\" printed "
             "on the bag in dark brown and no other text. Quote the text you read on the bag. Return {\"name_exact\": bool, "
             "\"read\": text, \"other_text\": bool, \"follows_brief\": 1-5, \"looks\": 1-5, \"note\": short}. ")
MASCOT_Q = ("These four pictures should show the same mascot, Bun: a small round bread-roll character in a white "
            "chef's hat and a red scarf. 1: front view, waving hello. 2: side view, running to the left. 3: carrying a "
            "tray of three croissants. 4: asleep in a wicker bread basket. No text. Judge whether all four are clearly "
            "the same character (shape, colours, face, hat, scarf). Return {\"same_character\": 1-5, \"poses\": "
            "[bool, bool, bool, bool], \"hat_and_scarf_all\": bool, \"has_text\": bool, \"looks\": 1-5, \"note\": short}. ")


def env() -> dict:
    vals = {}
    for line in (Path.home() / ".claude/.env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1); vals[k.strip()] = v.strip().strip('"')
    return vals


def find_file(folder: Path, stem: str) -> Path | None:
    """The deliverable named in the brief, whatever image extension it was saved with."""
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (folder / f"{stem}{ext}").exists():
            return folder / f"{stem}{ext}"
    return None


def image_calls(run: Path) -> dict:
    log = run / "images.jsonl"
    rows = [json.loads(x) for x in log.read_text().splitlines() if x.strip()] if log.exists() else []
    done = [r for r in rows if r.get("status") == "completed"]
    return {"calls": len(rows), "completed": len(done), "cost": round(sum(r.get("cost") or 0 for r in done), 4),
            "asked": sorted({str(r.get("asked")) for r in rows}), "models": sorted({r.get("model") for r in done})}


def last_words(run: Path) -> str:
    """The agent's final message (the stop reason when it stopped)."""
    lines = (run / "transcript.jsonl").read_text(errors="ignore").splitlines() if (run / "transcript.jsonl").exists() else []
    for line in reversed(lines):
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "result":
            return str(ev.get("result") or "")[-600:]
    return ""


def data_uri(p: Path) -> str:
    head = p.read_bytes()[:4]
    mime = "image/jpeg" if head[:2] == b"\xff\xd8" else "image/webp" if head == b"RIFF" else "image/png"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def ask(e: dict, question: str, images: list[Path]) -> dict:
    content = [{"type": "text", "text": question + STRICT}]
    content += [{"type": "image_url", "image_url": {"url": data_uri(p)}} for p in images]
    body = {"model": e.get("FLATROUTER_MODEL", "gpt-6-astra"), "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_object"}, "temperature": 0}
    req = urllib.request.Request(e["FLATROUTER_BASE_URL"] + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + e["FLATROUTER_API_KEY"], "Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # FlatRouter is reached directly
    with opener.open(req, timeout=300) as r:
        return json.loads(json.load(r)["choices"][0]["message"]["content"])


def judge(e: dict, files: dict) -> dict:
    out = {}
    if files["poster"]:
        out["poster"] = ask(e, POSTER_Q, [files["poster"]])
    if files["product"]:
        out["product"] = ask(e, PRODUCT_Q, [files["product"]])
    if all(files[m] for m in MASCOTS):
        out["mascot"] = ask(e, MASCOT_Q, [files[m] for m in MASCOTS])
    return out


def text_of(files: dict) -> dict:
    """OCR readings (text_check.py): the poster's six lines, and the shop name on the bag. Whether a line
    OCR did not find is wrong is line_verdict()'s call, with the judge and text_review.json."""
    out = {}
    if files["poster"]:
        c = check(files["poster"])
        out.update(poster_exact=c["exact"], poster_found=c["found"], poster_distance=c["distance"])
    if files["product"]:
        c = check(files["product"], ("Morning Loaf",))
        out.update(bag_name=c["found"][0], bag_distance=c["distance"][0])
    return out


def rescore_text(run: Path) -> None:
    """Only the OCR part again (after text_check.py changed); the judge's answers are kept."""
    s = json.loads((run / "score.json").read_text())
    folder = run / "deliverables"
    s["ocr"] = text_of({stem: find_file(folder, stem) for stem in FILES})
    (run / "score.json").write_text(json.dumps(s, indent=1, ensure_ascii=False))
    print(run.name, s["ocr"].get("poster_exact"), s["ocr"].get("bag_name"), flush=True)


def score(run: Path, e: dict) -> dict:
    folder = run / "deliverables"
    files = {s: find_file(folder, s) for s in FILES}
    result = {"run": json.loads((run / "run.json").read_text()), "files": {s: bool(p) for s, p in files.items()},
              "images": image_calls(run), "last_words": last_words(run), "judge": judge(e, files), "ocr": text_of(files)}
    (run / "score.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    return result


def main() -> None:
    e, args = env(), [a for a in sys.argv[1:] if not a.startswith("--")]
    names = [r.replace("/", "__") for r in args]
    if "--text" in sys.argv:   # python score_image.py --text [owner/repo ...]: OCR again, judge kept
        for run in [OUT / n for n in names] or sorted(p for p in OUT.iterdir() if (p / "score.json").exists()):
            rescore_text(run)
        return
    runs = [OUT / n for n in names] if names else [p for p in OUT.iterdir() if (p / "run.json").exists() and not (p / "score.json").exists()]
    for run in runs:
        if not (run / "run.json").exists():
            continue
        try:
            r = score(run, e)
        except Exception as err:   # a judge timeout or an unreadable deliverable must not leave the rest unscored
            print(run.name, "not scored:", repr(err)[:300], flush=True)
            continue
        print(run.name, r["run"]["status"], sum(r["files"].values()), "files", r["images"], flush=True)


if __name__ == "__main__":
    main()
