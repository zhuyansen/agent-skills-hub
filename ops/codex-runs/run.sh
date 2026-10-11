#!/bin/bash
# The trigger test: one sandbox per agent, all 12 skills installed, 42 prompts each.
#   [FILLERS=100] bash ops/codex-runs/run.sh codex|claude     (FILLERS: other real skills installed beside the 12)
# Codex runs gpt-6-astra through FlatRouter's Responses API; Claude Code runs Claude Opus on the subscription.
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"; AGENT="$1"; mkdir -p "$HERE/out"
key() { grep "^$1=" ~/.claude/.env | head -1 | cut -d= -f2- | tr -d '"'; }
docker run --rm --name "trigger-$AGENT-${FILLERS:-0}" --entrypoint python3 -e FILLERS="${FILLERS:-0}" \
  -e FLATROUTER_API_KEY="$(key FLATROUTER_API_KEY)" -e CLAUDE_CODE_OAUTH_TOKEN="$(key CLAUDE_CODE_OAUTH_TOKEN)" \
  -v "$HERE/in:/in:ro" -v "$HERE/out:/out" pptrun:1 /in/trigger.py "$AGENT"
