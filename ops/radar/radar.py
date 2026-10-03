"""New-term radar: one daily report of terms that are starting to surge.

  python ops/radar/radar.py <report.md> <snapshot-dir> [--skip-gsc] [--skip-db] [--skip-sitemaps]

Signals (see ops/gefei-seo-playbook.md §3, built 2026-10-03):
  ② GitHub   terms that new repos in the catalog suddenly share (signals.github_surge)
  ③ sitemaps pages competitors added since yesterday (sitemap_diff.diff)
  ④ GSC      queries that brought impressions for the first time (signals.gsc_new)
Terms from ② and ③ go to Jev with a few examples: is this the name of a specific new
product, model or technique, or a common word? Those that pass, and that no scenario
page covers yet, lead the report. Writes <report.md> and a JSON copy beside it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / "ops/jev-review")]
import signals  # noqa: E402
import sitemap_diff  # noqa: E402

NAMED_MIN = 0.5
NAMED = {"named_thing": {"type": "noul", "instructions": {
    "question": "Is `term` the name of a specific product, model, tool, company or technique, rather than a common word or a generic category?",
    "focus": "`examples` are repo names, descriptions or page paths where it appeared. 'opus 5.5', 'hyperframes', "
             "'jev' are names; 'dashboard', 'voice notes', 'pdf' are not."}}}


def run(name: str, fn, skip: bool) -> dict:
    if skip:
        return {"skipped": True}
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 — one signal failing still leaves a report
        return {"error": f"{type(exc).__name__}: {str(exc)[:160]}"}


def covered(term: str) -> str:
    """The scenario page whose slug, title or keywords already hold the term, if any."""
    for page in json.loads((ROOT / "frontend/scripts/scenario-keywords.json").read_text()):
        words = [page["slug"].replace("-", " "), page["title"].lower(),
                 *[k.lower() for k in page["match"].get("primary_keywords", [])]]
        if any(term in w for w in words) and not page.get("retired"):
            return page["slug"]
    return ""


def judge(rows: list[dict]) -> None:
    """Jev's named-thing score on each term; left out when the key is missing."""
    try:
        from jev_client import OpenRouter
        jev = OpenRouter()
    except Exception:  # noqa: BLE001
        return
    for r in rows:
        state = json.dumps({"term": r["term"], "examples": r.get("examples", [])[:3]}, ensure_ascii=False)
        r["named"] = float(jev.decisions(state, NAMED).answers["named_thing"].get("noul", 0.0))
        r["page"] = covered(r["term"])


def leads(gh: dict, sm: dict) -> list[dict]:
    """Terms from both signals, merged; a term in both is the strongest lead."""
    out: dict[str, dict] = {}
    for src, block in (("GitHub", gh), ("竞品", sm)):
        for r in block.get("terms", []):
            row = out.setdefault(r["term"], {"term": r["term"], "signals": [], "examples": []})
            row["signals"].append(f"{src} {r['recent']} 处 (×{r['lift']})")
            row["examples"] += r.get("examples", [])
    rows = list(out.values())
    judge(rows)
    rows.sort(key=lambda r: (-(r.get("named", 0) >= NAMED_MIN), -len(r["signals"]), -r.get("named", 0)))
    return rows


def markdown(lead: list[dict], gh: dict, sm: dict, gsc: dict) -> str:
    lines = ["## 新词雷达", "", "### 候选新词(Jev 判为专有名词、且还没有对应场景页的排前面)", "",
             "| 词 | 信号 | Jev | 已有页面 | 例子 |", "|---|---|---|---|---|"]
    for r in lead[:20]:
        ex = " / ".join(e[:50] for e in r["examples"][:2]).replace("|", "/")
        named = f"{r['named']:.2f}" if "named" in r else "—"
        lines.append(f"| **{r['term']}** | {'; '.join(r['signals'])} | {named} | {r.get('page') or '无'} | {ex} |")
    lines += ["", "### ④ GSC 首次出现的搜索词", ""]
    if gsc.get("queries"):
        lines += [f"{gsc['window']},共 {gsc['total_new']} 个新词,曝光 ≥{signals.GSC_MIN_IMPRESSIONS} 的:", "",
                  "| 搜索词 | 曝光 | 点击 | 落地页 |", "|---|---|---|---|"]
        lines += [f"| {q['query']} | {q['impressions']} | {q['clicks']} | {q['page'].replace('https://agentskillshub.top', '')} |"
                  for q in gsc["queries"]]
    else:
        lines.append(f"无({gsc.get('error') or ('跳过' if gsc.get('skipped') else '没有新词')})")
    lines += ["", "### 数据状态", "",
              f"- ② GitHub:近 {signals.RECENT_DAYS} 天新建 {gh.get('repos_recent', '—')} 个仓库,"
              f"基线 {gh.get('repos_baseline', '—')} 个 {gh.get('error', '')}"]
    for site, s in sm.get("sites", {}).items():
        state = s.get("error") or ("首次运行,只建快照" if s.get("first_run") else f"{s['urls']} 个网址,新增 {s['new']}")
        lines.append(f"- ③ {site}:{state}")
    if sm.get("error") or sm.get("skipped"):
        lines.append(f"- ③ 竞品:{sm.get('error') or '跳过'}")
    return "\n".join(lines) + "\n"


def main() -> int:
    report, snaps = Path(sys.argv[1]), Path(sys.argv[2])
    flags = set(sys.argv[3:])
    gh = run("github", signals.github_surge, "--skip-db" in flags)
    sm = run("sitemaps", lambda: sitemap_diff.diff(snaps), "--skip-sitemaps" in flags)
    gsc = run("gsc", signals.gsc_new, "--skip-gsc" in flags)
    lead = leads(gh, sm)
    report.write_text(markdown(lead, gh, sm, gsc))
    report.with_suffix(".json").write_text(json.dumps({"leads": lead, "github": gh, "sitemaps": sm, "gsc": gsc},
                                                      ensure_ascii=False, indent=1, default=str))
    print(report.read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
