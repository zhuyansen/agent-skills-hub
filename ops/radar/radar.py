"""New-term radar: one daily report of terms that are starting to surge.

  python ops/radar/radar.py <report.md> <snapshot-dir> [--skip-x] [--skip-hf] [--skip-breakout]
                            [--skip-appstore] [--skip-memes] [--skip-social] [--skip-db]
                            [--skip-review] [--skip-usecases]
  python ops/radar/radar.py <report.md> <snapshot-dir> --sources

The source signals (①) change by the hour, the rest by the day, so they run apart:
radar-source.yml every 8 hours with --sources (X, HF, the AI video trends and the new sites
people link; <report.md> is written
only when there is a name or an error, so quiet runs post nothing), and radar-daily.yml
once a day with --skip-x --skip-hf, its report listing the ① leads of the last day
from radar_leads.

Signals (see ops/gefei-seo-playbook.md §3), earliest first:
  ① X        names the labs and AI bloggers in sources.json said first (source_signals.x_new, AIsa)
  ① HF       models new to Hugging Face's trending top 50 (source_signals.hf_new)
  ① 梗       AI video trends people recreate (TikTok, Instagram, YouTube Shorts, X and TikTok's
             trending hashtags), with Jev's score for building a site or app for one now
             (memes.memes; about $0.02 a day through AIsa, plus the model and Jev)
  ① 社交新站 sites registered in the last 90 days that two or more people linked in X or
             Bluesky posts of the last 72 hours (social_sites.social_sites, with the source
             signals; at most 30 GoAnyAPI traffic tags a day, $0.06). In shadow mode while
             social_sites.SOCIAL_SHOW is off: kept in radar_leads for the review, shown only
             as one status line (record_shadow)
  ② breakout one new GitHub repo taking off on its own (breakout.breakouts)
  ② GitHub   terms that new repos in the catalog suddenly share (signals.github_surge). In shadow
             mode while signals.GITHUB_SHOW is off, like the new sites people link (shadow)
  ② 榜单     an app released in the last 30 days climbing the App Store charts in eight
             countries, the words it is sold on, how many copies already share them, and
             its Xiaohongshu and Douyin posts (appstore.apps; about $0.10 a day through AIsa)
Terms from ① and ② go to Jev with a few examples: is this the name of a specific new
product, model or technique, or a common word? Those that pass, and that no scenario
page covers yet, lead the report, and are kept in radar_leads; review.py checks them in
Google Trends 14 days later (⑤ as verification, not discovery) and the report ends with
the hit rate per signal. Writes <report.md> and a JSON copy beside it.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / "ops/jev-review")]
import appstore  # noqa: E402
import breakout  # noqa: E402
import memes  # noqa: E402
import review  # noqa: E402
import signals  # noqa: E402
import social_sites  # noqa: E402
import source_signals  # noqa: E402
import usecases  # noqa: E402

NAMED_MIN = 0.5
OTHER_TERMS = 15
SHOWN = 20
POSTS_SHOWN = 3   # posts quoted in full per term in the mail
NAMED = {"named_thing": {"type": "noul", "instructions": {
    "question": "Is `term` the name of a specific product, model, tool, company or technique, rather than a common word or a generic category?",
    "focus": "`examples` are repo names, descriptions, posts or page paths where it appeared. 'opus 5.5', 'hyperframes', "
             "'jev' are names; 'dashboard', 'voice notes', 'pdf' are not."}}}
# signal key -> label in the report, in the order of how early the signal comes
KINDS = {"x": "①X", "hf": "①HF", "meme": "①梗", "social": "①社交新站", "breakout": "②爆发", "appstore": "②榜单", "github": "②GitHub",
         "usecase": "通用词", "cosearch": "一起被搜", "watch": "观察词"}
# signals the radar no longer reads; the review still checks their old leads, and the hit-rate table names them so
RETIRED = {"sitemap": "③竞品(已停)", "newsite": "③新站(已停)"}
# what they kept in the daily snapshot dir, deleted so the Actions cache stops carrying it (toolify: about a million URLs)
RETIRED_SNAPSHOTS = (*(f"{site}.json.gz" for site in ("glama", "mcp.so", "skillsmp", "toolify", "lobehub-mcp",
                                                      "lobehub-skills", "lobehub-agents", "lobehub-blog")),
                     "new_sites.json.gz")
EARLY_NOTE = (f"提前命中 = Trends 在雷达第一次报出后至少 {review.EARLY_DAYS} 天才起涨;"
              "晚到 = 也起来了,但起涨在报出之前或当天")
# the ① leads the daily report lists from radar_leads; the new sites only once they are shown
SOURCE_KINDS = review.SOURCE_KINDS + (("social",) if social_sites.SOCIAL_SHOW else ())
# optional keys a lead takes from its signal's row: the picks read the first three, and
# radar_leads.evidence the last two (review.evidence), with a row's `evidence_posts`
CARRIED = ("what", "window", "checks", "meme", "site")


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
        if {"meme", "appstore"} & set(r["kinds"]):   # scored for opportunity already (memes.py, appstore.py)
            continue
        state = json.dumps({"term": r["term"], "examples": r.get("examples", [])[:3]}, ensure_ascii=False)
        try:
            r["named"] = float(jev.decisions(state, NAMED).answers["named_thing"].get("noul", 0.0))
        except Exception:  # noqa: BLE001 — no credit or a timeout: the report goes out without Jev's column
            return


def _merged(blocks: dict[str, dict]) -> list[dict]:
    """One row per term over the blocks' `terms`, each signal's row merged in (_merge)."""
    out: dict[str, dict] = {}
    for kind, block in blocks.items():
        for r in block.get("terms", []):
            row = out.setdefault(r["term"], {"term": r["term"], "kinds": [], "signals": [], "examples": [], "variants": [], "posts": []})
            _merge(row, kind, r)
    return list(out.values())


def _merge(row: dict, kind: str, r: dict) -> None:
    row["kinds"].append(kind)
    row["signals"].append(r.get("note") or f"{KINDS[kind]} {r['recent']} 处 (×{r['lift']})")
    row["examples"] += r.get("examples", [])
    row["posts"] += r.get("posts", [])
    row["variants"] += [v for v in r.get("variants", []) if v not in row["variants"]]
    if r.get("repo"):
        row["repo"] = r["repo"]
    if r.get("named") is not None:   # a meme's opportunity score (memes.py); judge() leaves these rows alone
        row["named"] = r["named"]
    row.update({k: r[k] for k in CARRIED if r.get(k)})
    row["evidence_posts"] = row.get("evidence_posts", []) + r.get("evidence_posts", [])
    if "described" in r:
        row["described"] = r["described"]


def shadow(block: dict, kind: str) -> dict:
    """A signal in shadow mode (signals.GITHUB_SHOW off for "github"): its terms leave the block for
    `shadow_leads`, the rows record_shadow() writes to radar_leads for the review, so they reach neither
    leads() and Jev nor the candidates, the picks or the keyword table, as social_sites.py does for
    the new sites people link."""
    block["shadow_leads"] = _merged({kind: {"terms": block.pop("terms", [])}})
    block["shadow"] = True
    return block


def leads(blocks: dict[str, dict]) -> list[dict]:
    """Terms from every discovery signal, merged; a term in several is the strongest lead."""
    rows = _merged(blocks)
    judge(rows)
    # Earliest signal first among equals: a name the labs said today beats a sitemap echo.
    first = {k: i for i, k in enumerate(KINDS)}
    # Unscored rows (a meme's search term, or no Jev today) count as names, as in named().
    rows.sort(key=lambda r: (-(r.get("named", 1.0) >= NAMED_MIN), -len(r["kinds"]),
                             min(first[k] for k in r["kinds"]), -r.get("named", 0)))
    return rows


def named(lead: list[dict]) -> list[dict]:
    """Without Jev's column (no key, no credit) every term counts; with it, only names."""
    return [r for r in lead if r.get("named", 1.0) >= NAMED_MIN]


def _cost(*blocks: dict) -> str:
    micros = sum(int(b.get("cost_micros") or 0) for b in blocks)
    return f"${micros / 1e6:.3f}"


PICKS = 3
MEME_HOW = "做法:单功能站(上传照片 → 生成你的版本),按次卖。"


def picks(b: dict[str, dict], today: date | None = None) -> list[str]:
    """The top of every mail: at most PICKS terms to build for today, each with why, how
    long it has, and what to make. Everything below it is the evidence. The mail had
    grown to a dozen sections and no answer (2026-10-19: "不知道做哪个词").

    Order: AI video trends over Jev's bar first, because they are over in about four days,
    and only those that first showed less than memes.PEAK_DAYS ago (10-20: two of three
    picks were weeks old and the mail did not say when they appeared); then keywords the
    table marked prioritize (measured demand, still rising); then new apps over Jev's bar
    whose search words are not crowded yet. The trends left out are listed with why."""
    today = today or date.today()
    uc = {r["phrase"]: r for r in b.get("usecases", {}).get("rows", [])}
    meme_out, held = _meme_picks(b, uc, today)
    out = meme_out + _usecase_picks(uc) + _app_picks(b)
    lines = ([f"{i}. {line}" for i, line in enumerate(out[:PICKS], 1)] if out
             else ["**今天没有值得动手的词。** 下面的明细扫一眼即可。"])
    if len(out) > PICKS:
        lines += ["", f"(另有 {len(out) - PICKS} 个够格的,见下面明细)"]
    if held:
        lines += ["", "没放进来的 AI 视频梗:" + "、".join(held)]
    if meme_out or held:
        lines += ["", memes.AGE_NOTE]
    return lines


def _meme_picks(b: dict[str, dict], uc: dict[str, dict], today: date) -> tuple[list[str], list[str]]:
    """Trends over Jev's bar still before their peak, and the others with why they are not."""
    rows = b.get("meme", {}).get("terms") or [r for r in b.get("recent_sources", {}).get("rows", [])
                                              if "meme" in r.get("kinds", [])]
    out, held = [], []
    for r in sorted(rows, key=lambda r: -(r.get("named") or 0)):
        if (r.get("named") or 0) < memes.OPPORTUNITY_MIN:
            continue
        t = uc.get(r["term"], {})
        info = memes.read_note(r.get("note", ""), today)
        info["checks"] = r.get("checks") or info["checks"]
        why = _meme_held(info, t, today)
        if why:
            held.append(f"{r['term']}({why})")
        else:
            out.append(_meme_line(r, info, t, today))
    return out, held


def _meme_held(info: dict, t: dict, today: date) -> str:
    """Why a trend over Jev's bar is not a pick today; empty when it is one."""
    if t.get("now") == "fading":   # Trends already says it is falling, whatever the posts say
        return "Trends 在回落"
    if "已经挤了" in info["checks"]:   # four or more tool sites in Google's top 10 (meme_checks.CROWDED)
        return "Google 前 10 已经挤了"
    if info["earliest"] is None:
        return "只在 YouTube 出现,看不出日期" if info["where"] == "YouTube" else "没有记下出现日期"
    if (today - info["earliest"]).days >= memes.PEAK_DAYS:
        return memes.age_text(info["earliest"], info["edge"], today) + ",过了见顶期"
    return ""


def _meme_line(r: dict, info: dict, t: dict, today: date) -> str:
    left = memes.PEAK_DAYS - (today - info["earliest"]).days
    demand = f",Google 估算日搜 {t['per_day']},{usecases.NOW_ZH.get(t.get('now'), '')}" if t.get("per_day") else ""
    what = r.get("what") or info["what"]
    return (f"**{r['term']}**:AI 视频梗{',' + what if what else ''}。  \n"
            f"{memes.age_text(info['earliest'], info['edge'], today)};{info['where']} {info['posts']} 帖,"
            f"Jev 机会 {r['named']:.2f}{demand}。  \n"
            + (f"{info['checks']}。  \n" if info["checks"] else "")
            + f"窗口:梗约 {memes.PEAK_DAYS} 天见顶,还剩约 {left} 天,**今天上线**。{MEME_HOW}")


def _usecase_picks(uc: dict[str, dict]) -> list[str]:
    out = []
    for r in (x for x in uc.values() if x.get("decision") == "prioritize"):
        src = f",来自 {', '.join(r['names'])}" if r.get("names") else ""
        out.append(f"**{r['phrase']}**:{'通用词' if r['kind'] == 'generic' else '新名字'},估算日搜 {r.get('per_day', '?')},"
                   f"{usecases.NOW_ZH.get(r.get('now'), '')}{src}。  \n做法:工具页或场景页,标题对准这个词。")
    return out


def _app_picks(b: dict[str, dict]) -> list[str]:
    rows = b.get("appstore", {}).get("terms") or [r for r in b.get("recent_sources", {}).get("rows", [])
                                                  if "appstore" in r.get("kinds", [])]
    out = []
    for r in sorted(rows, key=lambda r: -(r.get("named") or 0)):
        if (r.get("named") or 0) < memes.OPPORTUNITY_MIN or r.get("window") == "crowded" or "已经挤了" in r.get("note", ""):
            continue
        # an app whose name has no descriptive half sells on its own name: nothing to build on (10-20)
        if r.get("described") is False or "无卖点词" in r.get("note", ""):
            continue
        # a business's own app (a gym chain's members app) or one city's: no need to copy (10-20)
        if r.get("tied") or any(m in r.get("note", "") for m in appstore.TIED_ZH.values()):
            continue
        out.append(f"**{r['term']}**:{r.get('what') or r.get('note', '')},Jev 机会 {r['named']:.2f}。  \n"
                   f"做法:同类应用或网站,名字和标题用它的卖点词。")
    return out


def markdown(lead: list[dict], b: dict[str, dict], rev: dict, summ: dict) -> str:
    lines = ["## 今天做哪个词", "", *picks(b), "", "---", "", "## 明细(上面每个词的依据,不用每天细看)",
             *usecases.table(b.get("usecases", {"skipped": True})), "",
             "### 候选新词(Jev 判为专有名词、且还没有对应场景页的排前面)", "",
             "| 词 | 信号 | Jev | 已有页面 | 搜索变体 | 例子 |", "|---|---|---|---|---|---|"]
    names_ = named(lead)
    for r in names_[:SHOWN]:
        ex = " / ".join(e[:50] for e in r["examples"][:2]).replace("|", "/").replace("\n", " ")
        score = f"{r['named']:.2f}" if "named" in r else "—"
        lines.append(f"| **{r['term']}** | {_signals_cell(r)} | {score} | {r.get('page') or '无'} | "
                     f"{', '.join(r['variants'][1:]) or '—'} | {ex} |")
    rest = [r["term"] for r in lead if r not in names_][:OTHER_TERMS]
    if rest:
        lines += ["", "其他上升词(Jev 判为普通词):" + "、".join(rest)]

    recent = b.get("recent_sources", {})
    if not recent.get("skipped"):
        lines += ["", "### ① 近 24 小时的源头新词(每 8 小时任务记下的)", ""]
        rows = recent.get("rows") or []
        lines += ([f"- **{r['term']}**:{r['note']}" for r in rows] if rows
                  else [f"无({recent.get('error') or '没有新名字'})"])
    lines += memes.section(b.get("meme", {"skipped": True}))
    lines += ["", f"### ② 单仓库爆发(近 {breakout.WINDOW_DAYS} 天新建;{breakout.WINDOW_DAYS + 1}–{breakout.LATE_DAYS} 天的要 "
                  f"≥{breakout.LATE_MIN_STARS} 星;按每天涨星排;🆕 = 今天第一次达标,进上面的候选词)", ""]
    repos = b["breakout"].get("repos") or []
    if repos:
        lines += ["| 仓库 | ★ | 均/天 | 比昨天 | 天数 | 简介 |", "|---|---|---|---|---|---|"]
        lines += [f"| {'🆕 ' if r.get('new') else ''}[{r['repo']}](https://github.com/{r['repo']}) | {r['stars']} | {r['velocity']} | "
                  f"{'+' + str(r['delta']) if r['delta'] is not None else '—'} | {r['age_days']} | "
                  f"{r['description'][:60].replace('|', '/')} |" for r in repos]
    else:
        lines.append(f"无({b['breakout'].get('error') or ('跳过' if b['breakout'].get('skipped') else '没有爆发仓库')})")
    lines += appstore.section(b.get("appstore", {"skipped": True}))

    lines += review_lines(rev, summ)

    x, hf, gh = b["x"], b["hf"], b["github"]
    lines += ["", "### 数据状态", ""]
    if not (x.get("skipped") and hf.get("skipped")):
        lines += _source_status(x, hf)
    if not b.get("social", {"skipped": True}).get("skipped"):
        lines.append(social_sites.status(b["social"]))
    bo = b["breakout"]
    lines += _rest_status(bo, gh, b)
    lines.append(f"- AIsa 花费:{_cost(x, rev, b.get('usecases', {}), b.get('appstore', {}), b.get('meme', {}))}(新词表的模型调用另计)")
    return "\n".join(lines) + "\n"


def review_lines(rev: dict, summ: dict) -> list[str]:
    """⑤: today's verdicts as counts with only the early hits by name, then each signal's tally."""
    lines = ["", "### ⑤ 复盘(14 天前报出的词,在 Google Trends 里起没起来)", "", *_checked_lines(rev)]
    if summ.get("by_signal"):
        return lines + _tally_lines(summ)
    return lines + ([f"命中率:{summ['error']}"] if summ.get("error") else [])


def _checked_lines(rev: dict) -> list[str]:
    checked = rev.get("checked") or []
    if not checked:
        return [f"今天没有到期的词({rev.get('error') or ('跳过' if rev.get('skipped') else '最早报出的词还不满 14 天')})"]
    said = [review.outcome(c["verdict"], c["lead_days"]) for c in checked]
    n = Counter(said)
    early = [f"- 提前命中 **{c['term']}**:{c['first_seen']} 报出,提前 {c['lead_days']} 天"
             for c, o in zip(checked, said) if o == "early"]
    # the blank line: Python-Markdown (notify.py) reads a list right under a paragraph as more of the paragraph
    return ([f"今天复盘 {len(checked)} 个:提前命中 {n['early']},晚到 {n['late']},没起来 {n['miss']},没数据 {n['no_data']}。"]
            + (["", *early] if early else []))


def _tally_lines(summ: dict) -> list[str]:
    order = [*KINDS, *RETIRED]
    lines = ["", f"近 {summ['window_days']} 天各信号(待复盘 {summ['pending']} 个;{EARLY_NOTE}):", "",
             "| 信号 | 复盘 | 提前命中 | 晚到 | 没起来 | 没数据 | 提前命中率 | 提前天数中位数 |", "|---|---|---|---|---|---|---|---|"]
    for k, s in sorted(summ["by_signal"].items(), key=lambda kv: order.index(kv[0]) if kv[0] in order else len(order)):
        median = s["median_lead"] if s["median_lead"] is not None else "—"
        lines.append(f"| {KINDS.get(k) or RETIRED.get(k, k)} | {s['checked']} | {s['early']} | {s['late']} | {s['miss']} | "
                     f"{s['no_data']} | {s['early'] / s['checked']:.0%} | {median} |")
    return lines


def _source_status(x: dict, hf: dict) -> list[str]:
    return ["- ① X:" + (x.get("error") or ("跳过" if x.get("skipped") else
                 f"{x['answered']}/{x['accounts']} 个账号,{x['posts']} 条帖子" + (",首次运行,只建词表" if x.get("first_run") else ""))),
            "- ① HF:" + (hf.get("error") or ("跳过" if hf.get("skipped") else
                 f"trending {hf['models']} 个模型" + (",首次运行,只建快照" if hf.get("first_run") else "")))]


def _rest_status(bo: dict, gh: dict, b: dict) -> list[str]:
    lines = []
    lines.append("- ② 爆发:" + (bo.get("error") or ("跳过" if bo.get("skipped") else
                 f"搜到 {bo['searched']} 个新仓库(其中 {breakout.WINDOW_DAYS + 1}–{breakout.LATE_DAYS} 天的 {bo.get('searched_late', 0)} 个)"
                 + (",首次运行,没有昨天的星数" if bo.get("first_run") else "")
                 + (f",{bo['late_error']}" if bo.get("late_error") else ""))))
    lines += _meme_app_status(b)
    lines.append(github_status(gh))
    if b.get("record", {}).get("error"):
        lines.append(f"- 记录候选词:{b['record']['error']}")
    return lines


def github_status(gh: dict) -> str:
    """② GitHub's line; in shadow mode the only trace of the words new repos share."""
    label = "- ② GitHub 共用词" + ("(影子模式,只记录不展示)" if gh.get("shadow") else "")
    if gh.get("skipped") or gh.get("error"):
        return f"{label}:{gh.get('error') or '跳过'}"
    line = f"{label}:近 {signals.RECENT_DAYS} 天新建 {gh['repos_recent']} 个仓库,基线 {gh['repos_baseline']} 个"
    if not gh.get("shadow"):
        return line
    return line + f",{len(gh['shadow_leads'])} 个上升词" + _shadow_recorded(gh.get("recorded") or {})


def _shadow_recorded(rec: dict) -> str:
    """What record_shadow() did, for a shadow signal's line; '' when there was nothing to record."""
    if rec.get("error") or rec.get("skipped"):
        return f",没记录({rec.get('error') or '跳过数据库'})"
    merged = f",{rec['merged']} 个已是别的信号的线索,只补了证据" if rec.get("merged") else ""
    return f",已记录 {rec['recorded']} 个{merged}" if "recorded" in rec else ""


def _meme_app_status(b: dict) -> list[str]:
    """The daily run leaves trends and charts to the 8-hourly source job: say so, not '跳过'."""
    elsewhere = not b.get("recent_sources", {"skipped": True}).get("skipped")
    out = []
    for key, label, mod in (("meme", "① 梗", memes), ("appstore", "② 榜单", appstore)):
        block = b.get(key, {"skipped": True})
        out.append(f"- {label}:在每 8 小时的源头任务里跑,结果见上面「① 近 24 小时」" if elsewhere and block.get("skipped")
                   else mod.status(block))
    return out


def _signals_cell(r: dict) -> str:
    """A lead's signals for a table whose 例子 column already says what a trend is."""
    return "; ".join(s.split("｜" + memes.WHAT)[0] for s in r["signals"])


def _clip(text: str, n: int) -> str:
    """Cut at a word boundary with an ellipsis, not mid-word."""
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0]
    return (cut if len(cut) > n // 2 else text[:n]) + "…"


def posts_markdown(rows: list[dict]) -> list[str]:
    """Each term's posts in full, with a link: what was said and where, without opening X."""
    lines = []
    for r in rows:
        for p in r.get("posts", [])[:POSTS_SHOWN]:
            if not lines:
                lines += ["", "### 推文原文", ""]
            link = f" · [原推]({p['url']})" if p.get("url") else ""
            lines.append(f"- **{r['term']}** · @{p['account']} ♥{p['likes']}{link}  \n  {p['text']}")
    return lines


def sources_markdown(lead: list[dict], b: dict[str, dict]) -> str:
    lines = ["## 现在就能做", "", *picks(b), "", "---", "", "## 明细:新词雷达 · ① 源头(每 8 小时)", "", "| 词 | 信号 | Jev | 已有页面 | 例子 |", "|---|---|---|---|---|"]
    for r in named(lead)[:SHOWN]:
        ex = "<br>".join(_clip(e, 60) for e in r["examples"][:2]).replace("|", "/").replace("\n", " ")
        score = f"{r['named']:.2f}" if "named" in r else "—"
        lines.append(f"| **{r['term']}** | {_signals_cell(r)} | {score} | {r.get('page') or '无'} | {ex} |")
    lines += posts_markdown(named(lead)[:SHOWN])
    lines += memes.section(b.get("meme", {"skipped": True}))
    lines += appstore.section(b.get("appstore", {"skipped": True}))
    lines += [""] + [mod.status(b[k]) for k, mod in STATUS_LINES if not b.get(k, {"skipped": True}).get("skipped")]
    for key, label in (("x", "① X"), ("hf", "① HF")):
        if b[key].get("error"):
            lines.append(f"\n- {label}:{b[key]['error']}")
    if b.get("record", {}).get("error"):
        lines.append(f"- 记录候选词:{b['record']['error']}")
    lines.append(f"\nAIsa 花费:{_cost(b['x'], b.get('meme', {}), b.get('appstore', {}))}")
    return "\n".join(lines) + "\n"


# signals whose status line the source run prints; social's is all it shows in shadow mode
STATUS_LINES = (("meme", memes), ("appstore", appstore), ("social", social_sites))


def record_shadow(block: dict, no_db: bool) -> None:
    """Shadow mode (social_sites.SOCIAL_SHOW, signals.GITHUB_SHOW off): a signal's leads go straight
    into radar_leads, past Jev and the mail, so the review can measure them. record_new() leaves a
    lead another signal holds as it is (the reports show its last note), adding only the
    evidence. The outcome goes on the block, for its status line."""
    rows = block.get("shadow_leads") or []
    if rows:
        block["recorded"] = run("record shadow", lambda: review.record_new(rows), no_db)


def _mail_errors(blocks: dict[str, dict]) -> bool:
    """A failed signal sends the source mail, except the new sites in shadow mode: not in the mail."""
    return any(b.get("error") for k, b in blocks.items() if social_sites.SOCIAL_SHOW or k != "social")


def sources_main(report: Path, snaps: Path, flags: set[str]) -> int:
    blocks = {"x": run("x", lambda: source_signals.x_new(snaps), "--skip-x" in flags),
              "hf": run("hf", lambda: source_signals.hf_new(snaps), "--skip-hf" in flags),
              # a trend peaks in about four days: read every 8 hours, not once a day (memes.py)
              "meme": run("meme", lambda: memes.memes(snaps), "--skip-memes" in flags),
              # new apps on the charts move by the hour too (Apolu refreshes hourly)
              "appstore": run("appstore", lambda: appstore.apps(snaps), "--skip-appstore" in flags)}
    # new sites two or more people link, in the X posts just read and on Bluesky (social_sites.py)
    blocks["social"] = run("social", lambda: social_sites.social_sites(snaps, blocks["x"]), "--skip-social" in flags)
    lead = leads(blocks)
    keep = [r for r in named(lead)[:SHOWN] if not r.get("page")]
    blocks["record"] = run("record", lambda: {"recorded": review.record(keep)}, "--skip-db" in flags)
    record_shadow(blocks["social"], "--skip-db" in flags)
    if named(lead) or _mail_errors(blocks):
        report.write_text(sources_markdown(lead, blocks))
        print(report.read_text())
    else:
        print("① 没有新名字:" + "; ".join(f"{k} {v.get('posts', v.get('models', '—'))}" for k, v in blocks.items() if k != "record"))
        for k, mod in STATUS_LINES:
            if not blocks[k].get("skipped"):
                print(mod.status(blocks[k]))
    return 0


def drop_retired(snaps: Path) -> None:
    """Deletes what the signals the radar no longer reads kept in the snapshot dir (RETIRED_SNAPSHOTS)."""
    for name in RETIRED_SNAPSHOTS:
        (snaps / name).unlink(missing_ok=True)


def main() -> int:
    report, snaps = Path(sys.argv[1]), Path(sys.argv[2])
    flags = set(sys.argv[3:])
    return (sources_main if "--sources" in flags else daily_main)(report, snaps, flags)


def daily_main(report: Path, snaps: Path, flags: set[str]) -> int:
    no_db = "--skip-db" in flags
    drop_retired(snaps)
    blocks = daily_blocks(snaps, flags)
    lead = leads(blocks)
    keep = [r for r in named(lead)[:SHOWN] if not r.get("page")]
    blocks["record"] = run("record", lambda: {"recorded": review.record(keep)}, no_db)
    for key in ("social", "github"):
        record_shadow(blocks[key], no_db)
    rev = run("review", review.review, no_db or "--skip-review" in flags)
    summ = run("summary", review.summary, no_db)
    blocks["recent_sources"] = run("recent_sources", lambda: {"rows": review.recent_sources(kinds=SOURCE_KINDS)},
                                   no_db or "--skip-x" not in flags)
    keywords(blocks, lead, keep, snaps, flags)
    report.write_text(markdown(lead, blocks, rev, summ))
    report.with_suffix(".json").write_text(json.dumps({"leads": lead, **blocks, "review": rev,
                                                      "summary": summ}, ensure_ascii=False, indent=1, default=str))
    print(report.read_text())
    return 0


def daily_blocks(snaps: Path, flags: set[str]) -> dict[str, dict]:
    """The daily run's signals; radar-daily.yml leaves the source signals to the 8-hourly run (--skip-x ...)."""
    blocks = {
        "x": run("x", lambda: source_signals.x_new(snaps), "--skip-x" in flags),
        "hf": run("hf", lambda: source_signals.hf_new(snaps), "--skip-hf" in flags),
        "meme": run("meme", lambda: memes.memes(snaps), "--skip-memes" in flags),
        "breakout": run("breakout", lambda: breakout.breakouts(snaps), "--skip-breakout" in flags),
        "appstore": run("appstore", lambda: appstore.apps(snaps), "--skip-appstore" in flags),
        "github": run("github", signals.github_surge, "--skip-db" in flags),
    }
    if not signals.GITHUB_SHOW:
        shadow(blocks["github"], "github")
    # it reads the X posts, so the daily job (--skip-x) leaves it to the source job too
    blocks["social"] = run("social", lambda: social_sites.social_sites(snaps, blocks["x"]),
                           "--skip-x" in flags or "--skip-social" in flags)
    return blocks


def keywords(blocks: dict[str, dict], lead: list[dict], keep: list[dict], snaps: Path, flags: set[str]) -> None:
    """The generic terms behind the day's names (usecases.py): only names from the signals that report
    things (X, HF, AI video trends, apps, breakouts) with a high name score; see names_to_read. Read twice
    each (today and three days on); about $0.15 a day. Its leads and each name's reading go to radar_leads."""
    no_db = "--skip-db" in flags
    names = usecases.names_to_read(keep, blocks["recent_sources"].get("rows", []))
    repos = {r["term"]: r["repo"] for r in lead if r.get("repo")}
    blocks["usecases"] = run("usecases", lambda: usecases.run(snaps, list(dict.fromkeys(names)), repos), "--skip-usecases" in flags)
    run("record usecases", lambda: {"recorded": review.record(usecases.leads(blocks["usecases"]))}, no_db)
    # what the table found for each name, into that name's evidence (radar_leads.evidence)
    run("keyword evidence", lambda: {"added": review.add_evidence(usecases.name_evidence(blocks["usecases"]))}, no_db)


if __name__ == "__main__":
    sys.exit(main())
