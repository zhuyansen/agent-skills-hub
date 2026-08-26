"""Roll up the four analytics fetchers' JSON outputs into one markdown digest.

Reads ops/{gsc,ga,plausible,clarity}/out/*.json (whatever exists) and prints
a compact markdown summary to stdout. Used by the daily GitHub Actions job to
populate the run's Step Summary. Missing files are skipped gracefully so a
partial run (e.g. Clarity hit its 10/day limit) still yields a digest.

Run: python ops/analytics_digest.py > digest.md
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def load(rel):
    p = os.path.join(ROOT, rel)
    try:
        with open(p) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def section(title):
    print(f"\n## {title}\n")


def main():
    print("# 数据四件套日报 · Analytics Daily Digest")

    # Health banner: a missing source means its fetcher FAILED (auth/quota),
    # NOT that the metric is zero. Silent truncation once let a digest report
    # "0 conversions" when GA had actually crashed (07-12 token-expiry scar).
    down = [
        name
        for name, probe in (
            ("GSC", "gsc/out/queries.json"),
            ("GA", "ga/out/pages.json"),
            ("Plausible", "plausible/out/sources.json"),
            ("Clarity", "clarity/out/overview.json"),
        )
        if not (load(probe) or (name == "Plausible" and load("plausible/out/source.json")))
    ]
    if down:
        print(
            f"\n> ⚠️ **数据源未出数:{', '.join(down)}** — 这是抓取失败(凭证过期 or 网络超时,查 CI 日志定性),"
            f"不是指标为 0。相关板块缺失/转化数不可信,先修凭证再解读。\n"
        )

    # ── GSC ──
    q = load("gsc/out/queries.json")
    if q:
        # Quoted queries are exact-match search OPERATORS. A human almost never
        # types `"ppt master" "codex" "skill"`; rank trackers and scrapers do.
        # Measured 2026-08-16 over 90 days: 149 such queries, 4,827 impressions,
        # exactly 0 clicks — 12.6% of all impressions. They distort three things
        # at once: impressions up, CTR down, and average POSITION better than
        # reality (operator queries face less competition, ranking 5.2 against
        # 15.6 for real ones). An aggregate that mixes them in is unreadable.
        # queries.json is already operator-free — fetch_gsc.py filters at the
        # source so compare.json, the baselines and opportunities.py all inherit
        # the same clean set. The excluded rows are saved beside it; read them
        # to state the size of the exclusion rather than re-deriving it here
        # with a narrower rule than the fetcher uses.
        bots = load("gsc/out/queries-operators.json") or []
        humans = q
        if bots:
            bi = sum(r["impressions"] for r in bots)
            bc = sum(r["clicks"] for r in bots)
            ti = (sum(r["impressions"] for r in q) + bi) or 1
            print(f"> 已剔除 **{len(bots)} 个搜索操作符查询**"
                  f"(曝光 {bi:,},占 {bi/ti*100:.1f}%,点击 {bc})——"
                  f"引号/site:/减号等操作符是排名监控工具在跑,不是真人。"
                  f"名单见 `ops/gsc/out/queries-operators.json`。\n")
        section("GSC · 热门搜索词 (Top 10,真人)")
        print("| query | clicks | impr | ctr% | pos |")
        print("|---|--:|--:|--:|--:|")
        for r in humans[:10]:
            print(f"| {r['query'][:40]} | {r['clicks']} | {r['impressions']} | {r['ctr']} | {r['position']} |")
        if humans:
            hi = sum(r["impressions"] for r in humans)
            hc = sum(r["clicks"] for r in humans)
            print(f"\n*真人词合计:曝光 {hi:,} · 点击 {hc} · CTR {hc/hi*100:.2f}%*\n")
    cmp = load("gsc/out/compare.json")
    if cmp:
        risers = sorted(cmp, key=lambda r: r.get("d_clicks", 0), reverse=True)[:8]
        section("GSC · 涨幅 Top 8 (rising queries)")
        for r in risers:
            print(f"- **+{r.get('d_clicks', 0)}** {r['query'][:50]}")

    # ── GA ──
    ga_pages = load("ga/out/pages.json")
    if ga_pages:
        section("GA · 热门页 (Top 10)")
        print("| page | views | sessions | bounce |")
        print("|---|--:|--:|--:|")
        for r in ga_pages[:10]:
            b = round(float(r.get("bounceRate", 0)) * 100)
            print(f"| {r['pagePath'][:40]} | {r['screenPageViews']} | {r['sessions']} | {b}% |")
    ga_src = load("ga/out/sources.json")
    if ga_src:
        section("GA · 流量来源 (Top 8)")
        for r in ga_src[:8]:
            print(f"- {r['sessionSource']} / {r.get('sessionMedium', '')} — {r['sessions']} sessions")

        # GEO water level (water-system ①b): sessions referred by AI
        # assistants. The whole point of llms.txt / the dataset / MCP
        # distribution — surface it daily instead of eyeballing the list.
        AI_SRC = ("chatgpt", "openai", "perplexity", "doubao", "gemini",
                  "copilot", "claude", "kimi", "deepseek", "you.com", "phind")
        geo = [r for r in ga_src
               if any(k in (r.get("sessionSource") or "").lower() for k in AI_SRC)
               or (r.get("sessionMedium") or "") == "ai-assistant"]
        section("GEO 水位 · AI 引荐(①b 进水口)")
        if geo:
            total = sum(int(r["sessions"]) for r in geo)
            print(f"- **合计 {total} sessions** ← " + " · ".join(
                f"{r['sessionSource']} {r['sessions']}" for r in geo))
        else:
            print("- (本期无 AI 引荐来源)")

    # ── GA conversion events — the funnel we instrumented; the numbers that
    #    decide what to build next. 🎯 marks our custom events. ──
    ga_ev = load("ga/out/events.json")
    if ga_ev:
        # The enterprise funnel, in order. Instrumenting events without adding
        # them here makes them invisible — exactly what happened to the five
        # added on 2026-08-10: they shipped, fired, and never reached the report.
        # Anything new goes in the same commit as the trackEvent call.
        watch = {
            "install_command_copied", "audit_run", "enterprise_cta_click",
            "newsletter_subscribe", "audit_pro_upsell_click",
            "free_tier_click",
            "enterprise_form_viewed", "enterprise_form_started",
            "enterprise_lead_attempt", "enterprise_lead_submitted",
            "enterprise_lead_invalid", "enterprise_lead_failed",
            # deep_audit_checkout/mailto retired 2026-07-13 ($49 → Pro upsell)
        }
        # Print the paid funnel as a chain so a drop-off is visible as a shape,
        # not as five numbers the reader has to order themselves.
        FUNNEL = ["enterprise_cta_click", "enterprise_form_viewed",
                  "enterprise_form_started", "enterprise_lead_attempt",
                  "enterprise_lead_submitted"]
        custom = [r for r in ga_ev if r.get("eventName") in watch]
        # Bot-pollution flag (scar 2026-07-16): 851 audit_run/day from one
        # Singapore DC scraper poisoned the funnel KPI. If a single country
        # holds ≥60% of an event (and volume is non-trivial), say so inline.
        geo = load("ga/out/events_geo.json") or []
        conc = {}
        for ev in watch:
            rows = [g for g in geo if g.get("eventName") == ev]
            total = sum(int(g["eventCount"]) for g in rows)
            if total >= 50 and rows:
                top = max(rows, key=lambda g: int(g["eventCount"]))
                share = int(top["eventCount"]) / total
                if share >= 0.6:
                    conc[ev] = f" ⚠️ {int(share*100)}% 来自 {top['country']},疑似机器流量"
        section("GA · 转化事件 🎯 (28天)")
        if custom:
            for r in custom:
                flag = conc.get(r["eventName"], "")
                print(f"- 🎯 **{r['eventName']}** — {r['eventCount']} 次 / {r['totalUsers']} 人{flag}")
        else:
            print("- (自定义转化事件尚无数据)")
        counts = {r.get("eventName"): int(r["eventCount"]) for r in ga_ev}
        chain = " → ".join(
            f"{e.replace('enterprise_', '').replace('lead_', '').replace('form_', '')} {counts.get(e, 0)}"
            for e in FUNNEL)
        print(f"\n**企业漏斗**: {chain}")
        # These stages are NOT strictly nested and the arrow notation implies
        # they are. form_viewed fires from an IntersectionObserver, so anyone
        # who scrolls the page far enough counts — with or without ever
        # clicking a CTA. On 2026-08-25 that produced "cta_click 13 → viewed
        # 18", a funnel where a later stage outnumbers an earlier one, which is
        # impossible for a real funnel and reads as a data error. Say what it
        # actually means rather than leaving the reader to reconcile it.
        for prev, nxt in zip(FUNNEL, FUNNEL[1:]):
            if counts.get(nxt, 0) > counts.get(prev, 0):
                print(f"  ↳ 注:{nxt.replace('enterprise_','')} ({counts.get(nxt,0)}) "
                      f"高于 {prev.replace('enterprise_','')} ({counts.get(prev,0)}) —— "
                      f"form_viewed 由滚动触发,不要求先点 CTA,两者不是包含关系")
                break
        if counts.get("enterprise_lead_invalid"):
            print(f"  ↳ 被必填项挡回: {counts['enterprise_lead_invalid']} 次")
        if counts.get("enterprise_lead_failed"):
            print(f"  ↳ ⚠️ 写入失败: {counts['enterprise_lead_failed']} 次 —— 这是故障不是没需求")
        missing = watch - set(counts)
        if missing:
            print(f"- 未触发: {', '.join(sorted(missing))}")

    # ── Plausible (rows are {metrics:[visitors,pageviews], dimensions:[name]}) ──
    pl = load("plausible/out/sources.json") or load("plausible/out/source.json")
    if pl:
        section("Plausible · 来源")
        for r in pl[:8]:
            try:
                name = r["dimensions"][0]
                v = r["metrics"][0]
            except (KeyError, IndexError, TypeError):
                continue
            print(f"- {name}: {v} visitors")

    # ── Clarity ──
    ov = load("clarity/out/overview.json")
    if ov and isinstance(ov, list):
        section("Clarity · UX 摩擦")
        # Say which window these came from. Clarity's numbers are a 1-3 day
        # ROLLING window, so a fix shipped yesterday is still averaged against
        # pre-fix days — reading a flat number as "the fix didn't work" is the
        # trap this line exists to prevent.
        meta = load("clarity/out/overview.meta.json") or {}
        days = meta.get("numOfDays")
        if days:
            print(f"*(滚动窗口 {days} 天 · 抓取 {str(meta.get('fetched_at',''))[:16]}"
                  f" —— 刚上线的改动只占其中一天,别据此下结论)*\n")

        # Clarity separates human from bot sessions and reports both. That makes
        # it the only CLEAN absolute traffic number we have: GA's totals are
        # bot-inflated (~5.5x on 2026-08-10) and Plausible has been 402 since
        # 08-04. This sat unread in the payload for six days while the digest
        # kept saying no trustworthy baseline existed.
        # Per-session, not total. Totals rank by traffic, so a page with 346
        # sessions and normal friction (0.4 dead clicks each) outranks one where
        # a single session racked up 54 — and the second is the actual bug. Every
        # real defect found so far had this signature: /author/asgeirtj/ at 26
        # in one session, /book/ch02 at 54. The aggregate rate never showed them.
        by_url = load("clarity/out/by-url.json") or []
        dead = next((m for m in by_url if m.get("metricName") == "DeadClickCount"), None)
        if dead:
            rows = []
            for r in dead.get("information", []):
                n, sess = int(r.get("subTotal", 0) or 0), int(r.get("sessionsCount", 0) or 0)
                if n >= 10 and sess:
                    rows.append((n / sess, n, sess, r["Url"].replace("https://agentskillshub.top", "")))
            rows.sort(reverse=True)
            if rows:
                print("\n**摩擦最集中的页面(按每会话,>=10次才计)**\n")
                print("| 页面 | 每会话 | 次数 | 会话 |")
                print("|---|--:|--:|--:|")
                # The ⚠️ needs at least two sessions. Its record with one:
                # /author/asgeirtj/ (26) and /book/ch02 (54) were the same real
                # shell bug in the same week; every single-session hit since —
                # james-design, /analyzer?repo=, claude-obsidian, VideoCaptioner
                # — checked out healthy under investigation. One visitor
                # clicking 23 times is one visitor, not a page defect, and an
                # alarm that fires daily on those trains the reader to skip the
                # column. The rows stay visible because they are still data;
                # only the alarm is withheld.
                for per, n, sess, url in rows[:6]:
                    flag = " ⚠️" if per >= 5 and sess >= 2 else ""
                    note = " ·单会话" if sess == 1 else ""
                    print(f"| {url[:46]} | **{per:.1f}**{flag}{note} | {n} | {sess} |")
                print("\n*⚠️ = 每会话 >=5 次且横跨 >=2 个会话,才算页面缺陷。"
                      "单会话高频是一个访客的行为,不是页面的问题 —— "
                      "此前 5 次单会话告警查下来页面都是健康的。*\n")

        traffic = next((m for m in ov if m.get("metricName") == "Traffic"), None)
        if traffic and traffic.get("information"):
            t = traffic["information"][0]
            human = int(t.get("totalSessionCount", 0))
            bot = int(t.get("totalBotSessionCount", 0))
            if human or bot:
                share = bot / (human + bot) * 100 if (human + bot) else 0
                per_day = human / days if days else human
                print(f"**真人流量基线(Clarity,已剔除机器):约 {per_day:.0f} 会话/天**"
                      f" — {days}天共 {human:,} 真人 / {bot:,} 机器,机器占 {share:.0f}%\n")
        for m in ov:
            name = m.get("metricName", "")
            if name in ("DeadClickCount", "RageClickCount", "QuickbackClick", "ScriptErrorCount"):
                info = m.get("information", [{}])
                pct = info[0].get("sessionsWithMetricPercentage", "?") if info else "?"
                # Print the COUNT next to the rate. sessionsWithMetricPercentage
                # is the share of sessions with >=1 event — when session volume
                # drops, it rises even as the problem shrinks. On 2026-08-10 dead
                # clicks fell 420 -> 347 while that rate went 13.6% -> 16.4%, and
                # the rate alone read as a regression. Never track one without
                # the other.
                total = info[0].get("subTotal", "?") if info else "?"
                print(f"- {name}: {pct}% sessions · 共 {total} 次")

    print("\n---\n*生成: ops/analytics_digest.py · 数据源 ops/*/out/*.json*")


if __name__ == "__main__":
    main()
