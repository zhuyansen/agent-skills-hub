"""Daily review pass for the reviewed scenario pages and their GitHub lists:
/best/claude-video-skills/ (zhuyansen/awesome-claude-video-skills) and, since 10-03,
/best/ppt-presentation/ (zhuyansen/awesome-codex-ppt-skills). Each page has its own
questions and types in ops/jev-review/scenario_gate.py (profile()).

What the maintainer did by hand on 09-27, 09-30 and 10-03, as one job:

  1. candidates   GitHub search (scenario_gate.collect) + catalog rows first seen in the
                  last LOOKBACK_DAYS that match the page's keywords, minus every repo
                  already listed, excluded or reviewed
  2. review       Jev reads each README (scenario_gate.judge, state kept in git)
  3. admit        the page's rules: on topic, and the README quality bar under 50 stars.
                  Repos the owner names by hand are not touched here.
  4. describe     a Chinese description per admitted repo (GPT via FlatRouter), checked by
                  Jev against the original; one retry, then the original text is kept
  5. publish      page config, types, catalog queue + grades, the GitHub list
  6. report       markdown for the job summary and the tracking issue

The workflow (.github/workflows/video-daily.yml) commits, pushes and deploys.

Usage: python ops/awesome/daily_video_pass.py <report.md> <slug>=<list-repo-dir> [...]
Env:   OPENROUTER_API_KEY (Jev), FLATROUTER_API_KEY + FLATROUTER_BASE_URL (descriptions),
       SUPABASE_DB_URL, GH_TOKEN (gh CLI); GITHUB_REPOSITORY + ACTIONS_TOKEN to see a sync
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "ops/jev-review"), str(ROOT / "backend"), str(ROOT / "ops/awesome")]
import scenario_gate as gate  # noqa: E402

SLUG = "claude-video-skills"   # the page being processed; main() sets it per page
KEYWORDS = ROOT / "frontend/scripts/scenario-keywords.json"
DESC_ZH = ROOT / "frontend/scripts/scenario-desc-zh.json"
KINDS = ROOT / "frontend/scripts/scenario-kinds.json"
PREVIEWS = ROOT / "ops/awesome/previews.json"
LOOKBACK_DAYS = 4
PAGE_NAMES = {"claude-video-skills": "视频页", "ppt-presentation": "PPT 页", "typesafe-jev": "Jev 页",
              "skill-management-tools": "Skill 管理页", "telegram-bot": "Telegram 页", "ai-design": "设计页",
              "knowledge-base": "知识库页", "claude-code-hooks": "Hooks 页",
              "obsidian-second-brain": "Obsidian 页", "anti-slop": "去 AI 味页",
              "image-generation": "生图页"}
QUEUE_TAG = "daily-video-pass"
DESC_MODEL = "gpt-5.6"
DESC_MAX = 80
FAITHFUL_MIN = 0.5   # Jev: good translations scored 0.72-0.78, embellished or wrong 0.01-0.03 (10-03)
FAITHFUL = {
    "same_meaning": {"type": "noul", "instructions": {
        "question": "Does `zh` say what `original` says, in Chinese?",
        "focus": "The main claim and what the tool does must match; a shorter wording is fine."}},
    "adds_nothing": {"type": "noul", "instructions": {
        "question": "Does `zh` avoid claims, numbers or features that are not in `original`?"}},
}
SYNC_WAIT_SECONDS = 45 * 60
SYNC_POLL_SECONDS = 300
HTTP_TIMEOUT = 90
DESC_PROMPT = ("把 GitHub 仓库描述翻译成简体中文。只说原文说的,删去营销词(如 world's first、ultimate、100M views),"
               "产品、模型和技术名保留原文(Claude Code、Codex、Remotion、HyperFrames、Manim、MCP、skill、agent 等),"
               "不超过 80 个字符,不用竖线和换行。原文已是中文就整理精简。只输出译文。")


def log(msg: str) -> None:
    print(msg, flush=True)


# ── 0. never alongside a sync ─────────────────────────────────────────────────

def wait_for_sync() -> bool:
    """True when no sync is queued or running, waiting up to SYNC_WAIT_SECONDS."""
    from readme_backfill import sync_active  # backend/readme_backfill.py, same rule as the backfill
    deadline = time.time() + SYNC_WAIT_SECONDS
    while sync_active():
        if time.time() > deadline:
            return False
        log("a sync is queued or running; waiting")
        time.sleep(SYNC_POLL_SECONDS)
    return True


# ── 1. candidates ─────────────────────────────────────────────────────────────

def db_url() -> str:
    return os.environ.get("SUPABASE_DB_URL") or next(
        m.group(1).strip() for line in (ROOT / "backend/.env").read_text().splitlines()
        if (m := re.match(r'\s*SUPABASE_DB_URL\s*=\s*["\']?([^"\'\n]+)', line)))


def page_match() -> dict:
    return next(s for s in json.loads(KEYWORDS.read_text()) if s["slug"] == SLUG)["match"]


def listed_names() -> set[str]:
    return {k.lower() for k in json.loads(KINDS.read_text())[SLUG]["repos"]}


def catalog_candidates(match: dict, skip: set[str]) -> list[dict]:
    import psycopg2
    since = (date.today() - timedelta(days=LOOKBACK_DAYS)).isoformat()
    with psycopg2.connect(db_url(), connect_timeout=30) as conn, conn.cursor() as cur:
        cur.execute("SET statement_timeout = '60s'")
        cur.execute("SELECT repo_full_name, repo_name, coalesce(description,''), coalesce(topics,'[]'), stars, "
                    "created_at::date FROM skills WHERE stars >= %s AND (first_seen >= %s OR "
                    "(stars >= %s AND last_synced >= %s))", (gate.GATE_FLOOR, since, gate.PAGE_FLOOR, since))
        rows = cur.fetchall()
    found = []
    for full, name, desc, topics, stars, created in rows:
        try:
            tl = json.loads(topics) if isinstance(topics, str) else list(topics or [])
        except ValueError:
            tl = []
        repo = {"name": name or full.split("/")[1], "description": desc, "topics": tl}
        if full.lower() not in skip and gate.matches_page(repo, match):
            found.append({"repo": full, "name": repo["name"], "stars": stars, "description": desc, "topics": tl,
                          "created": str(created), "pushed": "", "source": "catalog"})
    return found


def reviewed_names() -> set[str]:
    names = set()
    for f in ("judged.json", "page-judged.json"):
        path = gate.state_dir(SLUG) / f
        if path.exists():
            names |= {r["repo"].lower() for r in json.loads(path.read_text())}
    return names


def fresh_candidates() -> list[dict]:
    match = page_match()
    skip = listed_names() | {k.lower() for k in match.get("exclude_repos", [])} | reviewed_names()
    gate.collect(SLUG)
    merged = {r["repo"].lower(): r for r in json.loads((gate.out_dir(SLUG) / "candidates.json").read_text())}
    for r in catalog_candidates(match, skip):
        merged.setdefault(r["repo"].lower(), r)
    fresh = [r for k, r in merged.items() if k not in skip]
    (gate.out_dir(SLUG) / "candidates.json").write_text(json.dumps(fresh, ensure_ascii=False, indent=1))
    return fresh


# ── 3. admit ──────────────────────────────────────────────────────────────────

def admitted(fresh: list[dict]) -> tuple[list[dict], list[dict]]:
    names = {r["repo"] for r in fresh}
    rows = [r for r in json.loads((gate.state_dir(SLUG) / "judged.json").read_text()) if r["repo"] in names]
    for r in rows:
        r["verdict"] = gate.verdict(r, SLUG)
    ok = [r for r in rows if r["verdict"] == "admit" or (r["stars"] >= gate.PAGE_FLOOR and r["verdict"] == "low_quality")]
    return sorted(ok, key=lambda r: -r["stars"]), rows


# ── 4. describe ───────────────────────────────────────────────────────────────

def faithful(jev, original: str, zh: str) -> float:
    """Jev's check of a translation: the lower of its two answers."""
    state = json.dumps({"original": original[:600], "zh": zh}, ensure_ascii=False)
    answers = jev.decisions(state, FAITHFUL).answers
    return min(float(answers.get(k, {}).get("noul", 0.0)) for k in FAITHFUL)


def describe_zh(row: dict, jev) -> tuple[str, float]:
    """A Chinese description Jev accepts, or ("", score) so the page keeps the original."""
    text = row["description"] or re.sub(r"\s+", " ", gate.prose(gate.readme_of(SLUG, row["repo"])))[:600]
    best = ("", 0.0)
    for _ in range(2):
        zh = translate(text)
        if not zh:
            continue
        score = faithful(jev, text, zh)
        if score >= FAITHFUL_MIN:
            return zh, score
        best = max(best, (zh, score), key=lambda p: p[1])
    log(f"  {row['repo']}: description not used, Jev {best[1]:.2f}")
    return "", best[1]


def translate(text: str, prompt: str = DESC_PROMPT) -> str:
    body = {"model": DESC_MODEL, "temperature": 0, "messages": [
        {"role": "system", "content": prompt}, {"role": "user", "content": text}]}
    req = urllib.request.Request(os.environ["FLATROUTER_BASE_URL"].rstrip("/") + "/chat/completions",
                                 data=json.dumps(body).encode(), headers={
                                     "Authorization": f"Bearer {os.environ['FLATROUTER_API_KEY']}",
                                     "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as res:
                out = json.load(res)["choices"][0]["message"]["content"]
            out = re.sub(r"\s+", " ", out).replace("|", "/").strip().strip('"')
            return out if len(out) <= DESC_MAX else out[:DESC_MAX - 1].rstrip() + "…"
        except Exception as exc:  # noqa: BLE001 — a missing description falls back to the original
            log(f"  translation retry {attempt + 1}: {str(exc)[:80]}")
            time.sleep(5 * (attempt + 1))
    return ""


# ── 5. publish ────────────────────────────────────────────────────────────────

def add_to_page(names: list[str], zh: dict[str, str]) -> None:
    """Add reviewed repos to the page's admit_reviewed. Edits the JSON, not its text: a
    regex over the text assumed "related" follows "match" and a comma follows the list,
    and failed on the video and Jev pages when either was not so (10-04)."""
    pages = json.loads(KEYWORDS.read_text())
    match = next(p for p in pages if p["slug"] == SLUG)["match"]
    have = match.get("admit_reviewed", [])
    match["admit_reviewed"] = have + [n for n in names if n not in have]
    KEYWORDS.write_text(json.dumps(pages, ensure_ascii=False, indent=1) + "\n")
    desc = json.loads(DESC_ZH.read_text())
    desc.update({n: v for n, v in zh.items() if v})
    DESC_ZH.write_text(json.dumps(desc, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


def keep_page_rows(rows: list[dict]) -> None:
    """Admitted repos of 50 stars or more go with the page's own rows (on_page reads them there)."""
    path = gate.state_dir(SLUG) / "page-judged.json"
    page = json.loads(path.read_text())
    have = {r["repo"] for r in page}
    page += [r for r in rows if r["stars"] >= gate.PAGE_FLOOR and r["repo"] not in have]
    path.write_text(json.dumps(page, ensure_ascii=False, indent=1))


def queue_and_grade(names: list[str]) -> dict:
    """Queue every admitted repo for the sync; give catalog rows without a README one, and a grade."""
    import psycopg2
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from app.models.skill import Skill
    from app.services.catalog_admission import REPO_NAME, apply
    from app.services.grade_refresh import _WRITE_GRADE
    from app.services.security_scanner import SecurityScanner

    names = [n for n in names if REPO_NAME.match(n)]
    with psycopg2.connect(db_url(), connect_timeout=30) as conn:
        for n in names:
            apply(conn, n, "approved", QUEUE_TAG)
        conn.commit()
    engine = create_engine(db_url().replace("postgres://", "postgresql://", 1), pool_pre_ping=True)
    db = sessionmaker(bind=engine)()
    db.execute(text("SET statement_timeout = '30s'"))
    rows = {r[0]: r for r in db.execute(text(
        "SELECT repo_full_name, security_grade, coalesce(readme_size,0) FROM skills WHERE repo_full_name = ANY(:n)"),
        {"n": names})}
    write = text("UPDATE skills SET readme_content = :v, readme_size = :n, readme_fetched_at = now() "
                 "WHERE repo_full_name = :r AND (readme_content IS NULL OR readme_content = '')")
    for n, (_, _, size) in rows.items():
        body = gate.readme_of(SLUG, n)[:50000] if size == 0 else ""
        if body.strip():
            db.execute(write, {"v": body, "n": len(body), "r": n})
    db.commit()
    ungraded = [n for n, (_, grade, _) in rows.items() if grade in (None, "unknown")]
    scanner, writes, grades = SecurityScanner(), [], {}
    for s in db.query(Skill).filter(Skill.repo_full_name.in_(ungraded)).all():
        grade, flags = scanner.scan_single(s)
        writes.append({"_id": s.id, "_grade": grade, "_flags": json.dumps(flags)})
        grades[s.repo_full_name] = grade
    if writes:
        db.execute(_WRITE_GRADE, writes)
        db.commit()
    db.close()
    return {"in_catalog": sorted(rows), "queued_only": sorted(set(names) - set(rows)), "graded": grades}


def rebuild_list(list_dir: Path) -> str:
    names = [n for n in json.loads(KINDS.read_text())[SLUG]["repos"] if n.count("/") == 1]
    tmp = gate.out_dir(SLUG) / "listed-names.json"
    tmp.write_text(json.dumps(names))
    py, out = sys.executable, []
    for args in (["ops/awesome/previews.py", "find", str(gate.out_dir(SLUG) / "readme"), str(PREVIEWS), str(tmp)],
                 ["ops/awesome/build_video_list.py", str(list_dir), SLUG],
                 ["ops/awesome/previews.py", "thumbs", str(PREVIEWS), str(list_dir)],
                 ["ops/awesome/build_video_list.py", str(list_dir), SLUG]):
        done = subprocess.run([py, *args], cwd=ROOT, capture_output=True, text=True)
        if done.returncode:
            raise RuntimeError(f"{args[0]} failed: {done.stderr[-600:]}")
        out.append(done.stdout.strip().splitlines()[-1] if done.stdout.strip() else "")
    return out[-1]


def exclude_gone() -> list[str]:
    """Listed repos to drop: ones GitHub no longer serves (deleted or private), and old names
    of renamed repos whose new name is listed too. The catalog notices both only later: the
    page kept showing deleted repos the list dropped (Vincentwei1021/video-shotcraft, 10-03),
    and a sync that met a renamed repo under its new name added a second row, so both names
    were reviewed and listed (opus-pro/opus-video-studio and opusclip-video-tools, 10-05).
    Edits the page JSON, not its text (the regex version broke on key order, 10-04)."""
    kinds = json.loads(KINDS.read_text())
    listed = [n for n in kinds[SLUG]["repos"] if n.count("/") == 1]
    lower = {n.lower() for n in listed}
    drop = []
    for name in listed:
        done = subprocess.run(["gh", "api", f"repos/{name}", "--jq", ".full_name"], capture_output=True, text=True)
        now = done.stdout.strip()
        if done.returncode and "Not Found" in (done.stdout + done.stderr):
            drop.append(name)
        elif now and now.lower() != name.lower() and now.lower() in lower:
            drop.append(name)
    if not drop:
        return []
    pages = json.loads(KEYWORDS.read_text())
    match = next(p for p in pages if p["slug"] == SLUG)["match"]
    match["exclude_repos"] = match.get("exclude_repos", []) + [n for n in drop if n not in match.get("exclude_repos", [])]
    KEYWORDS.write_text(json.dumps(pages, ensure_ascii=False, indent=1) + "\n")
    for name in drop:
        kinds[SLUG]["repos"].pop(name, None)
    KINDS.write_text(json.dumps(kinds, ensure_ascii=False, indent=1) + "\n")
    return drop

def consistency() -> str:
    done = subprocess.run([sys.executable, "ops/awesome/check_consistency.py", SLUG], cwd=ROOT, capture_output=True, text=True)
    return (done.stdout.strip() or done.stderr.strip()).replace("\n", " · ")


# ── 6. report ─────────────────────────────────────────────────────────────────

def report(path: Path, ok: list[dict], rows: list[dict], zh: dict, db: dict, list_line: str, before: str) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    near = sorted([r for r in rows if r not in ok and r["readme_chars"] and
                   (r["verdict"] == "low_quality" or gate.on_topic(r, SLUG) >= 0.4)],
                  key=lambda r: -r["stars"])
    kinds = json.loads(KINDS.read_text())[SLUG]["repos"]
    lines = [f"## {PAGE_NAMES.get(SLUG, SLUG)}每日补充 · {today}", "",
             f"- 页面与 GitHub 合集一致性(运行前):{before}",
             f"- 新评审 {len(rows)} 个,按规则放行 **{len(ok)}** 个"
             f"(跑题 {sum(r['verdict'] == 'off_topic' for r in rows)}、质量线下 {sum(r['verdict'] == 'low_quality' and r not in ok for r in rows)})",
             f"- 已在目录 {len(db.get('in_catalog', []))} 个,排队等同步 {len(db.get('queued_only', []))} 个",
             f"- 合集:{list_line}", ""]
    if ok:
        lines += ["| 仓库 | ★ | 类型 | 中文描述 |", "|---|---:|---|---|"]
        lines += [f"| [{r['repo']}](https://github.com/{r['repo']}) | {r['stars']} | {kinds.get(r['repo'], '')} | "
                  f"{zh.get(r['repo']) or '(Jev 未通过,沿用原文)'} |" for r in ok]
        lines.append("")
    if near:
        lines += ["线下(切题但没放行,要加请点名):", ""]
        lines += [f"- {r['repo']}({r['stars']}★,{r['verdict']},质量 {r['quality']:.2f})" for r in near[:15]]
    path.write_text("\n".join(lines) + "\n")


def run_page(slug: str, list_dir: Path, report_path: Path) -> None:
    global SLUG
    SLUG = slug
    before = consistency()
    fresh = fresh_candidates()
    log(f"[{slug}] {len(fresh)} candidates not reviewed before")
    gate.judge(SLUG)
    ok, rows = admitted(fresh)
    log(f"[{slug}] {len(ok)} pass the page's rules")
    from jev_client import OpenRouter
    jev = OpenRouter()
    described = {r["repo"]: describe_zh(r, jev) for r in ok}
    zh = {repo: text for repo, (text, _) in described.items()}
    db = {}
    if ok:
        names = [r["repo"] for r in ok]
        add_to_page(names, zh)
        keep_page_rows(ok)
        gate.types(SLUG)
        db = queue_and_grade(names)
    gone = exclude_gone()
    list_line = rebuild_list(list_dir)
    report(report_path, ok, rows, zh, db, list_line, before)
    if gone:
        with report_path.open("a") as f:
            f.write("\n已从页面和合集移除(GitHub 上已删除或转私有,或改名后新名字已在页上):" + "、".join(gone) + "\n")


def main() -> int:
    report_path = Path(sys.argv[1])
    pages = [arg.split("=", 1) for arg in sys.argv[2:]]
    if not wait_for_sync():
        report_path.write_text("## 每日补充\n\n同步一直在运行,今天跳过。\n")
        return 0
    parts = []
    for slug, list_dir in pages:
        part = report_path.with_suffix(f".{slug}.md")
        try:
            run_page(slug, Path(list_dir).expanduser(), part)
        except Exception as exc:  # noqa: BLE001 — one page failing must not stop the other
            part.write_text(f"## {PAGE_NAMES.get(slug, slug)}每日补充失败\n\n`{type(exc).__name__}: {str(exc)[:400]}`\n")
            log(f"[{slug}] failed: {exc}")
        parts.append(part.read_text())
    report_path.write_text("\n\n".join(parts))
    log(report_path.read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
