#!/bin/bash
# Post-tool hook: run TypeScript check on frontend files after edit
# Only triggers on .ts/.tsx files, non-blocking (exit 0 always)

set -uo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Parse file_path from stdin JSON
FILE_PATH=$(cat | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    path = data.get('tool_input', {}).get('file_path', '')
    print(path)
except:
    print('')
" 2>/dev/null)

# Skip if not a TypeScript frontend file
case "$FILE_PATH" in
  "$FRONTEND_DIR"/*.ts|"$FRONTEND_DIR"/*.tsx)
    ;;
  *)
    exit 0
    ;;
esac

# Run tsc --noEmit, output errors to stderr for Claude to see
cd "$FRONTEND_DIR"
ERRORS=$(npx tsc --noEmit 2>&1 | grep -c "error TS" || true)

if [ "$ERRORS" -gt 0 ]; then
  echo "{\"hookSpecificOutput\":{\"additionalContext\":\"TypeScript has $ERRORS error(s). Run 'npx tsc --noEmit' to see details.\"}}"
fi

exit 0
