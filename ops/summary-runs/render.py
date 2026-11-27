"""Evidence pictures for the film: each delivered summary as a page, its mistakes marked.

  python3 ops/summary-runs/render.py                     # every run with a document -> out/evidence/<task>__<owner__repo>.png
  python3 ops/summary-runs/render.py t2 phuryn/pm-skills # one run
  python3 ops/summary-runs/render.py --source            # the meeting record itself -> out/evidence/source.png

On top of each page a card gives the 7 verdicts (results.json once score.py has run, else the six
scripted ones and the tester's), the 字数 and the counts behind them. Marked in the text: red, a
figure the record does not say, an old figure given as current, a task with the wrong owner or date,
an open point not marked open; yellow, an action item the record does not have (kit's candidates for
check 7, not verdicts); blue, small talk. Pictures are 2,000 px wide (1,000 CSS px at 2x), made with
Chrome headless on the Mac (Playwright where it is installed). RUNS_HOME as in score.py.
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

BRIEF = {"t1": "一句话：帮我总结一下这个会议记录", "t2": "一段话：800 字以内、先写结论、决定和待办、数字照原文、没定的标出来、不许编"}


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
        if "invented" in tester:
            got["invented"] = bool(tester["invented"].get("pass"))
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
        page = tc.to_html(kit.SOURCE.replace("\n", "\n\n"), title="会议记录")
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
