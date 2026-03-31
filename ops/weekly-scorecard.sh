#!/usr/bin/env bash
#
# weekly-scorecard.sh — Agent Skills Hub Weekly Growth Scorecard
#
# Pulls real data from Supabase, GitHub, and local project stats,
# calculates week-over-week changes, and generates a formatted markdown report.
#
# Usage:
#   ./ops/weekly-scorecard.sh                  # Generate this week's scorecard
#   ./ops/weekly-scorecard.sh --dry-run        # Print to stdout only, don't save
#
# Requirements:
#   - curl, jq, gh (GitHub CLI), bc
#   - frontend/.env with VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY
#   - gh CLI authenticated
#
# Inspired by ericosiu/ai-marketing-skills growth-engine scorecard methodology,
# adapted from experiment tracking to product growth metrics.

set -euo pipefail

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/output"
PREV_FILE="$OUTPUT_DIR/.scorecard-prev.json"
ENV_FILE="$PROJECT_ROOT/frontend/.env"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi

# ── Load Supabase credentials from frontend/.env ──────────────────────────────
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found. Cannot query Supabase." >&2
  exit 1
fi

SUPABASE_URL="$(grep '^VITE_SUPABASE_URL=' "$ENV_FILE" | cut -d= -f2-)"
SUPABASE_KEY="$(grep '^VITE_SUPABASE_ANON_KEY=' "$ENV_FILE" | cut -d= -f2-)"

if [[ -z "$SUPABASE_URL" || -z "$SUPABASE_KEY" ]]; then
  echo "ERROR: Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY in $ENV_FILE" >&2
  exit 1
fi

# ── Date calculations ─────────────────────────────────────────────────────────
# Week ends on Sunday (yesterday if today is Monday, otherwise last Sunday)
TODAY="$(date +%Y-%m-%d)"
DOW="$(date +%u)"  # 1=Mon, 7=Sun

if [[ "$DOW" -eq 1 ]]; then
  WEEK_END="$(date -v-1d +%Y-%m-%d)"
else
  # Go back to last Sunday
  DAYS_SINCE_SUN=$(( DOW ))
  WEEK_END="$(date -v-${DAYS_SINCE_SUN}d +%Y-%m-%d)"
fi
# macOS date: -v must come before -f
WEEK_START="$(date -j -v-6d -f '%Y-%m-%d' "$WEEK_END" '+%Y-%m-%d')"

# Formatted labels
WEEK_START_LABEL="$(date -j -f '%Y-%m-%d' "$WEEK_START" '+%b %d')"
WEEK_END_LABEL="$(date -j -f '%Y-%m-%d' "$WEEK_END" '+%b %d, %Y')"

echo "Generating scorecard for week: $WEEK_START to $WEEK_END" >&2

# ── Helper: Supabase REST query ───────────────────────────────────────────────
supabase_get() {
  local endpoint="$1"
  curl -s "${SUPABASE_URL}/rest/v1/${endpoint}" \
    -H "apikey: ${SUPABASE_KEY}" \
    -H "Authorization: Bearer ${SUPABASE_KEY}" \
    -H "Accept: application/json" \
    -H "Prefer: count=exact"
}

supabase_count() {
  local endpoint="$1"
  local raw
  raw="$(curl -sI "${SUPABASE_URL}/rest/v1/${endpoint}" \
    -H "apikey: ${SUPABASE_KEY}" \
    -H "Authorization: Bearer ${SUPABASE_KEY}" \
    -H "Accept: application/json" \
    -H "Prefer: count=exact" \
    -X HEAD 2>/dev/null | grep -i 'content-range' | sed 's/.*\///' | tr -dc '0-9')"
  echo "${raw:-0}"
}

# ── Collect Supabase metrics ──────────────────────────────────────────────────
echo "  Querying Supabase..." >&2

# Total skills count
TOTAL_SKILLS="$(supabase_count 'skills?select=id')"
TOTAL_SKILLS="${TOTAL_SKILLS:-0}"

# New skills this week (first_seen >= WEEK_START)
NEW_SKILLS="$(supabase_count "skills?select=id&first_seen=gte.${WEEK_START}")"
NEW_SKILLS="${NEW_SKILLS:-0}"

# Total subscribers (returns 0 if RLS blocks anon key — set SUPABASE_SERVICE_ROLE_KEY env var to override)
# To use service role key: export SUPABASE_SERVICE_ROLE_KEY=... before running
if [[ -n "${SUPABASE_SERVICE_ROLE_KEY:-}" ]]; then
  _SUB_KEY="$SUPABASE_SERVICE_ROLE_KEY"
else
  _SUB_KEY="$SUPABASE_KEY"
fi
TOTAL_SUBS="$(curl -sI "${SUPABASE_URL}/rest/v1/subscribers?select=id" \
  -H "apikey: ${_SUB_KEY}" -H "Authorization: Bearer ${_SUB_KEY}" \
  -H "Accept: application/json" -H "Prefer: count=exact" \
  -X HEAD 2>/dev/null | grep -i 'content-range' | sed 's/.*\///' | tr -dc '0-9')"
TOTAL_SUBS="${TOTAL_SUBS:-0}"

VERIFIED_SUBS="$(curl -sI "${SUPABASE_URL}/rest/v1/subscribers?select=id&verified=eq.true&is_active=eq.true" \
  -H "apikey: ${_SUB_KEY}" -H "Authorization: Bearer ${_SUB_KEY}" \
  -H "Accept: application/json" -H "Prefer: count=exact" \
  -X HEAD 2>/dev/null | grep -i 'content-range' | sed 's/.*\///' | tr -dc '0-9')"
VERIFIED_SUBS="${VERIFIED_SUBS:-0}"

# Top trending: get latest snapshot week's top skill velocity
TOP_VELOCITY="$(supabase_get 'weekly_trending_snapshots?select=repo_full_name,star_velocity&order=star_velocity.desc&limit=1' | jq -r '.[0].star_velocity // 0')"

# Skill masters count
SKILL_MASTERS="$(supabase_count 'skill_masters?select=id')"
SKILL_MASTERS="${SKILL_MASTERS:-0}"

# Extra repos (community submissions)
EXTRA_REPOS_PENDING="$(supabase_count 'extra_repos?select=id&status=eq.pending')"
EXTRA_REPOS_PENDING="${EXTRA_REPOS_PENDING:-0}"
EXTRA_REPOS_APPROVED="$(supabase_count 'extra_repos?select=id&status=eq.approved')"
EXTRA_REPOS_APPROVED="${EXTRA_REPOS_APPROVED:-0}"

echo "  Supabase done. Skills=$TOTAL_SKILLS, New=$NEW_SKILLS, Subs=$VERIFIED_SUBS" >&2

# ── Collect GitHub metrics ────────────────────────────────────────────────────
echo "  Querying GitHub..." >&2

GH_REPO="zhuyansen/agent-skills-hub"
GH_DATA="$(gh api "repos/$GH_REPO" 2>/dev/null || echo '{}')"

GH_STARS="$(echo "$GH_DATA" | jq -r '.stargazers_count // 0')"
GH_FORKS="$(echo "$GH_DATA" | jq -r '.forks_count // 0')"
GH_OPEN_ISSUES="$(echo "$GH_DATA" | jq -r '.open_issues_count // 0')"

# Recent PRs merged this week
MERGED_PRS="$(gh pr list --repo "$GH_REPO" --state merged --search "merged:>=$WEEK_START" --json number 2>/dev/null | jq 'length' || echo 0)"

# Commits this week
COMMITS_THIS_WEEK="$(gh api "repos/$GH_REPO/commits?since=${WEEK_START}T00:00:00Z&until=${WEEK_END}T23:59:59Z&per_page=100" 2>/dev/null | jq 'length' || echo 0)"

echo "  GitHub done. Stars=$GH_STARS, Forks=$GH_FORKS, PRs=$MERGED_PRS" >&2

# ── Collect local project metrics ─────────────────────────────────────────────
echo "  Counting scenario pages..." >&2

# Count scenario pages from the keywords JSON (source of truth)
SCENARIO_PAGES=0
SCENARIO_JSON="$PROJECT_ROOT/frontend/scripts/scenario-keywords.json"
if [[ -f "$SCENARIO_JSON" ]]; then
  SCENARIO_PAGES="$(jq 'length' "$SCENARIO_JSON" 2>/dev/null || echo 0)"
fi
# Fallback: count built HTML files
if [[ "$SCENARIO_PAGES" -eq 0 ]] && [[ -d "$PROJECT_ROOT/frontend/public/scenarios" ]]; then
  SCENARIO_PAGES="$(find "$PROJECT_ROOT/frontend/public/scenarios" -name '*.html' -type f 2>/dev/null | wc -l | tr -d ' ')"
fi

# ── Traffic placeholder (Plausible / Analytics) ───────────────────────────────
# If you have a Plausible API token, set PLAUSIBLE_TOKEN and PLAUSIBLE_SITE_ID
PLAUSIBLE_TOKEN="${PLAUSIBLE_TOKEN:-}"
PLAUSIBLE_SITE_ID="${PLAUSIBLE_SITE_ID:-agentskillshub.top}"
WEEKLY_VISITORS="N/A"
WEEKLY_PAGEVIEWS="N/A"

if [[ -n "$PLAUSIBLE_TOKEN" ]]; then
  echo "  Querying Plausible..." >&2
  PLAUSIBLE_DATA="$(curl -s "https://plausible.io/api/v1/stats/aggregate?site_id=${PLAUSIBLE_SITE_ID}&period=custom&date=${WEEK_START},${WEEK_END}&metrics=visitors,pageviews" \
    -H "Authorization: Bearer ${PLAUSIBLE_TOKEN}" 2>/dev/null || echo '{}')"
  WEEKLY_VISITORS="$(echo "$PLAUSIBLE_DATA" | jq -r '.results.visitors.value // "N/A"')"
  WEEKLY_PAGEVIEWS="$(echo "$PLAUSIBLE_DATA" | jq -r '.results.pageviews.value // "N/A"')"
fi

# ── Load previous week's data for comparison ──────────────────────────────────
PREV_TOTAL_SKILLS=0; PREV_NEW_SKILLS=0; PREV_VERIFIED_SUBS=0; PREV_TOTAL_SUBS=0
PREV_GH_STARS=0; PREV_GH_FORKS=0; PREV_SCENARIO_PAGES=0; PREV_MERGED_PRS=0
PREV_COMMITS=0; PREV_SKILL_MASTERS=0

if [[ -f "$PREV_FILE" ]]; then
  echo "  Loading previous week data from $PREV_FILE..." >&2
  PREV_TOTAL_SKILLS="$(jq -r '.total_skills // 0' "$PREV_FILE")"
  PREV_NEW_SKILLS="$(jq -r '.new_skills // 0' "$PREV_FILE")"
  PREV_VERIFIED_SUBS="$(jq -r '.verified_subs // 0' "$PREV_FILE")"
  PREV_TOTAL_SUBS="$(jq -r '.total_subs // 0' "$PREV_FILE")"
  PREV_GH_STARS="$(jq -r '.gh_stars // 0' "$PREV_FILE")"
  PREV_GH_FORKS="$(jq -r '.gh_forks // 0' "$PREV_FILE")"
  PREV_SCENARIO_PAGES="$(jq -r '.scenario_pages // 0' "$PREV_FILE")"
  PREV_MERGED_PRS="$(jq -r '.merged_prs // 0' "$PREV_FILE")"
  PREV_COMMITS="$(jq -r '.commits // 0' "$PREV_FILE")"
  PREV_SKILL_MASTERS="$(jq -r '.skill_masters // 0' "$PREV_FILE")"
else
  echo "  No previous data found — first run, showing absolute values only." >&2
fi

# ── Change calculation helper ─────────────────────────────────────────────────
calc_change() {
  local current="$1"
  local previous="$2"
  local diff=$(( current - previous ))
  if [[ "$previous" -eq 0 ]]; then
    if [[ "$diff" -eq 0 ]]; then
      echo "—"
    else
      echo "+${diff} (new)"
    fi
  else
    local pct
    pct="$(echo "scale=1; ($diff * 100) / $previous" | bc 2>/dev/null || echo "0")"
    if [[ "$diff" -ge 0 ]]; then
      echo "+${diff} (+${pct}%)"
    else
      echo "${diff} (${pct}%)"
    fi
  fi
}

format_number() {
  printf "%'d" "$1" 2>/dev/null || echo "$1"
}

# ── Goals configuration ──────────────────────────────────────────────────────
# Adjust these targets as the project grows
GOAL_NEW_SUBS_WEEK=10
GOAL_SKILLS_TOTAL=50000
GOAL_STARS=200
GOAL_SCENARIO_PAGES=60

goal_status() {
  local actual="$1"
  local target="$2"
  if [[ "$target" -eq 0 ]]; then echo "—"; return; fi
  local pct
  pct="$(echo "scale=0; ($actual * 100) / $target" | bc 2>/dev/null || echo 0)"
  if [[ "$pct" -ge 100 ]]; then
    echo "🟢 ${pct}%"
  elif [[ "$pct" -ge 60 ]]; then
    echo "🟡 ${pct}%"
  else
    echo "🔴 ${pct}%"
  fi
}

# New subscribers this week = current verified - previous verified
NEW_SUBS_THIS_WEEK=$(( VERIFIED_SUBS - PREV_VERIFIED_SUBS ))
if [[ "$NEW_SUBS_THIS_WEEK" -lt 0 ]]; then NEW_SUBS_THIS_WEEK=0; fi

# ── Generate the scorecard ────────────────────────────────────────────────────
SCORECARD="$(cat <<SCORECARD_EOF
# Agent Skills Hub — Weekly Scorecard
## Week of ${WEEK_START_LABEL} – ${WEEK_END_LABEL}

---

### 📊 Key Metrics

| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| Total Skills | $(format_number "$TOTAL_SKILLS") | $(format_number "$PREV_TOTAL_SKILLS") | $(calc_change "$TOTAL_SKILLS" "$PREV_TOTAL_SKILLS") |
| New Skills | $(format_number "$NEW_SKILLS") | $(format_number "$PREV_NEW_SKILLS") | $(calc_change "$NEW_SKILLS" "$PREV_NEW_SKILLS") |
| Verified Subscribers | ${VERIFIED_SUBS} | ${PREV_VERIFIED_SUBS} | $(calc_change "$VERIFIED_SUBS" "$PREV_VERIFIED_SUBS") |
| Total Subscribers | ${TOTAL_SUBS} | ${PREV_TOTAL_SUBS} | $(calc_change "$TOTAL_SUBS" "$PREV_TOTAL_SUBS") |
| GitHub Stars | ${GH_STARS} | ${PREV_GH_STARS} | $(calc_change "$GH_STARS" "$PREV_GH_STARS") |
| GitHub Forks | ${GH_FORKS} | ${PREV_GH_FORKS} | $(calc_change "$GH_FORKS" "$PREV_GH_FORKS") |
| Scenario Pages | ${SCENARIO_PAGES} | ${PREV_SCENARIO_PAGES} | $(calc_change "$SCENARIO_PAGES" "$PREV_SCENARIO_PAGES") |
| Skill Masters | ${SKILL_MASTERS} | ${PREV_SKILL_MASTERS} | $(calc_change "$SKILL_MASTERS" "$PREV_SKILL_MASTERS") |

### 🚀 Development Activity

| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| Commits | ${COMMITS_THIS_WEEK} | ${PREV_COMMITS} | $(calc_change "$COMMITS_THIS_WEEK" "$PREV_COMMITS") |
| PRs Merged | ${MERGED_PRS} | ${PREV_MERGED_PRS} | $(calc_change "$MERGED_PRS" "$PREV_MERGED_PRS") |
| Open Issues | ${GH_OPEN_ISSUES} | — | — |

### 🌐 Traffic (Plausible)

| Metric | This Week |
|--------|-----------|
| Visitors | ${WEEKLY_VISITORS} |
| Pageviews | ${WEEKLY_PAGEVIEWS} |

> Set \`PLAUSIBLE_TOKEN\` env var to enable real traffic data.

### 🎯 Goals vs Actual

| Goal | Target | Actual | Status |
|------|--------|--------|--------|
| New subscribers/week | ${GOAL_NEW_SUBS_WEEK} | ${NEW_SUBS_THIS_WEEK} | $(goal_status "$NEW_SUBS_THIS_WEEK" "$GOAL_NEW_SUBS_WEEK") |
| Total skills indexed | $(format_number "$GOAL_SKILLS_TOTAL") | $(format_number "$TOTAL_SKILLS") | $(goal_status "$TOTAL_SKILLS" "$GOAL_SKILLS_TOTAL") |
| GitHub stars | ${GOAL_STARS} | ${GH_STARS} | $(goal_status "$GH_STARS" "$GOAL_STARS") |
| Scenario pages | ${GOAL_SCENARIO_PAGES} | ${SCENARIO_PAGES} | $(goal_status "$SCENARIO_PAGES" "$GOAL_SCENARIO_PAGES") |

### 📦 Community

| Metric | Count |
|--------|-------|
| Pending submissions | ${EXTRA_REPOS_PENDING} |
| Approved submissions | ${EXTRA_REPOS_APPROVED} |
| Top trending velocity | ${TOP_VELOCITY} stars/week |

---

*Generated $(date '+%Y-%m-%d %H:%M') by weekly-scorecard.sh*
SCORECARD_EOF
)"

# ── Output ────────────────────────────────────────────────────────────────────
if [[ "$DRY_RUN" == true ]]; then
  echo "$SCORECARD"
  echo "" >&2
  echo "Dry run — not saving files." >&2
  exit 0
fi

# Save the scorecard
mkdir -p "$OUTPUT_DIR"
SCORECARD_FILE="$OUTPUT_DIR/scorecard-${TODAY}.md"
echo "$SCORECARD" > "$SCORECARD_FILE"
echo "" >&2
echo "Scorecard saved to: $SCORECARD_FILE" >&2

# Save current data as previous for next week's comparison
cat > "$PREV_FILE" <<JSON_EOF
{
  "week_end": "${WEEK_END}",
  "generated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "total_skills": ${TOTAL_SKILLS},
  "new_skills": ${NEW_SKILLS},
  "verified_subs": ${VERIFIED_SUBS},
  "total_subs": ${TOTAL_SUBS},
  "gh_stars": ${GH_STARS},
  "gh_forks": ${GH_FORKS},
  "scenario_pages": ${SCENARIO_PAGES},
  "skill_masters": ${SKILL_MASTERS},
  "merged_prs": ${MERGED_PRS},
  "commits": ${COMMITS_THIS_WEEK},
  "extra_repos_pending": ${EXTRA_REPOS_PENDING},
  "extra_repos_approved": ${EXTRA_REPOS_APPROVED},
  "top_velocity": ${TOP_VELOCITY},
  "weekly_visitors": "${WEEKLY_VISITORS}",
  "weekly_pageviews": "${WEEKLY_PAGEVIEWS}"
}
JSON_EOF

echo "Previous-week data saved to: $PREV_FILE" >&2
echo "" >&2
echo "Done! Run 'cat $SCORECARD_FILE' to view." >&2
