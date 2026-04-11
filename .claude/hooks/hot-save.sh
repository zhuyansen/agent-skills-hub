#!/bin/bash
# Stop hook: update memory/hot.md with session summary
# Runs at end of each conversation to preserve working context
# Uses Claude's own transcript summary (passed via stdin) to extract key facts

set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
HOT_FILE="$PROJECT_DIR/memory/hot.md"
MEMORY_DIR="$PROJECT_DIR/memory"

# Ensure memory directory exists
mkdir -p "$MEMORY_DIR"

# Read the stop hook input (contains transcript_summary)
INPUT=$(cat 2>/dev/null || echo "{}")

# Extract summary from stdin JSON
SUMMARY=$(echo "$INPUT" | python3 -c "
import sys, json
from datetime import datetime
try:
    data = json.load(sys.stdin)
    summary = data.get('transcript_summary', '')
    if not summary:
        # Fallback: try to get from stop_hook_data
        summary = data.get('stop_hook_data', {}).get('summary', '')
    if summary:
        print(summary[:1500])
    else:
        print('')
except Exception:
    print('')
" 2>/dev/null)

# If we got a summary, update hot.md
if [ -n "$SUMMARY" ] && [ ${#SUMMARY} -gt 20 ]; then
    TIMESTAMP=$(date -u '+%Y-%m-%d %H:%M UTC')
    cat > "$HOT_FILE" <<HOTEOF
# Hot Cache — Agent Skills Hub
> Auto-updated: ${TIMESTAMP}
> This file is read at session start to restore working context.

## Last Session Summary
${SUMMARY}

## Active Work Streams
<!-- Updated by Stop hook based on session activity -->
- Check memory/daily-report-archive.md for dedup before generating reports
- Check CLAUDE.md for coding conventions and hard stops
- Frontend deploys via GitHub Pages on push to main
- Backend changes take effect on next sync cycle (every 8h)

## Key Numbers
- Skills in DB: 25000+
- Newsletter subscribers: 58 verified
- Deploy: GitHub Pages at agentskillshub.top
HOTEOF
    exit 0
fi

# If no summary available, preserve existing hot.md but update timestamp
if [ -f "$HOT_FILE" ]; then
    # Just touch the file, keep existing content
    exit 0
fi

# First time: create a seed hot.md
cat > "$HOT_FILE" <<HOTEOF
# Hot Cache — Agent Skills Hub
> Auto-updated: $(date -u '+%Y-%m-%d %H:%M UTC')
> This file is read at session start to restore working context.

## Last Session Summary
No previous session recorded yet.

## Active Work Streams
- Daily report generation (check archive for dedup)
- Frontend: React 19 + Vite, deploy to GitHub Pages
- Backend: FastAPI + Supabase, sync every 8h
- Newsletter: weekly on Mondays via Resend

## Key Numbers
- Skills in DB: 25000+
- Newsletter subscribers: 58 verified
- Deploy: GitHub Pages at agentskillshub.top
HOTEOF

exit 0
