#!/bin/bash
# SessionStart hook: inject hot.md context for cross-session memory
# Reads memory/hot.md and outputs as additionalContext so Claude sees it immediately

set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
HOT_FILE="$PROJECT_DIR/memory/hot.md"

# Skip if hot.md doesn't exist or is empty
[ ! -f "$HOT_FILE" ] && exit 0
[ ! -s "$HOT_FILE" ] && exit 0

# Use Python for reliable JSON escaping
python3 -c "
import json, sys

with open('$HOT_FILE', 'r') as f:
    content = f.read()[:2000]

result = {
    'hookSpecificOutput': {
        'additionalContext': '[HOT CACHE] Project working memory from last session:\\n' + content
    }
}
print(json.dumps(result))
" 2>/dev/null

exit 0
