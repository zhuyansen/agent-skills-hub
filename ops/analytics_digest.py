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

    # ── GSC ──
    q = load("gsc/out/queries.json")
    if q:
        section("GSC · 热门搜索词 (Top 10)")
        print("| query | clicks | impr | ctr% | pos |")
        print("|---|--:|--:|--:|--:|")
        for r in q[:10]:
            print(f"| {r['query'][:40]} | {r['clicks']} | {r['impressions']} | {r['ctr']} | {r['position']} |")
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
        watch = {
            "install_command_copied", "audit_run", "enterprise_cta_click",
            "newsletter_subscribe", "deep_audit_checkout", "deep_audit_mailto",
        }
        custom = [r for r in ga_ev if r.get("eventName") in watch]
        section("GA · 转化事件 🎯 (28天)")
        if custom:
            for r in custom:
                print(f"- 🎯 **{r['eventName']}** — {r['eventCount']} 次 / {r['totalUsers']} 人")
        else:
            print("- (自定义转化事件尚无数据)")
        missing = watch - {r.get("eventName") for r in ga_ev}
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
        for m in ov:
            name = m.get("metricName", "")
            if name in ("DeadClickCount", "RageClickCount", "QuickbackClick", "ScriptErrorCount"):
                info = m.get("information", [{}])
                pct = info[0].get("sessionsWithMetricPercentage", "?") if info else "?"
                print(f"- {name}: {pct}% sessions")

    print("\n---\n*生成: ops/analytics_digest.py · 数据源 ops/*/out/*.json*")


if __name__ == "__main__":
    main()
