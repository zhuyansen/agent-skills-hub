#!/bin/bash
# Pre-tool hook: warn before editing critical files
# Returns exit 2 to block if needed (currently just warns)

set -uo pipefail

FILE_PATH=$(cat | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    path = data.get('tool_input', {}).get('file_path', '')
    print(path)
except:
    print('')
" 2>/dev/null)

[ -z "$FILE_PATH" ] && exit 0

BASENAME=$(basename "$FILE_PATH")

# Critical files that need extra care
case "$BASENAME" in
  supabaseClient.ts|email_service.py|sync_runner.py)
    echo "{\"hookSpecificOutput\":{\"additionalContext\":\"WARNING: $BASENAME is a critical file (RLS/email/sync). Double-check changes carefully.\"}}"
    ;;
esac

exit 0
