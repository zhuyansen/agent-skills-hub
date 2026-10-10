#!/bin/bash
# Checkpoint for the skill-manager test: how many tokens Claude Code sends before you type
# anything, and which agent folders hold which skills. Usage: bash /in/measure.sh <label>
label="$1"; out=/out/measure-$label.json
# Outside the agent's session: no CLAUDECODE markers, and the token the harness saved (the
# agent's shell does not inherit it). Errors go to /out so a 0 is never silent again.
usage=$(cd /tmp && env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT -u CLAUDE_CODE_MESSAGING_SOCKET -u CLAUDE_CODE_MESSAGING_TOKEN \
  CLAUDE_CODE_OAUTH_TOKEN="$(cat ~/.measure_token 2>/dev/null)" \
  claude -p "Reply with the single word OK." --output-format json --model haiku 2>"/out/measure-$label.err")
python3 - "$label" "$out" <<PY
import json, os, sys, glob
label, out = sys.argv[1], sys.argv[2]
try:
    u = json.loads('''$usage''').get("usage", {})
except Exception:
    u = {}
total = sum(u.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
home = os.path.expanduser("~")
dirs = {d: sorted(os.listdir(os.path.join(home, d))) for d in (".claude/skills", ".codex/skills", ".agents/skills", ".cursor/skills", ".gemini/skills") if os.path.isdir(os.path.join(home, d))}
claude_md = os.path.join(home, ".claude/CLAUDE.md")
json.dump({"label": label, "context_tokens": total, "skills": dirs,
           "claude_md_bytes": os.path.getsize(claude_md) if os.path.exists(claude_md) else 0,
           "mcp": os.popen("claude mcp list 2>/dev/null").read().strip()[:2000]}, open(out, "w"), indent=1)
print(f"{label}: {total} context tokens, {len(dirs.get('.claude/skills', []))} skills in ~/.claude/skills")
PY
