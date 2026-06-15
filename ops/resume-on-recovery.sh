#!/usr/bin/env bash
# Health-gated auto-resume: wait until Supabase genuinely recovers (3 consecutive
# real-catalog-query successes), then ONE clean deploy + ONE sync. No retriggering.
set -u
KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrbnp6ZWNtenNmbW9oZ2xwZmdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4MDQ3MzIsImV4cCI6MjA4ODM4MDczMn0.zFAGZH-lDcL-GwyMkR-9sSV8pJToVzomsJ_fuXZIoDo"
BASE="https://vknzzecmzsfmohglpfgm.supabase.co/rest/v1/skills"
# Probe with the build's ACTUAL 300-row page query, and gate on genuinely-fast
# responses. The 13:45 "recovery" was a false positive — 7s probes passed a
# <15s gate but the build then 57014'd because the DB was still warming. This
# time: 300-row query must return <4s, FOUR consecutive times, before we deploy.
PROBE="${BASE}?select=id,repo_full_name,stars,description,category&order=id.asc&id=gt.0&limit=300"
cd /Users/zhuyansen/content/agent-skills-hub || exit 1

# ── Phase 0: strict health gate (read-only; 45s spacing to catch recovery promptly) ──
ok=0; tries=0; MAX=120; NEED=4; THRESH=2
while [ "$tries" -lt "$MAX" ]; do
  tries=$((tries+1))
  R=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" -m 15 -H "apikey: $KEY" -H "Authorization: Bearer $KEY" "$PROBE")
  CODE=${R% *}; T=${R#* }
  if [ "$CODE" = "200" ] && [ "$(python3 -c "print(1 if $T < $THRESH else 0)" 2>/dev/null)" = "1" ]; then ok=$((ok+1)); else ok=0; fi
  echo "$(date +%H:%M:%S) probe=$R ok=$ok/$NEED"
  [ "$ok" -ge "$NEED" ] && break
  sleep 45
done
if [ "$ok" -lt "$NEED" ]; then echo "TIMEOUT: Supabase 探了 $tries 次仍未稳定恢复（<${THRESH}s×${NEED}），停下不动作"; exit 0; fi
echo "$(date +%H:%M:%S) Supabase 真恢复 ✓（300行 <${THRESH}s ×${NEED}）"

# ── Phase 1: push → clean deploy ──
git push 2>&1 | tail -1
sleep 6
DID=$(gh run list --workflow=deploy.yml --limit 1 --json databaseId --jq '.[0].databaseId')
echo "$(date +%H:%M:%S) deploy=$DID"
while true; do
  DS=$(gh run view "$DID" --json status,conclusion --jq '"\(.status)/\(.conclusion)"' 2>/dev/null)
  echo "$(date +%H:%M:%S) deploy=$DS"
  case "$DS" in completed/*) break;; esac
  sleep 40
done
if [ "$DS" != "completed/success" ]; then echo "deploy 未成功: $DS — 停下，等人工"; exit 0; fi

# verify npm command live
sleep 20
JS=$(curl -s https://agentskillshub.top/ | grep -oE '/assets/index-[A-Za-z0-9_-]+\.js' | head -1)
curl -s "https://agentskillshub.top${JS}" -o /tmp/ash_verify.js
echo "首页 @agentskillshub/cli 出现: $(grep -o '@agentskillshub/cli' /tmp/ash_verify.js | wc -l | tr -d ' ') · 旧 github: $(grep -o 'github:zhuyansen/agentskillshub-cli' /tmp/ash_verify.js | wc -l | tr -d ' ')"
rm -f /tmp/ash_verify.js

# ── Phase 2 DEFERRED: do NOT chain sync right after deploy. ──
# sync is heavier (writes + scan) than the read-only build. Running it
# back-to-back on a just-recovered IO budget risks re-throttling. Stop here;
# sync runs separately once the instance is confirmed stable post-deploy.
echo "=== deploy 上线 ✓ — sync 暂缓(不背靠背压实例,稍后单独跑)==="
