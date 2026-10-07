#!/bin/bash
# Run one skill inside the sandbox: install it, have Claude Code build the deck
# from the shared brief, render what it made. Args: <owner/repo>. Outputs go to /out.
set -u
REPO="$1"; OUT=/out; mkdir -p "$OUT" ~/.claude/skills
git clone --depth 1 "https://github.com/$REPO.git" ~/src 2>&1 | tail -1
cd ~/src && git rev-parse HEAD > "$OUT/commit.txt"; cd ~/work
# Install every SKILL.md folder; a repo may ship several.
find ~/src -name SKILL.md -not -path '*/node_modules/*' | while read -r f; do
  d=$(dirname "$f"); n=$(basename "$d"); [ "$d" = ~/src ] && n=$(basename "$REPO")
  cp -r "$d" ~/.claude/skills/"$n"; echo "$n" >> "$OUT/skills.txt"
done
# No SKILL.md: a Claude Code plugin is copied in; anything else (an MCP server, a
# README-only repo) is installed by the agent in a separate session first, so that
# what it registers (e.g. `claude mcp add`) is live in the deck session.
if [ ! -s "$OUT/skills.txt" ]; then
  if [ -f ~/src/.claude-plugin/plugin.json ]; then
    for k in commands agents skills; do [ -d ~/src/$k ] && mkdir -p ~/.claude/$k && cp -r ~/src/$k/* ~/.claude/$k/; done
    echo "plugin" > "$OUT/install.txt"
  else
    timeout 15m claude -p "$(cat /in/setup_prompt.txt)" --model "${CLAUDE_MODEL:-opus}" --dangerously-skip-permissions \
      --output-format stream-json --verbose > "$OUT/setup.jsonl" 2>> "$OUT/claude.err"
    echo "agent-setup" > "$OUT/install.txt"
  fi
fi
cp /in/brief.md ~/work/brief.md
# Image models: an OpenAI-compatible adapter in front of the async provider (image_proxy.py).
if [ -n "${IMAGE_API_KEY:-}" ]; then
  python3 ~/bin/image_proxy.py & sleep 1
  export OPENAI_BASE_URL=http://127.0.0.1:8787/v1 OPENAI_API_KEY=sk-sandbox-proxy
fi
PROMPT=$(cat /in/prompt.txt)
timeout "${RUN_MINUTES:-30}m" claude -p "$PROMPT" --model "${CLAUDE_MODEL:-opus}" \
  --dangerously-skip-permissions --output-format stream-json --verbose > "$OUT/transcript.jsonl" 2> "$OUT/claude.err"
echo $? > "$OUT/exit.txt"
python3 ~/bin/render.py ~/work "$OUT"
