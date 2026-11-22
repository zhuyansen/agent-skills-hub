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


def print_fact_todos(todos):
    """Edits first, then the ones that only wait for a deploy or a publish."""
    def where(t):
        return " · ".join(f"`{w['file']}:{w['line']}`" if w.get("line") else f"`{w['file']}`" for w in t["where"])
    act = [t for t in todos if t["where"]]
    wait = [t for t in todos if not t["where"]]
    for t in act:
        print(f"- [ ] **{t['source']}** 写的是「{t['found']}」→ 改成 **{t['replace_with']}**")
        print(f"  - 改哪里: {where(t)}")
        print(f"  - 改完: {t['then']}" + (f" · {t['note']}" if t["note"] else ""))
    if wait:
        print(("\n" if act else "") + "**不用改,等着就行:**")
        for t in wait:
            print(f"- {t['source']}「{t['found']}」— {t['note'] or t['then']}")


def print_fact_consistency():
    """Entity-audit node 7: do the site, npm, GitHub, Wikidata and Zenodo state the same facts?

    The catalog grows every sync, so any count frozen into copy (a package README, a
    listing) drifts. ops/geo/fact_consistency.py reads the live counts and flags copy
    that has fallen more than its tolerance behind. A missing file means the check did
    not run, not that everything agrees.
    """
    num = lambda n: f"{n:,}" if isinstance(n, int) else "?"
    fc = load("geo/out/fact-consistency.json")
    if not fc:
        print("\n## ⚠️ 品牌事实没核成\n")
        print("- 事实一致性检查没出结果(查 Actions 日志里 Brand facts 这一步),不代表各处都一致。")
        return
    conflicts = fc.get("conflicts") or []
    if conflicts:
        todos = fc.get("todos")
        n_edit = sum(1 for t in todos if t["where"]) if todos else len(conflicts)
        tail = f"{n_edit} 处要改文案" if n_edit else "都只等部署/发布"
        print(f"\n## ⚠️ 品牌事实不一致 {len(todos or conflicts)} 处({tail})\n")
        if todos:
            print_fact_todos(todos)
        else:
            for c in conflicts:
                print(f"- **{c['source']}** `{c['fact']}`: 写的是 {c['found']},应为 {c['expected']} — {c['url']}")
        print("\n> 账本在 `ops/geo/brand-facts.json`;快照数(数据集 DOI、旧博文)旁边带出处就不算错。")
    section("🧾 品牌事实一致性")
    errs = fc.get("fetch_errors") or {}
    state = "✅ 一致" if not conflicts else f"⚠️ {len(conflicts)} 处不一致"
    print(f"- {state} · 核了 {fc.get('sources_checked', 0)} 个节点"
          f"(实时:收录 {num(fc.get('live_directory_size'))} / 已评级 {num(fc.get('live_graded_count'))})"
          + (f" · ⚠️ {len(errs)} 个节点没抓到: {', '.join(errs)}" if errs else ""))
    if fc.get("counts_skipped"):
        print("- ⚠️ 实时数没读到,今天**没核数字**(只核了日期、规则数、创始人、仿冒域名)。明天再看;连着几天都这样就查抓取。")


# GA counting more than this multiple of Clarity's human sessions means bots
# are still in the numbers. Before the automation filter it was 4.1x.
GA_TO_HUMAN_ALARM = 2.0
# A page viewed this many times per session is being reloaded by a script: a
# Linux box in Reims loaded / 8,261 times in 22 sessions on 2026-09-10. Real
# visitors returning to / through the SPA sit near 2.
RELOAD_VIEWS_PER_SESSION = 3
RELOAD_MIN_VIEWS = 500


def clarity_humans_per_day():
    """Clarity's human (non-bot) sessions per day, or None if unavailable."""
    ov = load("clarity/out/overview.json")
    days = (load("clarity/out/overview.meta.json") or {}).get("numOfDays")
    traffic = next((m for m in ov or [] if m.get("metricName") == "Traffic"), None)
    if not (days and traffic and traffic.get("information")):
        return None
    return int(traffic["information"][0].get("totalSessionCount", 0)) / days


def print_ga_exclusion():
    """State the automation GA dropped, and alarm if what's left still isn't human."""
    auto = load("ga/out/automation.json") or []
    days = load("ga/out/overview.json") or []
    kept = sum(int(r["sessions"]) for r in days)
    if auto:
        dropped = sum(int(r["sessions"]) for r in auto)
        share = dropped / ((dropped + kept) or 1) * 100
        # automation.json written before 2026-10-16 has no "rule"; a local run
        # on that stale output must still print, not die with a KeyError.
        detail = " / ".join(f"{r.get('rule') or r['screenResolution']} {int(r['sessions']):,}"
                            for r in auto)
        print(f"> 已剔除 **GA 自动化流量 {dropped:,} 会话**(占 {share:.0f}%:{detail})——"
              f"是机房里的无头浏览器:真实设备没有的屏幕,或真实屏幕上特定的系统+浏览器组合。"
              f"明细见 `ops/ga/out/automation.json`。\n")
    human = clarity_humans_per_day()
    if days and human:
        ratio = kept / len(days) / human
        if ratio > GA_TO_HUMAN_ALARM:
            print(f"> ⚠️ 剔除后 GA 仍有 {kept/len(days):.0f} 会话/天,是 Clarity 真人基线 "
                  f"{human:.0f}/天 的 **{ratio:.1f} 倍** —— 大概率出现了新的爬虫指纹。"
                  f"下面的 GA 数先别用,查 screenResolution 分布(真实屏幕再按 operatingSystem、browser 拆),"
                  f"把新指纹加进 `fetch_ga.py` 的 AUTOMATION_SCREENS 或 AUTOMATION_FINGERPRINTS。\n")


def main():
    print("# 数据四件套日报 · Analytics Daily Digest")

    # ── 0. 任务运行状态 + API 渠道与余额监控 ──
    hl = load("health/out/health.json")
    if hl:
        wfs = hl.get("workflows") or []
        chs = hl.get("channels") or []
        bad_wf = [w for w in wfs if not w.get("ok")]
        bad_ch = [c for c in chs if not c.get("ok")]
        if bad_wf or bad_ch:
            print("\n## ⚠️ 任务或渠道异常（需处理）\n")
            for w in bad_wf:
                err = w.get("error") or f"最近一次 {w.get('conclusion')} ({w.get('at', '')}) {w.get('url', '')}"
                print(f"- ❌ **任务失败 · {w['label']}** (`{w['file']}`): {err}")
            for c in bad_ch:
                print(f"- ⚠️ **渠道/余额告警 · {c['channel']}** ({c['used_by']}): {c.get('status_text', '')} {c.get('detail', '')}")
        section("🩺 任务运行状态 & 渠道余额监控")
        ok_wf = [w for w in wfs if w.get("ok")]
        print(f"- **定时任务 ({len(ok_wf)}/{len(wfs)} 正常)**: " + " · ".join(
            f"✅ {w['label']} ({w['at'] or '运行中'})" for w in ok_wf))
        for c in chs:
            icon = "🔌" if c.get("ok") else "⚠️"
            print(f"- {icon} **{c['channel']}** ({c['used_by']}): {c.get('status_text', '')}")

    print_fact_consistency()

    # Health banner: a missing source means its fetcher FAILED (auth/quota),
    # NOT that the metric is zero. Silent truncation once let a digest report
    # "0 conversions" when GA had actually crashed (07-12 token-expiry scar).
    down = [
        name
        for name, probe in (
            ("GSC", "gsc/out/queries.json"),
            ("GA", "ga/out/pages.json"),
            ("Clarity", "clarity/out/overview.json"),
        )
        if not load(probe)
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
    print_ga_exclusion()
    ga_pages = load("ga/out/pages.json")
    if ga_pages:
        section("GA · 热门页 (Top 10)")
        print("| page | views | sessions | bounce |")
        print("|---|--:|--:|--:|")
        for r in ga_pages[:10]:
            b = round(float(r.get("bounceRate", 0)) * 100)
            v, n = int(r["screenPageViews"]), int(r["sessions"]) or 1
            flag = (f" ⚠️ 每会话 {v/n:.1f} 次,疑似刷新脚本"
                    if v >= RELOAD_MIN_VIEWS and v / n >= RELOAD_VIEWS_PER_SESSION else "")
            print(f"| {r['pagePath'][:40]} | {v}{flag} | {r['sessions']} | {b}% |")
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
            "audit_cigate_upsell_click", "free_tier_click",
            "pro_checkout_click", "cigate_checkout_click", "fasttrack_checkout_click",
            "ci_gate_hero_cta", "ci_gate_copy_snippet",
            "org_audit_run", "org_audit_pro_click",
            "hero_guide_click", "fasttrack_lane_select",
            "enterprise_form_viewed", "enterprise_form_started",
            "enterprise_lead_attempt", "enterprise_lead_submitted",
            "enterprise_lead_invalid", "enterprise_lead_failed",
            # Audit-result capture (2026-09-23): same stages, own event family,
            # so this funnel prints on its own line next to the /enterprise/ one.
            "audit_lead_viewed", "audit_lead_started", "audit_lead_attempt",
            "audit_lead_submitted", "audit_lead_invalid", "audit_lead_failed",
            # deep_audit_checkout/mailto retired 2026-07-13 ($49 → Pro upsell)
        }
        # Print the paid funnel as a chain so a drop-off is visible as a shape,
        # not as five numbers the reader has to order themselves.
        FUNNEL = ["enterprise_cta_click", "enterprise_form_viewed",
                  "enterprise_form_started", "enterprise_lead_attempt",
                  "enterprise_lead_submitted"]
        AUDIT_FUNNEL = ["audit_run", "audit_lead_viewed", "audit_lead_started",
                        "audit_lead_attempt", "audit_lead_submitted"]
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

        def chain(stages, table=counts):
            short = lambda e: e.replace("enterprise_", "").replace("audit_", "").replace("lead_", "").replace("form_", "")
            return " → ".join(f"{short(e)} {table.get(e, 0)}" for e in stages)

        print(f"\n**企业漏斗**: {chain(FUNNEL)}")
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
        # The same offer, placed at the audit result. The two lines are the
        # experiment: same 48h promise, two surfaces, which one converts.
        # audit_run carries 28 days of history but the capture only exists
        # since 2026-09-23, so this funnel prints over the sweep's 7-day pull —
        # every stage on one window — and falls back to 28d until that exists.
        recent = load("ga/out/events_7d.json") or []
        counts7 = {r.get("eventName"): int(r["eventCount"]) for r in recent} if recent else counts
        print(f"**审计页漏斗({'7天' if recent else '28天'})**: {chain(AUDIT_FUNNEL, counts7)}")
        for stage in ("invalid", "failed"):
            if counts7.get(f"audit_lead_{stage}"):
                print(f"  ↳ 审计页 {stage}: {counts7[f'audit_lead_{stage}']} 次")
        if counts.get("enterprise_lead_invalid"):
            print(f"  ↳ 被必填项挡回: {counts['enterprise_lead_invalid']} 次")
        if counts.get("enterprise_lead_failed"):
            print(f"  ↳ ⚠️ 写入失败: {counts['enterprise_lead_failed']} 次 —— 这是故障不是没需求")
        missing = watch - set(counts)
        if missing:
            print(f"- 未触发: {', '.join(sorted(missing))}")

    ga_bd = load("ga/out/breakdown.json")
    if ga_bd:
        section("GA · 端 × 国家分布 (Top 8)")
        print("| 国家 | 端 | 会话 | 互动会话 | 活跃用户 |")
        print("|---|---|--:|--:|--:|")
        for r in ga_bd[:8]:
            print(f"| {r['country']} | {r['deviceCategory']} | {r['sessions']} | {r['engagedSessions']} | {r['activeUsers']} |")

    # ── Stripe (source-of-truth revenue & orders, zero PII) ──
    st = load("stripe/out/summary.json")
    if st:
        section("Stripe · 付费真相 (06 源头)")
        print(f"- **7 天**: {st.get('orders_7d', 0)} 单 / **${st.get('revenue_7d_usd', 0):.2f}** · "
              f"**28 天**: {st.get('orders_28d', 0)} 单 / **${st.get('revenue_28d_usd', 0):.2f}** · "
              f"**累计**: {st.get('total_orders', 0)} 单 / ${st.get('total_revenue_usd', 0):.2f}")
        print(f"- **美元早鸟**: {st.get('early_bird_sold', 0)}/{st.get('early_bird_limit', 100)} · "
              f"**28 天会话归因覆盖**: {st.get('attributed_28d', 0)}/{st.get('orders_28d', 0)} 单带 PostHog `distinct_id`")
        by_sku = st.get("by_sku") or {}
        if by_sku:
            print("\n| SKU | 28天订单 | 28天收入 | 累计订单 | 累计收入 |")
            print("|---|--:|--:|--:|--:|")
            for sku, row in sorted(by_sku.items()):
                print(f"| `{sku}` | {row.get('orders_28d', 0)} | ${row.get('revenue_28d_usd', 0):.2f} | "
                      f"{row.get('orders_all', 0)} | ${row.get('revenue_all_usd', 0):.2f} |")

    # ── PostHog (anti-adblock first-party proxy + product funnel + #11 breakdown) ──
    ph_ov = load("posthog/out/overview.json")
    ph_src = load("posthog/out/sources.json")
    ph_fun = load("posthog/out/funnel.json")
    ph_dim = load("posthog/out/dimensions.json")
    if any((ph_ov, ph_src, ph_fun, ph_dim)):
        section("PostHog · 无拦截流量与产品漏斗 (反代)")
        if ph_ov:
            tot_v = sum(int(r.get("visitors", 0) or 0) for r in ph_ov)
            tot_pv = sum(int(r.get("pageviews", 0) or 0) for r in ph_ov)
            tot_s = sum(int(r.get("sessions", 0) or 0) for r in ph_ov)
            last_day = ph_ov[-1]
            print(f"- **近 {len(ph_ov)} 天汇总**: {tot_s:,} sessions · {tot_v:,} visitors · {tot_pv:,} pageviews"
                  f"（最新 {last_day.get('day')}: {last_day.get('sessions', 0)} sessions / {last_day.get('pageviews', 0)} pv）")
        if ph_src:
            print("\n**PostHog 来源 Top 6**（含被广告拦截的开发者流量）:")
            for r in ph_src[:6]:
                print(f"- {r.get('source')} / {r.get('medium')} — {r.get('sessions')} sessions ({r.get('visitors')} visitors)")
        if ph_fun:
            print("\n**PostHog 产品事件 (7天 / 28天去重人数)**:")
            for r in ph_fun[:15]:
                if r.get("event") == "$pageview":
                    continue
                rev = float(r.get("revenue_28d_usd") or 0)
                rev_txt = f" · 收入 ${rev:.2f}" if rev > 0 else ""
                print(f"- `{r.get('event')}`: 7d {r.get('users_7d', 0)} 人 ({r.get('events_7d', 0)} 次) · 28d {r.get('users_28d', 0)} 人 ({r.get('events_28d', 0)} 次){rev_txt}")
        if ph_dim:
            print("\n**增长拆解 (首触落地页 × 端 × 国家 → 付费/意图/复制)**:\n")
            print("| 首触落地页 | 端 | 国家 | 会话 | audit | 商业意图 | 复制安装 | 付费人数 |")
            print("|---|---|---|--:|--:|--:|--:|--:|")
            for r in ph_dim[:12]:
                print(f"| {r.get('page_type')} | {r.get('device')} | {r.get('country')} | {r.get('sessions', 0)} | {r.get('audit_sessions', 0)} | {r.get('commercial_sessions', 0)} | {r.get('install_copy_sessions', 0)} | {r.get('buyers', 0)} |")

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
                # The numbers alone cannot classify a friction row — proven
                # repeatedly. Single-session-high has meant a real shell bug
                # (asgeirtj 26, book ch02 54), a by-design sub-50★ 404 fallback
                # (james-design 15, human-in-loop 41), AND a clicky visitor on a
                # healthy page (claude-obsidian 23). Magnitude 23 sits between a
                # 15 fallback and a 26 bug, so no per-session threshold
                # separates them. The only reliable classifier is what the URL
                # actually serves. So the ⚠️ is kept deliberately rare — a
                # defect hitting >=3 distinct visitors, which no noise ever did —
                # and the real value is the 30-second check spelled out below.
                for per, n, sess, url in rows[:6]:
                    flag = " ⚠️" if per >= 5 and sess >= 3 else ""
                    note = " ·单会话" if sess == 1 else ""
                    print(f"| {url[:46]} | **{per:.1f}**{flag}{note} | {n} | {sess} |")
                print("\n*判别一行高摩擦,curl 一下该 URL 即可,别靠数字猜:*\n"
                      "*· HTTP 404 → 低星页(<50★)无静态页,SPA 兜底空白,已知成因非 bug*\n"
                      "*· 200 且含 \"Browse by Category\" → 壳子画了首页内容,是 bug,要修*\n"
                      "*· 200 且干净 → 一个手快的访客,噪音*\n"
                      "*⚠️ 只在 >=5次/会话且>=3会话时亮(缺陷波及多人)—— 此前所有单/双会话告警查下来非空即已知。*\n")

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
