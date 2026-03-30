#!/bin/bash
# Badge Outreach Script
# Generates a list of top repos to add Agent Skills Hub badge
# Usage: ./ops/badge-outreach.sh [--dry-run] [--limit N]
#
# Strategy: Start with repos that already reference agentskillshub.top
# or have "agent skill" in their description, then expand to top starred repos.
#
# IMPORTANT: Do NOT auto-submit PRs. Review each repo manually.
# Submitting too many PRs too fast = flagged as spam.

set -e

LIMIT=${2:-20}
DRY_RUN=${1:-"--dry-run"}
BADGE_BASE="https://agentskillshub.top/badge"
SITE_BASE="https://agentskillshub.top/skill"
SUPABASE_URL="https://vknzzecmzsfmohglpfgm.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrbnp6ZWNtenNmbW9oZ2xwZmdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4MDQ3MzIsImV4cCI6MjA4ODM4MDczMn0.zFAGZH-lDcL-GwyMkR-9sSV8pJToVzomsJ_fuXZIoDo"

echo "🏷️  Badge Outreach — Generating target list"
echo "   Limit: $LIMIT repos"
echo ""

# Fetch top repos by score (quality + stars)
REPOS=$(curl -s "${SUPABASE_URL}/rest/v1/skills?select=repo_full_name,stars,score,category&order=score.desc,stars.desc&limit=${LIMIT}" \
  -H "apikey: ${SUPABASE_KEY}" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data:
    name = r['repo_full_name']
    stars = r['stars']
    score = r['score']
    cat = r['category']
    print(f'{name}|{stars}|{score}|{cat}')
")

echo "| # | Repo | Stars | Score | Badge Markdown |"
echo "|---|------|-------|-------|----------------|"

i=0
echo "$REPOS" | while IFS='|' read -r name stars score cat; do
  i=$((i+1))
  owner=$(echo "$name" | cut -d/ -f1)
  repo=$(echo "$name" | cut -d/ -f2)
  badge_md="[![Agent Skills Hub](${BADGE_BASE}/${owner}/${repo}.svg)](${SITE_BASE}/${owner}/${repo}/)"
  echo "| $i | [$name](https://github.com/$name) | ⭐$stars | $score | \`$badge_md\` |"
done

echo ""
echo "---"
echo "📋 To submit a PR to a repo:"
echo ""
echo "  1. Fork the repo"
echo "  2. Add badge to README.md (usually after the title/description)"
echo "  3. Create PR with title: 'Add Agent Skills Hub badge'"
echo "  4. PR body template:"
echo ""
cat << 'TEMPLATE'
Hi! 👋

[Agent Skills Hub](https://agentskillshub.top) is an open-source directory of 42,000+ AI agent tools, MCP servers, and Claude Code skills.

Your project is listed and ranked on our platform. This PR adds a badge to your README that links to your project's page on Agent Skills Hub, where users can discover your tool alongside related alternatives.

**Badge preview:**
![Agent Skills Hub](https://agentskillshub.top/badge/{owner}/{repo}.svg)

Feel free to customize the badge placement. No obligation to merge — just thought it might help with discoverability!
TEMPLATE
