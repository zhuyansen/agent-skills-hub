#!/bin/bash
# Pre-tool hook: scan file content for secrets/credentials before Write/Edit
# Blocks (exit 2) if high-confidence secrets found in new_string or content
# Uses Python regex for reliable pattern matching (no grep quirks)

set -uo pipefail

RESULT=$(cat | python3 -c "
import sys, json, re

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

inp = data.get('tool_input', {})
file_path = inp.get('file_path', '')
content = inp.get('new_string', '') or inp.get('content', '')

if not file_path or not content:
    sys.exit(0)

# Only scan source code extensions
import os
ext = os.path.splitext(file_path)[1].lower()
SCAN_EXTS = {'.ts','.tsx','.js','.jsx','.py','.sh','.json','.yaml','.yml',
             '.toml','.env','.md','.sql','.html','.css','.conf','.cfg',
             '.pem','.key','.txt','.ini','.xml','.properties'}
if ext not in SCAN_EXTS and '.env' not in os.path.basename(file_path):
    sys.exit(0)

# ── High-confidence patterns (BLOCK) ──
BLOCK_PATTERNS = [
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
    (r'ghp_[0-9a-zA-Z]{36}', 'GitHub PAT'),
    (r'github_pat_[0-9a-zA-Z_]{82}', 'GitHub Fine-grained PAT'),
    (r'xox[bpors]-[0-9a-zA-Z-]{10,}', 'Slack Token'),
    (r'sk_live_[0-9a-zA-Z]{24,}', 'Stripe Live Key'),
    (r'-----BEGIN[A-Z ]*PRIVATE KEY-----', 'Private Key'),
    (r're_[0-9a-zA-Z]{20,}', 'Resend API Key'),
    (r'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6', 'Supabase Service Role JWT'),
    (r'sk-[0-9a-zA-Z]{32,}', 'OpenAI API Key'),
    (r'AIza[0-9A-Za-z_-]{35}', 'Google API Key'),
]

for pattern, label in BLOCK_PATTERNS:
    m = re.search(pattern, content)
    if m:
        snippet = m.group()[:20]
        result = {
            'decision': 'block',
            'reason': f'Secret detected: {snippet}... ({label}) — Use env variables instead of hardcoding.'
        }
        print(json.dumps(result))
        sys.exit(2)

# ── Medium-confidence patterns (WARN) ──
WARN_PATTERNS = [
    r'(?i)(api_key|apikey|api_secret|secret_key)\s*[=:]\s*[\"\\x27][0-9a-zA-Z]{20,}',
    r'(?i)(password|passwd|pwd)\s*[=:]\s*[\"\\x27][^\s\"\\x27]{8,}',
    r'(?i)(token|auth_token|access_token)\s*[=:]\s*[\"\\x27][0-9a-zA-Z_-]{20,}',
]

for pattern in WARN_PATTERNS:
    if re.search(pattern, content):
        result = {
            'hookSpecificOutput': {
                'additionalContext': 'Possible hardcoded credential found. Consider using env variables instead of hardcoded secrets.'
            }
        }
        print(json.dumps(result))
        break

sys.exit(0)
" 2>/dev/null)

EXIT_CODE=$?

if [ -n "$RESULT" ]; then
  echo "$RESULT"
fi

exit $EXIT_CODE
