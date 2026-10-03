"""New-term radar: one daily report of terms that are starting to surge.

  python ops/radar/radar.py <report.md> <snapshot-dir> [--skip-x] [--skip-hf] [--skip-breakout]
                            [--skip-db] [--skip-sitemaps] [--skip-gsc] [--skip-review]

Signals (see ops/gefei-seo-playbook.md §3), earliest first:
  ① X        names the labs and AI bloggers in sources.json said first (source_signals.x_new, AIsa)
  ① HF       models new to Hugging Face's trending top 50 (source_signals.hf_new)
  ② breakout one new GitHub repo taking off on its own (breakout.breakouts)
  ② GitHub   terms that new repos in the catalog suddenly share (signals.github_surge)
  ③ sitemaps pages competitors and LobeHub added since yesterday (sitemap_diff.diff)
  ④ GSC      queries that brought impressions for the first time (signals.gsc_new)
Terms from ①–③ go to Jev with a few examples: is this the name of a specific new
product, model or technique, or a common word? Those that pass, and that no scenario
page covers yet, lead the report, and are kept in radar_leads; review.py checks them in
Google Trends 14 days later (⑤ as verification, not discovery) and the report ends with
the hit rate per signal. Writes <report.md> and a JSON copy beside it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / "ops/jev-review")]
import breakout  # noqa: E402
import review  # noqa: E402
import signals  # noqa: E402
import sitemap_diff  # noqa: E402
import source_signals  # noqa: E402

NAMED_MIN = 0.5
OTHER_TERMS = 15
SHOWN = 20
NAMED = {"named_thing": {"type": "noul", "instructions": {
    "question": "Is `term` the name of a specific product, model, tool, company or technique, rather than a common word or a generic category?",
    "focus": "`examples` are repo names, descriptions, posts or page paths where it appeared. 'opus 5.5', 'hyperframes', "
             "'jev' are names; 'dashboard', 'voice notes', 'pdf' are not."}}}
# signal key -> label in the report, in the order of how early the signal comes
KINDS = {"x": "①X", "hf": "①HF", "breakout": "②爆发", "github": "②GitHub", "sitemap": "③竞品"}


def run(name: str, fn, skip: bool) -> dict:
    if skip:
        return {"skipped": True}
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 — one signal failing still leaves a report
        return {"error": f"{type(exc).__name__}: {' '.join(str(exc).split())[:160]}"}


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
    for r in rows:
        r["page"] = covered(r["term"])
    try:
        from jev_client import OpenRouter
        jev = OpenRouter()
    except Exception:  # noqa: BLE001
        return
    for r in rows:
        state = json.dumps({"term": r["term"], "examples": r.get("examples", [])[:3]}, ensure_ascii=False)
        try:
            r["named"] = float(jev.decisions(state, NAMED).answers["named_thing"].get("noul", 0.0))
        except Exception:  # noqa: BLE001 — no credit or a timeout: the report goes out without Jev's column
            return


def leads(blocks: dict[str, dict]) -> list[dict]:
    """Terms from every discovery signal, merged; a term in several is the strongest lead."""
    out: dict[str, dict] = {}
    for kind, block in blocks.items():
        for r in block.get("terms", []):
            row = out.setdefault(r["term"], {"term": r["term"], "kinds": [], "signals": [], "examples": [], "variants": []})
            row["kinds"].append(kind)
            row["signals"].append(r.get("note") or f"{KINDS[kind]} {r['recent']} 处 (×{r['lift']})")
            row["examples"] += r.get("examples", [])
            row["variants"] += [v for v in r.get("variants", []) if v not in row["variants"]]
    rows = list(out.values())
    judge(rows)
    # Earliest signal first among equals: a name the labs said today beats a sitemap echo.
    first = {k: i for i, k in enumerate(KINDS)}
    rows.sort(key=lambda r: (-(r.get("named", 0) >= NAMED_MIN), -len(r["kinds"]),
                             min(first[k] for k in r["kinds"]), -r.get("named", 0)))
    return rows


def named(lead: list[dict]) -> list[dict]:
    """Without Jev's column (no key, no credit) every term counts; with it, only names."""
    return [r for r in lead if r.get("named", 1.0) >= NAMED_MIN]


def _cost(*blocks: dict) -> str:
    micros = sum(int(b.get("cost_micros") or 0) for b in blocks)
    return f"${micros / 1e6:.3f}"


def markdown(lead: list[dict], b: dict[str, dict], gsc: dict, rev: dict, summ: dict) -> str:
    lines = ["## 新词雷达", "", "### 候选新词(Jev 判为专有名词、且还没有对应场景页的排前面)", "",
             "| 词 | 信号 | Jev | 已有页面 | 搜索变体 | 例子 |", "|---|---|---|---|---|---|"]
    names_ = named(lead)
    for r in names_[:SHOWN]:
        ex = " / ".join(e[:50] for e in r["examples"][:2]).replace("|", "/").replace("\n", " ")
        score = f"{r['named']:.2f}" if "named" in r else "—"
        lines.append(f"| **{r['term']}** | {'; '.join(r['signals'])} | {score} | {r.get('page') or '无'} | "
                     f"{', '.join(r['variants'][1:]) or '—'} | {ex} |")
    rest = [r["term"] for r in lead if r not in names_][:OTHER_TERMS]
    if rest:
        lines += ["", "其他上升词(Jev 判为普通词):" + "、".join(rest)]

    lines += ["", "### ② 单仓库爆发(近 14 天新建,按每天涨星排;🆕 = 今天第一次达标,进上面的候选词)", ""]
    repos = b["breakout"].get("repos") or []
    if repos:
        lines += ["| 仓库 | ★ | 均/天 | 比昨天 | 天数 | 简介 |", "|---|---|---|---|---|---|"]
        lines += [f"| {'🆕 ' if r.get('new') else ''}[{r['repo']}](https://github.com/{r['repo']}) | {r['stars']} | {r['velocity']} | "
                  f"{'+' + str(r['delta']) if r['delta'] is not None else '—'} | {r['age_days']} | "
                  f"{r['description'][:60].replace('|', '/')} |" for r in repos]
    else:
        lines.append(f"无({b['breakout'].get('error') or ('跳过' if b['breakout'].get('skipped') else '没有爆发仓库')})")

    lines += ["", "### ④ GSC 首次出现的搜索词(新鲜数据,约晚 1 天)", ""]
    if gsc.get("queries"):
        lines += [f"{gsc['window']},共 {gsc['total_new']} 个新词,曝光 ≥{signals.GSC_MIN_IMPRESSIONS} 的:", "",
                  "| 搜索词 | 曝光 | 点击 | 落地页 |", "|---|---|---|---|"]
        lines += [f"| {q['query']} | {q['impressions']} | {q['clicks']} | {q['page'].replace('https://agentskillshub.top', '')} |"
                  for q in gsc["queries"]]
    else:
        lines.append(f"无({gsc.get('error') or ('跳过' if gsc.get('skipped') else '没有新词')})")

    lines += ["", "### ⑤ 复盘(14 天前报出的词,在 Google Trends 里起没起来)", ""]
    if rev.get("checked"):
        lines += ["| 词 | 首次报出 | 结论 | 提前天数 |", "|---|---|---|---|"]
        lines += [f"| {c['term']} | {c['first_seen']} | {c['verdict']} | {c['lead_days'] if c['lead_days'] is not None else '—'} |"
                  for c in rev["checked"]]
    else:
        lines.append(f"今天没有到期的词({rev.get('error') or ('跳过' if rev.get('skipped') else '最早报出的词还不满 14 天')})")
    if summ.get("by_signal"):
        lines += ["", f"近 {summ['window_days']} 天的命中率(待复盘 {summ['pending']} 个):", "",
                  "| 信号 | 复盘 | 命中 | 命中率 | 提前天数中位数 |", "|---|---|---|---|---|"]
        for k, s in sorted(summ["by_signal"].items(), key=lambda kv: list(KINDS).index(kv[0]) if kv[0] in KINDS else 99):
            lines.append(f"| {KINDS.get(k, k)} | {s['checked']} | {s['hit']} | {s['hit'] / s['checked']:.0%} | "
                         f"{s['median_lead'] if s['median_lead'] is not None else '—'} |")
    elif summ.get("error"):
        lines.append(f"命中率:{summ['error']}")

    x, hf, gh, sm = b["x"], b["hf"], b["github"], b["sitemap"]
    lines += ["", "### 数据状态", ""]
    lines.append("- ① X:" + (x.get("error") or ("跳过" if x.get("skipped") else
                 f"{x['answered']}/{x['accounts']} 个账号,{x['posts']} 条帖子" + (",首次运行,只建词表" if x.get("first_run") else ""))))
    lines.append("- ① HF:" + (hf.get("error") or ("跳过" if hf.get("skipped") else
                 f"trending {hf['models']} 个模型" + (",首次运行,只建快照" if hf.get("first_run") else ""))))
    bo = b["breakout"]
    lines.append("- ② 爆发:" + (bo.get("error") or ("跳过" if bo.get("skipped") else
                 f"搜到 {bo['searched']} 个新仓库" + (",首次运行,没有昨天的星数" if bo.get("first_run") else ""))))
    lines.append(f"- ② GitHub:近 {signals.RECENT_DAYS} 天新建 {gh.get('repos_recent', '—')} 个仓库,"
                 f"基线 {gh.get('repos_baseline', '—')} 个 {gh.get('error', '')}")
    for site, s in sm.get("sites", {}).items():
        state = s.get("error") or ("首次运行,只建快照" if s.get("first_run") else f"{s['urls']} 个网址,新增 {s['new']}")
        lines.append(f"- ③ {site}:{state}")
    if sm.get("error") or sm.get("skipped"):
        lines.append(f"- ③ 竞品:{sm.get('error') or '跳过'}")
    if b.get("record", {}).get("error"):
        lines.append(f"- 记录候选词:{b['record']['error']}")
    lines.append(f"- AIsa 花费:{_cost(x, rev)}")
    return "\n".join(lines) + "\n"


def main() -> int:
    report, snaps = Path(sys.argv[1]), Path(sys.argv[2])
    flags = set(sys.argv[3:])
    blocks = {
        "x": run("x", lambda: source_signals.x_new(snaps), "--skip-x" in flags),
        "hf": run("hf", lambda: source_signals.hf_new(snaps), "--skip-hf" in flags),
        "breakout": run("breakout", lambda: breakout.breakouts(snaps), "--skip-breakout" in flags),
        "github": run("github", signals.github_surge, "--skip-db" in flags),
        "sitemap": run("sitemaps", lambda: sitemap_diff.diff(snaps), "--skip-sitemaps" in flags),
    }
    gsc = run("gsc", signals.gsc_new, "--skip-gsc" in flags)
    lead = leads(blocks)
    no_db = "--skip-db" in flags
    keep = [r for r in named(lead)[:SHOWN] if not r.get("page")]
    blocks["record"] = run("record", lambda: {"recorded": review.record(keep)}, no_db)
    rev = run("review", review.review, no_db or "--skip-review" in flags)
    summ = run("summary", review.summary, no_db)
    report.write_text(markdown(lead, blocks, gsc, rev, summ))
    report.with_suffix(".json").write_text(json.dumps({"leads": lead, **blocks, "gsc": gsc, "review": rev,
                                                      "summary": summ}, ensure_ascii=False, indent=1, default=str))
    print(report.read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
