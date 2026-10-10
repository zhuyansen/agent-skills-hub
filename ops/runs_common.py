"""Shared by the tests' evidence.py scripts (ops/*-runs): the evidence page shell, and writing
a test's results into the page data (scenario-runs.json) and the page's method block."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS_JSON = ROOT / "frontend/scripts/scenario-runs.json"
KEYWORDS_JSON = ROOT / "frontend/scripts/scenario-keywords.json"
PUBLIC = ROOT / "frontend/public/best-runs"
REPO_URL = "https://github.com/zhuyansen/agent-skills-hub/blob/main/ops/"
STYLE = """:root{--bg:#fff;--fg:#1f2328;--mute:#59636e;--line:#d0d7de;--card:#f6f8fa;--ok:#1a7f37;--no:#cf222e}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--mute:#9198a1;--line:#30363d;--card:#161b22;--ok:#3fb950;--no:#f85149}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,'PingFang SC',sans-serif}
main{max-width:960px;margin:0 auto;padding:24px 16px 48px}a{color:#0969da}img{max-width:100%;border:1px solid var(--line);border-radius:8px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 8px}.mute{color:var(--mute);font-size:13px}.ok{color:var(--ok);font-weight:600}.no{color:var(--no);font-weight:600}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid var(--line);padding:6px 10px;text-align:left;vertical-align:top}
th{background:var(--card)}pre{white-space:pre-wrap;word-wrap:break-word;margin:6px 0 0;padding:12px;border:1px solid var(--line);
border-radius:8px;background:var(--card);font:13px/1.5 ui-monospace,Menlo,monospace;max-height:420px;overflow:auto}summary{cursor:pointer}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media(max-width:700px){.two{grid-template-columns:1fr}}"""


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def key(repo: str) -> str:
    return repo.replace("/", "__")


def shell(title: str, back: tuple[str, str], body: str) -> str:
    """An evidence page: noindex, a link back to the scenario page, then the body."""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>{esc(title)}</title><style>{STYLE}</style></head><body><main>
<p class="mute"><a href="{back[0]}">← {esc(back[1])}</a></p>
{body}
</main></body></html>"""


def final_message(transcript: Path) -> str:
    """The session's closing message, from a stream-json transcript."""
    last = ""
    if not transcript.exists():
        return last
    for line in transcript.read_text(errors="ignore").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "result":
            last = e.get("result") or ""
    return last


def write_runs(slug: str, entry: dict) -> None:
    runs = json.loads(RUNS_JSON.read_text())
    runs[slug] = entry
    RUNS_JSON.write_text(json.dumps(runs, indent=1, ensure_ascii=False) + "\n")


def pair(en: str, zh: str) -> dict:
    return {"item": en, "item_zh": zh}


def update_method(slug: str, findings: list[dict], did: dict, limits: dict, marker: str) -> None:
    """Put the test into the page's method block: its findings first, what we did, and its limits in
    place of the "not yet run" line. `marker` is a phrase of this test's first finding, so a rerun replaces."""
    pages = json.loads(KEYWORDS_JSON.read_text())
    m = next(p for p in pages if p["slug"] == slug)["method"]
    ours = {f["item"] for f in findings} | {did["item"], limits["item"]}
    stale = lambda x: x["item"] in ours or marker in x["item"] or "not yet run" in x["item"]   # noqa: E731
    m["h3_findings"] = ["What our test and the research found", "实测和研究发现了什么"]
    m["findings"] = findings + [x for x in m["findings"] if not stale(x) and not x.get("ours")]
    for f in findings:
        f["ours"] = True
    m["did"] = [{**did, "ours": True}] + [x for x in m["did"] if not x.get("ours")]
    m["not_done"] = [{**limits, "ours": True}] + [x for x in m["not_done"] if not stale(x) and not x.get("ours")]
    KEYWORDS_JSON.write_text(json.dumps(pages, indent=1, ensure_ascii=False) + "\n")
