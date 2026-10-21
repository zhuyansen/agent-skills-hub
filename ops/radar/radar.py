"""New-term radar: one daily report of terms that are starting to surge.

  python ops/radar/radar.py <report.md> <snapshot-dir> [--skip-x] [--skip-hf] [--skip-breakout]
                            [--skip-appstore] [--skip-memes] [--skip-social] [--skip-db]
                            [--skip-review] [--skip-usecases] [--sent-picks=<source snapshot>/sent_picks.json]
  python ops/radar/radar.py <report.md> <snapshot-dir> --sources

The source signals (①) change by the hour, the rest by the day, so they run apart, and each
mail shows a term once:
  radar-source.yml, every 8 hours with --sources: HF, the AI video trends, the App Store charts
    and the new sites people link, and X once a day (x_block). Its full report, <report.md>,
    goes to the run's summary only, written when there is a name or an error. The mail,
    <report>.picks.md, holds only the picks no earlier 8-hourly mail sent (mail_new_picks);
    with none, or with only errors, there is no mail.
  radar-daily.yml, once a day with --skip-x --skip-hf --skip-memes --skip-appstore: one mail.
    Its picks leave out those the 8-hourly mails sent since yesterday (--sent-picks), and its
    ① lists the last day's source leads from radar_leads that no earlier daily, no pick mail
    and no other part of the mail showed (daily_view, LISTED).

Signals, earliest first:
  ① X        names the labs and AI bloggers in sources.json said first (source_signals.x_new, AIsa;
             about once a day, source_signals.X_EVERY_HOURS)
  ① HF       models new to Hugging Face's trending top 50 (source_signals.hf_new)
  ① 梗       AI video trends people recreate (TikTok, Instagram, YouTube Shorts, X and TikTok's
             trending hashtags), with Jev's score for building a site or app for one now
             (memes.memes; about $0.03 a day through AIsa, plus the model and Jev)
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
each signal's early hits: Trends rose a day or more after the radar first saw the term.
Writes <report.md> and a JSON copy beside it.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
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
# signals with a section of their own in the daily mail (② 单仓爆发 lists every 🆕 repo): their
# leads stay out of its candidate table, which had become a copy of that section (10-21)
OWN_SECTION = frozenset({"breakout"})
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
TRENDS_LINK = "https://trends.google.com/trends/explore?date=today%203-m&q="


def picks(b: dict[str, dict], today: date | None = None, sent: frozenset[str] | set[str] = frozenset()) -> list[str]:
    """The top of every mail: at most PICKS terms to build for today, each with why, how
    long it has, what to make and one link. Everything below it is the evidence. The mail had
    grown to a dozen sections and no answer (2026-10-19: "不知道做哪个词"). Picks in `sent`,
    mailed already, are left out (pick_lines)."""
    items, held = pick_items(b, today or date.today())
    return pick_lines([p for p in items if p["term"] not in sent], [p["term"] for p in items if p["term"] in sent], held)


def pick_items(b: dict[str, dict], today: date) -> tuple[list[dict], list[tuple[str, str]]]:
    """Every pick as {"term", "kind", "text"}, and the AI video trends over Jev's bar left out, as (term, why).

    Order: AI video trends over Jev's bar first, because they are over in about four days,
    and only those that first showed less than memes.PEAK_DAYS ago (10-20: two of three
    picks were weeks old and the mail did not say when they appeared); then keywords the
    table marked prioritize (measured demand, still rising); then new apps over Jev's bar
    whose search words are not crowded yet."""
    uc = {r["phrase"]: r for r in b.get("usecases", {}).get("rows", [])}
    meme_out, held = _meme_picks(b, uc, today)
    return meme_out + _usecase_picks(uc) + _app_picks(b), held


def pick_lines(fresh: list[dict], sent: list[str], held: list[tuple[str, str]]) -> list[str]:
    """The picks section: the picks not mailed yet, or, when every pick was (`sent`), one line naming them;
    then the trends left out, with why."""
    if fresh:
        lines = [f"{i}. {p['text']}" for i, p in enumerate(fresh[:PICKS], 1)]
        lines += ["", f"(另有 {len(fresh) - PICKS} 个够格的,见下面明细)"] if len(fresh) > PICKS else []
    else:
        lines = [f"今天够格的词都已在每 8 小时的邮件里发过:{'、'.join(sent)}。" if sent
                 else "**今天没有值得动手的词。** 下面的明细扫一眼即可。"]
    if held:
        lines += ["", "没放进来的 AI 视频梗:" + "、".join(f"{t}({why})" for t, why in held)]
    if held or any(p["kind"] == "meme" for p in fresh):
        lines += ["", memes.AGE_NOTE]
    return lines


def _link(label: str, url: str) -> str:
    """A pick's one link, on a line of its own; '' without a URL."""
    return f"  \n[{label}]({url})" if url else ""


def _meme_picks(b: dict[str, dict], uc: dict[str, dict], today: date) -> tuple[list[dict], list[tuple[str, str]]]:
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
            held.append((r["term"], why))
        else:
            out.append({"term": r["term"], "kind": "meme", "text": _meme_line(r, info, t, today)})
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
    top = next((p["url"] for p in r.get("posts", []) if p.get("url")), "")   # the most-liked post (memes.py)
    return (f"**{r['term']}**:AI 视频梗{',' + what if what else ''}。  \n"
            f"{memes.age_text(info['earliest'], info['edge'], today)};{info['where']} {info['posts']} 帖,"
            f"Jev 机会 {r['named']:.2f}{demand}。  \n"
            + (f"{info['checks']}。  \n" if info["checks"] else "")
            + f"窗口:梗约 {memes.PEAK_DAYS} 天见顶,还剩约 {left} 天,**今天上线**。{MEME_HOW}" + _link("最热一条", top))


def _usecase_picks(uc: dict[str, dict]) -> list[dict]:
    out = []
    for r in (x for x in uc.values() if x.get("decision") == "prioritize"):
        src = f",来自 {', '.join(r['names'])}" if r.get("names") else ""
        out.append({"term": r["phrase"], "kind": "usecase", "text": (
            f"**{r['phrase']}**:{'通用词' if r['kind'] == 'generic' else '新名字'},估算日搜 {r.get('per_day', '?')},"
            f"{usecases.NOW_ZH.get(r.get('now'), '')}{src}。  \n做法:工具页或场景页,标题对准这个词。"
            + _link("Google Trends", TRENDS_LINK + urllib.parse.quote(r["phrase"])))})
    return out


def _app_picks(b: dict[str, dict]) -> list[dict]:
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
        out.append({"term": r["term"], "kind": "app", "text": f"**{r['term']}**:{r.get('what') or r.get('note', '')},"
                    f"Jev 机会 {r['named']:.2f}。  \n做法:同类应用或网站,名字和标题用它的卖点词。" + _link("应用页", r.get("link", ""))})
    return out


# --- what each mail has already shown --------------------------------------------------------

SENT = "sent_picks.json"             # source snapshot dir: {term: when, UTC} of the picks the 8-hourly mails sent
SENT_NEXT = "sent_picks.next.json"   # that with this run's new picks; radar-source.yml moves it to SENT once mailed
PICK_MAIL = ".picks.md"              # the 8-hourly mail, <report>.picks.md, written only when a pick is new
LISTED = "listed.json"               # daily snapshot dir: {term: day} of the source leads a daily mail showed
MEMORY_DAYS = 14                     # how long a term mailed or listed stays out of the next mails
SENT_DAILY_DAYS = 1                  # the daily leaves out picks mailed since yesterday: the days recent_sources reads


def memory(path: Path) -> dict[str, str]:
    """{term: when} from one of the mail memories (SENT, LISTED); empty when it is missing or unreadable."""
    try:
        held = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return held if isinstance(held, dict) else {}


def remember(held: dict[str, str], terms: list[str], when: str, today: date) -> dict[str, str]:
    """`held` with `terms` added at `when` (a term held keeps its first date), the last MEMORY_DAYS kept."""
    cut = (today - timedelta(days=MEMORY_DAYS)).isoformat()
    out = {t: at for t, at in held.items() if str(at)[:10] >= cut}
    return out | {t: out.get(t, when) for t in terms}


def pick_mail(items: list[dict]) -> str:
    """The 8-hourly mail: the new picks and nothing else; radar-source.yml adds the run's link."""
    return "\n".join(f"{i}. {p['text']}" for i, p in enumerate(items, 1)) + "\n"


def mail_new_picks(report: Path, snaps: Path, blocks: dict[str, dict], now: datetime | None = None) -> list[dict]:
    """The picks no 8-hourly mail sent in the last MEMORY_DAYS (SENT), as <report>.picks.md for radar-source.yml
    to mail, with the memory that adds them staged as SENT_NEXT: the workflow moves it to SENT only once the
    mail is sent, so a mail that failed is tried again by the next run. No new pick: no file and no mail."""
    now = now or datetime.now(timezone.utc)
    mail = report.with_suffix(PICK_MAIL)
    for stale in (mail, snaps / SENT_NEXT):
        stale.unlink(missing_ok=True)
    sent = memory(snaps / SENT)
    new = [p for p in pick_items(blocks, now.date())[0] if p["term"] not in sent]
    if new:
        mail.write_text(pick_mail(new))
        snaps.mkdir(parents=True, exist_ok=True)
        staged = remember(sent, [p["term"] for p in new], now.isoformat(timespec="minutes"), now.date())
        (snaps / SENT_NEXT).write_text(json.dumps(staged, ensure_ascii=False, indent=1))
    return new


def option(flags: set[str], name: str) -> str:
    """The value of a --name=value flag; '' without one."""
    return next((f.split("=", 1)[1] for f in flags if f.startswith(name + "=")), "")


def sent_lately(flags: set[str], today: date) -> set[str]:
    """The picks the 8-hourly mails sent since yesterday (SENT_DAILY_DAYS), read from the source snapshot that
    radar-daily.yml restores (--sent-picks=<its SENT>); none without the flag."""
    path = option(flags, "--sent-picks")
    since = (today - timedelta(days=SENT_DAILY_DAYS)).isoformat()
    return {t for t, at in memory(Path(path)).items() if str(at)[:10] >= since} if path else set()


def daily_view(b: dict[str, dict], today: date, sent: set[str], listed: set[str]) -> dict:
    """What the daily mail shows of the picks and the source leads, each term once: the picks no 8-hourly
    mail sent, the trends held back, and in ① the last day's source leads that no earlier daily (`listed`),
    no 8-hourly pick mail, nothing above and no 🆕 repo of ② 单仓爆发 shows. `shown` is what LISTED keeps."""
    items, held = pick_items(b, today)
    fresh = [p for p in items if p["term"] not in sent]
    mailed = [p["term"] for p in items if p["term"] in sent]
    above = {p["term"] for p in fresh[:PICKS]} | {t for t, _ in held} | set(mailed)
    elsewhere = above | listed | {t["term"] for t in b["breakout"].get("terms", [])}
    rows = b.get("recent_sources", {}).get("rows") or []
    recent = [r for r in rows if r["term"] not in elsewhere]
    return {"fresh": fresh, "sent": mailed, "held": held, "recent": recent,
            "dropped": len(rows) - len(recent), "shown": above | {r["term"] for r in rows}}


def save_listed(snaps: Path, shown: set[str], today: date) -> None:
    """The source leads this daily mail showed, kept MEMORY_DAYS so that the next dailies do not list them again."""
    snaps.mkdir(parents=True, exist_ok=True)
    held = remember(memory(snaps / LISTED), sorted(shown), today.isoformat(), today)
    (snaps / LISTED).write_text(json.dumps(held, ensure_ascii=False, indent=1))


def markdown(lead: list[dict], b: dict[str, dict], view: dict) -> str:
    """The daily mail (radar-daily.yml sends exactly one): what to build, then the evidence. `view` (daily_view)
    says which picks and source leads it shows."""
    lines = ["## 今天做哪个词", "", *pick_lines(view["fresh"], view["sent"], view["held"]), "", "---", "",
             "## 明细(上面每个词的依据,不用每天细看)", *usecases.table(b.get("usecases", {"skipped": True})),
             *candidate_lines(lead), *recent_lines(b.get("recent_sources", {}), view),
             *memes.section(b.get("meme", {"skipped": True})), *breakout_lines(b["breakout"]),
             *appstore.section(b.get("appstore", {"skipped": True})),
             *review_lines(b.get("review", {}), b.get("summary", {})), *status_lines(b)]
    return "\n".join(lines) + "\n"


def candidate_lines(lead: list[dict]) -> list[str]:
    """The candidate table, for the leads no section of their own lists (OWN_SECTION); none, no table."""
    rows = [r for r in lead if not set(r["kinds"]) <= OWN_SECTION]
    names_ = named(rows)
    rest = [r["term"] for r in rows if r not in names_][:OTHER_TERMS]
    if not (names_ or rest):
        return []
    lines = ["", "### 候选新词(Jev 判为专有名词、且还没有对应场景页的排前面)", "",
             "| 词 | 信号 | Jev | 已有页面 | 搜索变体 | 例子 |", "|---|---|---|---|---|---|"]
    for r in names_[:SHOWN]:
        ex = " / ".join(e[:50] for e in r["examples"][:2]).replace("|", "/").replace("\n", " ")
        score = f"{r['named']:.2f}" if "named" in r else "—"
        lines.append(f"| **{r['term']}** | {_signals_cell(r)} | {score} | {r.get('page') or '无'} | "
                     f"{', '.join(r['variants'][1:]) or '—'} | {ex} |")
    return lines + (["", "其他上升词(Jev 判为普通词):" + "、".join(rest)] if rest else [])


def recent_lines(recent: dict, view: dict) -> list[str]:
    """① in the daily mail, the one place the source leads show: the last day's leads, less those an
    earlier daily or another part of this mail already showed (daily_view)."""
    if recent.get("skipped"):
        return []
    lines = ["", "### ① 近 24 小时的源头新词(每 8 小时任务记下的;之前的日报、可做词邮件和本封别处列过的不再列)", ""]
    if view["recent"]:
        return lines + [f"- **{r['term']}**:{r['note']}" for r in view["recent"]]
    why = recent.get("error") or (f"{view['dropped']} 个都已列过" if view["dropped"] else "没有新名字")
    return lines + [f"无({why})"]


def breakout_lines(bo: dict) -> list[str]:
    lines = ["", f"### ② 单仓库爆发(近 {breakout.WINDOW_DAYS} 天新建;{breakout.WINDOW_DAYS + 1}–{breakout.LATE_DAYS} 天的要 "
                 f"≥{breakout.LATE_MIN_STARS} 星;按每天涨星排;🆕 = 今天第一次达标,记为候选词,14 天后复盘)", ""]
    repos = bo.get("repos") or []
    if not repos:
        return lines + [f"无({bo.get('error') or ('跳过' if bo.get('skipped') else '没有爆发仓库')})"]
    return lines + ["| 仓库 | ★ | 均/天 | 比昨天 | 天数 | 简介 |", "|---|---|---|---|---|---|"] + [
        f"| {'🆕 ' if r.get('new') else ''}[{r['repo']}](https://github.com/{r['repo']}) | {r['stars']} | {r['velocity']} | "
        f"{'+' + str(r['delta']) if r['delta'] is not None else '—'} | {r['age_days']} | "
        f"{r['description'][:60].replace('|', '/')} |" for r in repos]


def status_lines(b: dict[str, dict]) -> list[str]:
    x, hf = b["x"], b["hf"]
    lines = ["", "### 数据状态", ""]
    if not (x.get("skipped") and hf.get("skipped")):
        lines += _source_status(x, hf)
    if not b.get("social", {"skipped": True}).get("skipped"):
        lines.append(social_sites.status(b["social"]))
    lines += _rest_status(b["breakout"], b["github"], b)
    cost = _cost(x, b.get("review", {}), b.get("usecases", {}), b.get("appstore", {}), b.get("meme", {}))
    return lines + [f"- AIsa 花费:{cost}(新词表的模型调用另计)"]


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
    lines += [x_waiting(b["x"])] if b["x"].get("waiting") else []
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


def report_errors(blocks: dict[str, dict]) -> bool:
    """A failed signal writes the source report, the run's step summary, except the new sites in shadow
    mode: not in it. No error sends mail; only a new pick does (mail_new_picks)."""
    return any(b.get("error") for k, b in blocks.items() if social_sites.SOCIAL_SHOW or k != "social")


def x_block(snaps: Path, flags: set[str]) -> dict:
    """X about once a day (source_signals.X_EVERY_HOURS): the runs in between leave it out, saying when it
    was read. HF, the trends, the charts and the new sites keep their 8 hours."""
    if "--skip-x" in flags:
        return {"skipped": True}
    return source_signals.x_wait(snaps) or run("x", lambda: source_signals.x_new(snaps), False)


def x_waiting(x: dict) -> str:
    """'- ① X:8.2 小时前读过(10-21 00:41 UTC),每 20 小时读一次,这轮不读' for a run that left X out."""
    when = x["last_read"][5:16].replace("T", " ")
    return f"- ① X:{x['hours']} 小时前读过({when} UTC),每 {source_signals.X_EVERY_HOURS} 小时读一次,这轮不读"


def sources_main(report: Path, snaps: Path, flags: set[str]) -> int:
    blocks = {"x": x_block(snaps, flags),
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
    new = mail_new_picks(report, snaps, blocks)
    print("新的可做词:" + ("、".join(p["term"] for p in new) or "无,不发邮件"))
    if named(lead) or report_errors(blocks):
        report.write_text(sources_markdown(lead, blocks))
        print(report.read_text())
    else:
        _print_quiet(blocks)
    return 0


def _print_quiet(blocks: dict[str, dict]) -> None:
    """A run with no new name writes no report: its status goes to the log."""
    print("① 没有新名字:" + "; ".join(f"{k} {v.get('posts', v.get('models', '—'))}" for k, v in blocks.items() if k != "record"))
    for k, mod in STATUS_LINES:
        if not blocks[k].get("skipped"):
            print(mod.status(blocks[k]))
    if blocks["x"].get("waiting"):
        print(x_waiting(blocks["x"]))


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
    blocks["review"] = run("review", review.review, no_db or "--skip-review" in flags)
    blocks["summary"] = run("summary", review.summary, no_db)
    blocks["recent_sources"] = run("recent_sources", lambda: {"rows": review.recent_sources(kinds=SOURCE_KINDS)},
                                   no_db or "--skip-x" not in flags)
    keywords(blocks, lead, keep, snaps, flags)
    write_daily(report, snaps, flags, lead, blocks)
    return 0


def write_daily(report: Path, snaps: Path, flags: set[str], lead: list[dict], blocks: dict[str, dict]) -> None:
    """The daily mail and its JSON copy, then the memory of the source leads it showed (LISTED)."""
    today = date.today()
    view = daily_view(blocks, today, sent_lately(flags, today), set(memory(snaps / LISTED)))
    report.write_text(markdown(lead, blocks, view))
    report.with_suffix(".json").write_text(json.dumps({"leads": lead, **blocks}, ensure_ascii=False, indent=1, default=str))
    save_listed(snaps, view["shown"], today)
    print(report.read_text())


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
