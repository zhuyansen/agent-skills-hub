#!/bin/bash
# Post-tool hook: auto-format frontend files with prettier
# Reads JSON from stdin, extracts file_path, runs prettier if applicable

set -euo pipefail
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

# Skip if no file path
[ -z "$FILE_PATH" ] && exit 0

# Only format frontend files with known extensions
case "$FILE_PATH" in
  "$FRONTEND_DIR"/*.ts|"$FRONTEND_DIR"/*.tsx|"$FRONTEND_DIR"/*.js|"$FRONTEND_DIR"/*.jsx|"$FRONTEND_DIR"/*.css|"$FRONTEND_DIR"/*.json)
    ;;
  *)
    exit 0
    ;;
esac

# Skip if file doesn't exist (deleted)
[ ! -f "$FILE_PATH" ] && exit 0

# Run prettier
cd "$FRONTEND_DIR"
npx prettier --write "$FILE_PATH" >/dev/null 2>&1

exit 0
