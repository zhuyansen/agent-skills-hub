"""Evidence pictures for the film: each delivered report as a page, its AI tone and its made-up figures marked.

  python3 ops/writing-runs/render.py                     # every run with a document -> out/evidence/<task>__<owner__repo>.png
  python3 ops/writing-runs/render.py t2 op7418/Humanizer-zh   # one run
  python3 ops/writing-runs/render.py --source            # the fact list itself -> out/evidence/source.png

On top of each page a card gives the 8 verdicts (results.json once score.py has run, else the seven
scripted ones and the tester's), the 字数 and the counts behind them. Marked in the text: red, a
figure the list does not give (the tooltip says how it may have been worked out), an old figure
given as current, a problem turned into a success; yellow, stock phrases, vague verbs and empty
elevation; orange underline, 排比. Pictures are 2,000 px wide (1,000 CSS px at 2x), made with Chrome
headless on the Mac (Playwright where it is installed). RUNS_HOME as in score.py.
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = Path(os.environ.get("RUNS_HOME") or HERE).resolve()
sys.path.insert(0, str(HERE / "in"))
import kit  # noqa: E402
import textcheck as tc  # noqa: E402

BRIEF = {"t1": "一句话：帮我写一份季度工作总结", "t2": "一段话：只用清单、1500 字左右、三块、说大白话、别用套话排比、问题写实"}


def verdicts(task: str, repo: str, r: dict, run: Path) -> dict:
    results = HOME / "results.json"
    if results.exists():
        row = next((x for x in json.loads(results.read_text()) if x["task"] == task and x["repo"] == repo), None)
        if row:
            return row["checks"]
    got = {c: v["pass"] for c, v in r["checks"].items()}
    report = run / "test" / "report.json"
    if report.exists():
        tester = {c.get("id"): c for c in json.loads(report.read_text()).get("checks", [])}
        if "facts" in tester:
            got["facts"] = bool(tester["facts"].get("pass"))
    return got


def one(task: str, repo: str) -> Path | None:
    run = HOME / "out" / task / repo.replace("/", "__")
    report = json.loads((run / "test" / "report.json").read_text()) if (run / "test" / "report.json").exists() else {}
    named = report.get("file") or ""
    doc = run / "deliverables" / named[len("output/"):] if named.startswith("output/") else None
    doc = doc if doc and doc.is_file() else kit.deliverable(run / "deliverables")
    text = kit.read(doc) if doc else ""
    if not text.strip():
        print(f"{task} {repo}: no document", flush=True)
        return None
    r = kit.check(text)
    label = f"{task} · {repo} · {doc.name}　　{BRIEF.get(task, '')}"
    page = tc.to_html(text, r["marks"], title=f"{task} {repo}", card=kit.card(r, verdicts(task, repo, r, run), label))
    png = tc.shoot(page, HOME / "out" / "evidence" / f"{task}__{repo.replace('/', '__')}.png")
    print(f"{task} {repo}: {png}", flush=True)
    return png


def main() -> None:
    args = sys.argv[1:]
    if args == ["--source"]:
        page = tc.to_html(kit.SOURCE, title="季度事实清单")
        print(tc.shoot(page, HOME / "out" / "evidence" / "source.png"))
        return
    tasks = [args[0]] if args and args[0] in ("t1", "t2") else ["t1", "t2"]
    repos = args[1:] if args and args[0] in ("t1", "t2") else []
    for task in tasks:
        folder = HOME / "out" / task
        names = [r.replace("/", "__") for r in repos] or sorted(p.name for p in folder.iterdir() if p.is_dir()) if folder.exists() else []
        for name in names:
            one(task, name.replace("__", "/", 1))


if __name__ == "__main__":
    main()
