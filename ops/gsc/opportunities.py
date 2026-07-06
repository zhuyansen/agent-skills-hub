"""GSC opportunity-page pipeline — turns the manual ppt/browser-automation
diagnosis into one repeatable command.

For every page with real impressions but a weak CTR that is ALREADY rankable
(avg position in top ~20), pull its queries and classify:
  - GENERIC-WASTE: the high-impression queries rank 25+ (unwinnable head terms
    burning impressions) while specific/long-tail queries rank top-10.
    → prescription: retarget the title to the specific intent (the ppt fix).
  - LOW-CTR-BUT-RANKING: ranks top-10 but CTR still low → title/description
    isn't compelling; rewrite the snippet, not the target.
  - RISING: position < 5 → leave alone, it's working.

Output: ranked worklist to stdout + ops/gsc/out/opportunities.json.

Usage (backend venv, Clash proxy on):
  export https_proxy=http://127.0.0.1:7897 HTTPS_PROXY=http://127.0.0.1:7897
  python ops/gsc/opportunities.py [--days 28] [--min-impr 500] [--max-ctr 1.5]
"""
import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_gsc import get_service, pick_site, query, arg  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


def classify(page_queries, page_ctr):
    """Decide the prescription from a page's query mix."""
    ranked = [q for q in page_queries if q["impressions"] >= 3]
    if not ranked:
        return "THIN", "too few queries to judge"
    # impression-weighted: where do the impressions actually sit?
    heavy = sorted(ranked, key=lambda q: -q["impressions"])[:8]
    top10 = [q for q in heavy if q["position"] <= 10]
    deep = [q for q in heavy if q["position"] >= 25]
    heavy_impr = sum(q["impressions"] for q in heavy) or 1
    deep_impr = sum(q["impressions"] for q in deep)

    if deep and deep_impr / heavy_impr >= 0.4 and top10:
        specific = ", ".join(q["query"] for q in top10[:3])
        return "GENERIC-WASTE", (
            f"{deep_impr} impr on unrankable head terms (pos 25+); "
            f"already top-10 for specific: {specific} → retarget title to these"
        )
    if top10 and page_ctr < 1.5:
        return "WEAK-SNIPPET", (
            f"ranks top-10 ({len(top10)}/8 heavy queries) but CTR {page_ctr}% — "
            f"rewrite title/description, keep the target"
        )
    best = min(heavy, key=lambda q: q["position"])
    if best["position"] < 5:
        return "RISING", f"already pos {best['position']} — leave it"
    return "BUILD-AUTHORITY", "mid-page, needs links/depth not a title tweak"


def main():
    days = arg("--days", 28)
    min_impr = arg("--min-impr", 500)
    max_ctr = arg("--max-ctr", 1.5)
    end = date.today() - timedelta(days=2)
    start = end - timedelta(days=days - 1)

    svc = get_service()
    site = pick_site(svc)
    print(f"property: {site} · {start} → {end}\n")

    pages = query(svc, site, start, end, ["page"], limit=500)
    opps = [
        p for p in pages
        if p["impressions"] >= min_impr and p["ctr"] < max_ctr and p["position"] <= 20
    ]
    opps.sort(key=lambda p: -p["impressions"])
    print(f"{len(opps)} opportunity pages (impr≥{min_impr}, CTR<{max_ctr}%, pos≤20):\n")

    results = []
    for p in opps[:15]:
        path = p["page"].replace("https://agentskillshub.top", "")
        pq = query(svc, site, start, end, ["query"],
                   filters=[{"dimension": "page", "operator": "equals", "expression": p["page"]}],
                   limit=50)
        verdict, why = classify(pq, p["ctr"])
        results.append({
            "page": path, "impressions": p["impressions"], "ctr": p["ctr"],
            "position": p["position"], "verdict": verdict, "why": why,
            "top_queries": [{"q": q["query"], "impr": q["impressions"], "pos": q["position"]}
                            for q in sorted(pq, key=lambda x: -x["impressions"])[:6]],
        })
        icon = {"GENERIC-WASTE": "🎯", "WEAK-SNIPPET": "✍️", "RISING": "📈",
                "BUILD-AUTHORITY": "🔗", "THIN": "·"}.get(verdict, "?")
        print(f"{icon} {verdict:15} {p['impressions']:>6}i {p['ctr']:>5}% pos{p['position']:>5}  {path}")
        print(f"    → {why}")

    os.makedirs(OUT, exist_ok=True)
    json.dump(results, open(os.path.join(OUT, "opportunities.json"), "w"), ensure_ascii=False, indent=1)
    actionable = [r for r in results if r["verdict"] in ("GENERIC-WASTE", "WEAK-SNIPPET")]
    print(f"\n{len(actionable)} actionable now → ops/gsc/out/opportunities.json")


if __name__ == "__main__":
    main()
