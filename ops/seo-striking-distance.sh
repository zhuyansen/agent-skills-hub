#!/usr/bin/env bash
#
# SEO Striking Distance Finder for Agent Skills Hub
#
# Finds keywords where agentskillshub.top ranks #4-20 (striking distance
# to page 1 top 3). Uses Google Search Console API if credentials exist,
# otherwise falls back to estimating via our sitemap + target keyword list.
#
# Usage:
#   ./ops/seo-striking-distance.sh
#   ./ops/seo-striking-distance.sh --gsc          # Use GSC API (requires auth)
#   ./ops/seo-striking-distance.sh --estimate      # Free estimate mode (no API)
#   ./ops/seo-striking-distance.sh --output FILE   # Custom output path
#
# GSC API Requirements (optional):
#   - Google Cloud project with Search Console API enabled
#   - OAuth credentials (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
#   - Authenticated token (run gsc_auth.py first)
#   - Set GSC_SITE_URL=https://agentskillshub.top/ or sc-domain:agentskillshub.top
#
# Dependencies:
#   pip install google-api-python-client google-auth (for GSC mode)
#   curl, jq (for estimate mode)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${SCRIPT_DIR}/output"
mkdir -p "$OUTPUT_DIR"

DOMAIN="agentskillshub.top"
SITE_URL="https://${DOMAIN}"
TODAY=$(date +%Y-%m-%d)
OUTPUT_FILE="${OUTPUT_DIR}/striking-distance-${TODAY}.md"

MODE="auto"  # auto, gsc, estimate

# ─── Parse arguments ───────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --gsc)       MODE="gsc"; shift ;;
        --estimate)  MODE="estimate"; shift ;;
        --output)    OUTPUT_FILE="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [--gsc|--estimate] [--output FILE]"
            echo ""
            echo "Modes:"
            echo "  --gsc       Use Google Search Console API (requires credentials)"
            echo "  --estimate  Free estimate mode using sitemap analysis"
            echo "  (default)   Auto-detect: GSC if available, else estimate"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ─── GSC Mode ──────────────────────────────
run_gsc_mode() {
    echo "=== GSC Striking Distance Analysis ==="
    echo "Site: ${SITE_URL}"
    echo ""

    # Check for GSC credentials
    if [[ -z "${GSC_SITE_URL:-}" ]]; then
        export GSC_SITE_URL="${SITE_URL}/"
    fi

    if [[ -z "${GOOGLE_CLIENT_ID:-}" ]] || [[ -z "${GOOGLE_CLIENT_SECRET:-}" ]]; then
        echo "Error: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET required for GSC mode."
        echo "Set up Google OAuth credentials at:"
        echo "  https://console.cloud.google.com/apis/credentials"
        echo ""
        echo "Then export:"
        echo "  export GOOGLE_CLIENT_ID='your-id'"
        echo "  export GOOGLE_CLIENT_SECRET='your-secret'"
        echo "  export GSC_SITE_URL='https://agentskillshub.top/'"
        echo ""
        echo "And authenticate:"
        echo "  python ${SCRIPT_DIR}/../backend/gsc_auth.py"
        echo ""
        echo "Falling back to estimate mode..."
        run_estimate_mode
        return
    fi

    # Use Python to call GSC API
    python3 - <<'PYEOF'
import json
import os
import sys
from datetime import datetime, timedelta

# Try to import GSC client
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    print("Error: google-api-python-client not installed.")
    print("Run: pip install google-api-python-client google-auth")
    sys.exit(1)

SITE_URL = os.environ.get("GSC_SITE_URL", "https://agentskillshub.top/")
TOKEN_FILE = os.environ.get("GSC_TOKEN_FILE", ".gsc-token.json")

# Build credentials
if not os.path.exists(TOKEN_FILE):
    print(f"Error: Token file not found: {TOKEN_FILE}")
    print("Run gsc_auth.py first to authenticate.")
    sys.exit(1)

with open(TOKEN_FILE) as f:
    token_data = json.load(f)

cred = Credentials(
    token=token_data.get("access_token"),
    refresh_token=token_data.get("refresh_token"),
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
)
cred.refresh(Request())

service = build("searchconsole", "v1", credentials=cred)

# Query last 28 days
end_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

# Get all queries with position data
result = service.searchanalytics().query(
    siteUrl=SITE_URL,
    body={
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["query", "page"],
        "rowLimit": 5000,
        "type": "web",
        "dataState": "all",
    }
).execute()

rows = result.get("rows", [])
if not rows:
    print("No GSC data found. Site may be too new or not verified.")
    sys.exit(0)

# Filter for striking distance (positions 4-20)
striking = []
for row in rows:
    pos = row["position"]
    if 4 <= pos <= 20:
        striking.append({
            "query": row["keys"][0],
            "page": row["keys"][1],
            "position": round(pos, 1),
            "clicks": row["clicks"],
            "impressions": row["impressions"],
            "ctr": round(row["ctr"] * 100, 2),
        })

# Sort by impressions (highest opportunity first)
striking.sort(key=lambda x: x["impressions"], reverse=True)

# Calculate potential
today = datetime.now().strftime("%Y-%m-%d")
print(f"# Striking Distance Keywords — {today}")
print(f"**Site:** {SITE_URL}")
print(f"**Period:** {start_date} to {end_date}")
print(f"**Total striking distance queries:** {len(striking)}")
print()

if not striking:
    print("No keywords found in positions 4-20. Keep building content!")
    sys.exit(0)

# Top 3 opportunity (position 4-6, high impressions)
top3_opps = [s for s in striking if s["position"] <= 6]
print("## Almost Page 1 Top 3 (Position 4-6)")
print()
if top3_opps:
    print("| Query | Page | Position | Impressions | Clicks | CTR |")
    print("|---|---|---|---|---|---|")
    for row in top3_opps[:20]:
        page_short = row["page"].replace(f"https://{os.environ.get('DOMAIN', 'agentskillshub.top')}", "")
        print(f"| {row['query']} | {page_short} | {row['position']} | {row['impressions']} | {row['clicks']} | {row['ctr']}% |")
    print()
    print("**Action:** These need minor optimization — better title tags, H1 match, internal links.")
else:
    print("No queries at positions 4-6 yet.")
print()

# Page 1 bottom (position 7-10)
p1_bottom = [s for s in striking if 7 <= s["position"] <= 10]
print("## Page 1 Bottom (Position 7-10)")
print()
if p1_bottom:
    print("| Query | Page | Position | Impressions | Clicks | CTR |")
    print("|---|---|---|---|---|---|")
    for row in p1_bottom[:20]:
        page_short = row["page"].replace(f"https://{os.environ.get('DOMAIN', 'agentskillshub.top')}", "")
        print(f"| {row['query']} | {page_short} | {row['position']} | {row['impressions']} | {row['clicks']} | {row['ctr']}% |")
    print()
    print("**Action:** Add more content depth, get 1-2 backlinks, improve internal linking.")
else:
    print("No queries at positions 7-10 yet.")
print()

# Page 2 (position 11-20)
p2 = [s for s in striking if 11 <= s["position"] <= 20]
print("## Page 2 (Position 11-20)")
print()
if p2:
    print("| Query | Page | Position | Impressions | Clicks | CTR |")
    print("|---|---|---|---|---|---|")
    for row in p2[:30]:
        page_short = row["page"].replace(f"https://{os.environ.get('DOMAIN', 'agentskillshub.top')}", "")
        print(f"| {row['query']} | {page_short} | {row['position']} | {row['impressions']} | {row['clicks']} | {row['ctr']}% |")
    print()
    print("**Action:** Consider content refresh, add FAQ section, build topical cluster.")
else:
    print("No queries at positions 11-20 yet.")
print()

# CTR underperformers (good position but low CTR)
ctr_under = [s for s in striking if s["position"] <= 10 and s["ctr"] < 3.0 and s["impressions"] > 50]
if ctr_under:
    print("## CTR Underperformers (Good Rank, Low CTR)")
    print("These pages rank well but nobody clicks — improve title tag and meta description.")
    print()
    print("| Query | Position | Impressions | CTR | Potential Clicks |")
    print("|---|---|---|---|---|")
    for row in ctr_under[:15]:
        # Estimate: position 1-3 avg CTR ~8%, current CTR is low
        potential = round(row["impressions"] * 0.08 - row["clicks"])
        print(f"| {row['query']} | {row['position']} | {row['impressions']} | {row['ctr']}% | +{potential} |")
    print()

# Summary stats
total_potential_clicks = sum(
    max(0, round(s["impressions"] * 0.08 - s["clicks"]))
    for s in striking if s["position"] <= 10
)
print("## Summary")
print()
print(f"- **Striking distance keywords (pos 4-20):** {len(striking)}")
print(f"- **Almost top 3 (pos 4-6):** {len(top3_opps)}")
print(f"- **Page 1 bottom (pos 7-10):** {len(p1_bottom)}")
print(f"- **Page 2 (pos 11-20):** {len(p2)}")
print(f"- **Estimated additional clicks if optimized:** +{total_potential_clicks}/month")
PYEOF
}

# ─── Estimate Mode (Free, no API) ─────────
run_estimate_mode() {
    echo "=== Striking Distance Estimate (Free Mode) ==="
    echo "Site: ${SITE_URL}"
    echo ""
    echo "Note: This mode estimates based on sitemap analysis and target keywords."
    echo "For actual position data, set up Google Search Console API (--gsc mode)."
    echo ""

    # Generate the estimate report
    python3 - <<PYEOF
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, unquote
from collections import Counter

DOMAIN = "${DOMAIN}"
SITE_URL = "${SITE_URL}"
OUTPUT_DIR = "${OUTPUT_DIR}"
PROJECT_ROOT = "${PROJECT_ROOT}"
today = datetime.now().strftime("%Y-%m-%d")

# Load scenario keywords for semantic matching
SCENARIO_DATA = {}
scenario_json_path = os.path.join(PROJECT_ROOT, "frontend", "scripts", "scenario-keywords.json")
try:
    with open(scenario_json_path) as f:
        scenarios = json.load(f)
    for sc in scenarios:
        slug = sc["slug"]
        # Collect all matchable terms for this scenario
        match_info = sc.get("match", {})
        terms = set()
        # Add slug parts
        terms.update(slug.split("-"))
        # Add title words (lowercased)
        terms.update(sc.get("title", "").lower().split())
        # Add keywords from match config
        for key in ["keywords", "primary_keywords", "secondary_keywords"]:
            for kw_phrase in match_info.get(key, []):
                terms.update(kw_phrase.lower().split())
        # Add category slugs
        for cat in match_info.get("categories", []):
            terms.update(cat.split("-"))
        # Add topic matches
        for topic in match_info.get("topic_matches", []):
            terms.update(topic.lower().split("-"))
        SCENARIO_DATA[slug] = {
            "terms": terms,
            "title": sc.get("title", slug),
            "categories": match_info.get("categories", []),
        }
except Exception as e:
    print(f"Warning: Could not load scenario-keywords.json: {e}", file=sys.stderr)

# Target keywords we want to rank for
TARGET_KEYWORDS = {
    "Core Identity": [
        "ai agent tools", "ai agent framework", "mcp server directory",
        "claude code skills", "ai agent catalog", "best ai agents",
        "model context protocol servers", "agent skills hub",
    ],
    "Use Cases": [
        "ai web scraping tools", "ai code review", "ai workflow automation",
        "ai browser automation", "best mcp servers", "ai debugging tools",
        "ai security audit tools", "ai semantic search",
    ],
    "Comparison / BOFU": [
        "langchain vs crewai", "autogen vs crewai", "best ai agent framework 2026",
        "mcp server vs api", "claude skills vs gpt actions",
        "ai agent framework comparison",
    ],
    "Long-tail": [
        "best ai agent for web scraping",
        "how to build ai agent with mcp",
        "open source mcp server list",
        "claude code skill tutorial",
        "ai agent for devops automation",
        "best github repos for ai agents",
    ],
}

# Fetch our sitemap to understand what pages we have
def fetch_sitemap(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read().decode("utf-8", errors="ignore")
        data = re.sub(r'\s+xmlns\s*=\s*"[^"]*"', '', data, count=1)
        root = ET.fromstring(data)
        urls = []
        # Check for sitemap index
        for sm in root.findall(".//sitemap"):
            loc = sm.find("loc")
            if loc is not None and loc.text:
                urls.extend(fetch_sitemap(loc.text.strip()))
        if not urls:
            for url_elem in root.findall(".//url"):
                loc = url_elem.find("loc")
                if loc is not None and loc.text:
                    urls.append(loc.text.strip())
        return urls
    except Exception as e:
        return []

print(f"# Striking Distance Analysis — {today}")
print(f"**Site:** {SITE_URL}")
print(f"**Mode:** Free estimate (no GSC API)")
print()

# Fetch our pages
our_urls = fetch_sitemap(f"{SITE_URL}/sitemap.xml")
print(f"**Pages in sitemap:** {len(our_urls)}")
print()

# Classify our pages
page_map = {}
for url in our_urls:
    path = urlparse(url).path.strip("/")
    parts = path.split("/")
    if not parts or not parts[0]:
        page_map[url] = {"type": "home", "slug": ""}
    elif parts[0] == "skill":
        page_map[url] = {"type": "skill", "slug": "/".join(parts[1:])}
    elif parts[0] == "category":
        page_map[url] = {"type": "category", "slug": parts[1] if len(parts) > 1 else ""}
    elif parts[0] == "best":
        page_map[url] = {"type": "scenario", "slug": parts[1] if len(parts) > 1 else ""}
    elif parts[0] == "compare":
        page_map[url] = {"type": "compare", "slug": parts[1] if len(parts) > 1 else ""}
    else:
        page_map[url] = {"type": "other", "slug": path}

type_counts = Counter(p["type"] for p in page_map.values())
print("**Page breakdown:**")
for ptype, count in type_counts.most_common():
    print(f"  - {ptype}: {count}")
print()

# Keyword-to-page mapping analysis
# Priority: scenario > compare > category > skill > home/other
PAGE_TYPE_PRIORITY = {"scenario": 4, "compare": 3, "category": 2, "skill": 1, "home": 0, "other": 0}

def match_keyword_to_page(kw, page_map):
    """Match a keyword to the best page using scenario-aware logic.

    Strategy:
    1. Check scenario pages first — use scenario-keywords.json terms for
       semantic matching (not just slug word overlap).
    2. Then check category/compare pages by slug overlap.
    3. Fall back to skill pages only if nothing better found.
    4. Among equal scores, prefer higher-priority page types.
    """
    kw_lower = kw.lower()
    kw_words = set(kw_lower.split())
    # Remove stop words for matching; keep domain terms (ai, agent) but strip
    # generic English words and SEO filler that appear in every scenario
    stop_words = {"the", "a", "an", "for", "with", "and", "or", "to", "of", "in",
                  "on", "is", "how", "best", "top", "open", "source", "list",
                  "2026", "2025", "tool", "tools"}
    kw_content_words = kw_words - stop_words
    # Ensure we always have at least one word to match against
    if not kw_content_words:
        kw_content_words = kw_words - {"the", "a", "an", "for", "with", "and", "or", "to", "of", "in", "on", "is"}

    def fuzzy_overlap(words_a, words_b):
        """Count matches allowing prefix/stem overlap (e.g. debug~debugging)."""
        count = 0
        for wa in words_a:
            for wb in words_b:
                if wa == wb or wa.startswith(wb) or wb.startswith(wa):
                    count += 1
                    break
        return count

    best_match = None
    best_score = 0
    best_priority = -1

    # --- Phase 1: Match against scenario pages using scenario keyword data ---
    for url, meta in page_map.items():
        if meta["type"] != "scenario":
            continue
        slug = meta["slug"]
        if slug not in SCENARIO_DATA:
            continue

        sc = SCENARIO_DATA[slug]
        sc_terms = sc["terms"]
        slug_words = set(slug.split("-"))

        # Check how many keyword content words appear in scenario terms
        # Use fuzzy matching to handle stems (debug/debugging, scrape/scraping)
        overlap = fuzzy_overlap(kw_content_words, sc_terms)
        if not kw_content_words:
            continue
        score = overlap / len(kw_content_words)

        # Bonus: keyword contains "best"/"top" and this is a /best/ page
        if any(w in kw_words for w in ["best", "top"]):
            score += 0.15

        # Bonus: slug words appear directly in the keyword (fuzzy)
        slug_in_kw = fuzzy_overlap(slug_words, kw_content_words)
        if slug_in_kw > 0:
            score += 0.2 * (slug_in_kw / len(slug_words))

        priority = PAGE_TYPE_PRIORITY["scenario"]
        if score > best_score or (score == best_score and priority > best_priority):
            best_score = score
            best_match = url
            best_priority = priority

    # --- Phase 2: Match against compare pages ---
    for url, meta in page_map.items():
        if meta["type"] != "compare":
            continue
        slug_words = set(re.split(r'[-_/]', meta["slug"].lower()))
        overlap = len(kw_content_words & slug_words)
        score = overlap / len(kw_content_words) if kw_content_words else 0

        if any(w in kw_words for w in ["vs", "comparison", "compare"]):
            score += 0.3

        priority = PAGE_TYPE_PRIORITY["compare"]
        if score > best_score or (score == best_score and priority > best_priority):
            best_score = score
            best_match = url
            best_priority = priority

    # --- Phase 3: Match against category pages ---
    for url, meta in page_map.items():
        if meta["type"] != "category":
            continue
        slug_words = set(re.split(r'[-_/]', meta["slug"].lower()))
        overlap = len(kw_content_words & slug_words)
        score = overlap / len(kw_content_words) if kw_content_words else 0

        if any(w in kw_words for w in ["framework", "server", "skill", "category"]):
            score += 0.15

        priority = PAGE_TYPE_PRIORITY["category"]
        if score > best_score or (score == best_score and priority > best_priority):
            best_score = score
            best_match = url
            best_priority = priority

    # --- Phase 4: Match against skill pages (only if no good match yet) ---
    if best_score < 0.4:
        for url, meta in page_map.items():
            if meta["type"] != "skill":
                continue
            slug_words = set(re.split(r'[-_/]', meta["slug"].lower()))
            overlap = len(kw_content_words & slug_words)
            score = overlap / len(kw_content_words) if kw_content_words else 0

            priority = PAGE_TYPE_PRIORITY["skill"]
            if score > best_score or (score == best_score and priority > best_priority):
                best_score = score
                best_match = url
                best_priority = priority

    return best_match, best_score


print("## Keyword Coverage Analysis")
print()
print("For each target keyword, which of our pages is the best match?")
print()

for group_name, keywords in TARGET_KEYWORDS.items():
    print(f"### {group_name}")
    print()
    print("| Target Keyword | Best Matching Page | Coverage | Optimization Notes |")
    print("|---|---|---|---|")

    for kw in keywords:
        best_match, best_score = match_keyword_to_page(kw, page_map)

        if best_match and best_score > 0.2:
            short_url = best_match.replace(SITE_URL, "")
            coverage = "Strong" if best_score > 0.6 else "Partial" if best_score > 0.3 else "Weak"
            notes = ""
            if best_score < 0.5:
                notes = "Add keyword to title/H1"
            elif best_score < 0.7:
                notes = "Optimize meta description"
            else:
                notes = "Good match - build links"
            print(f"| {kw} | {short_url} | {coverage} | {notes} |")
        else:
            print(f"| {kw} | **NO PAGE** | Missing | Create dedicated page |")

    print()

# Optimization recommendations
print("## Optimization Recommendations")
print()
print("### Pages to Create (No Coverage)")
print()
missing_pages = []
for group_name, keywords in TARGET_KEYWORDS.items():
    for kw in keywords:
        best_match, best_score = match_keyword_to_page(kw, page_map)
        if not best_match or best_score <= 0.3:
            slug = kw.replace(" ", "-").lower()
            missing_pages.append((kw, slug))

if missing_pages:
    for kw, slug in missing_pages:
        print(f"- **{kw}** -> Consider creating \`/best/{slug}/\` or \`/guide/{slug}/\`")
else:
    print("All target keywords have at least partial page coverage.")
print()

print("### Title Tag Templates")
print()
print("Use these templates for scenario/category pages:")
print()
print("- Scenario: \`Best {Tool Type} for {Use Case} in 2026 | Agent Skills Hub\`")
print("- Category: \`Top {Count}+ {Category} — Ranked by Stars | Agent Skills Hub\`")
print("- Compare: \`{Tool A} vs {Tool B}: Features, Stars & Use Cases | Agent Skills Hub\`")
print("- Skill: \`{Skill Name} — {Short Description} | Agent Skills Hub\`")
print()

print("### Quick Technical SEO Checks")
print()
checks = [
    ("Trailing slashes", "All URLs should end with / (GitHub Pages requirement)"),
    ("Canonical tags", "Each page needs <link rel='canonical'> pointing to itself"),
    ("robots.txt", f"Verify {SITE_URL}/robots.txt allows crawling"),
    ("Sitemap submission", f"Submit {SITE_URL}/sitemap.xml to Google Search Console"),
    ("Meta descriptions", "Each page type needs unique, keyword-rich meta descriptions"),
    ("H1 tags", "Each page should have exactly one H1 containing primary keyword"),
    ("Internal linking", "Link from high-authority pages (home, categories) to scenario pages"),
    ("Image alt text", "Add descriptive alt text to all images/icons"),
    ("Core Web Vitals", "Check LCP, FID, CLS at pagespeed.web.dev"),
    ("Mobile responsive", "Test at search.google.com/test/mobile-friendly"),
]
for check, detail in checks:
    print(f"- [ ] **{check}**: {detail}")
print()

print("### Next Steps")
print()
print("1. **Set up Google Search Console** for real position data:")
print(f"   - Go to https://search.google.com/search-console")
print(f"   - Add property: {SITE_URL} or sc-domain:{DOMAIN}")
print(f"   - Verify via DNS TXT record or HTML file")
print(f"   - Submit sitemap: {SITE_URL}/sitemap.xml")
print()
print("2. **Re-run with GSC data** after 2-4 weeks of data collection:")
print(f"   ./ops/seo-striking-distance.sh --gsc")
print()
print("3. **Run competitor gap analysis** for content opportunities:")
print(f"   python ops/seo-competitor-gap.py")
PYEOF
}

# ─── Auto-detect mode ─────────────────────
if [[ "$MODE" == "auto" ]]; then
    if [[ -n "${GOOGLE_CLIENT_ID:-}" ]] && [[ -n "${GOOGLE_CLIENT_SECRET:-}" ]] && [[ -f ".gsc-token.json" ]]; then
        MODE="gsc"
    else
        MODE="estimate"
    fi
fi

# ─── Run selected mode ────────────────────
echo "Running in ${MODE} mode..."
echo ""

if [[ "$MODE" == "gsc" ]]; then
    run_gsc_mode > "$OUTPUT_FILE"
else
    run_estimate_mode > "$OUTPUT_FILE"
fi

echo ""
echo "=== Done ==="
echo "Report saved to: ${OUTPUT_FILE}"
echo ""
echo "Quick view:"
head -30 "$OUTPUT_FILE"
