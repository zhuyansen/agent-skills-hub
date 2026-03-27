#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Agent Skills Hub — 日报自动化流水线
#
# 用法：
#   ./ops/daily-report.sh              # 完整流水线
#   ./ops/daily-report.sh --data-only  # 仅采集数据
#   ./ops/daily-report.sh --trend-only # 仅拉 TrendRadar 热点
#
# 流水线：
#   ① TrendRadar 热点采集（如有 Docker）
#   ② Supabase 新 Skills 查询
#   ③ feedgrab 热门链接抓取（可选）
#   ④ 输出素材到 ops/daily-data/YYYY-MM-DD/
#
# 最终日报由 Claude Code 基于素材生成（人工确认后发布）
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# ── 配置 ──
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)
TWO_DAYS_AGO=$(date -v-2d +%Y-%m-%d 2>/dev/null || date -d "2 days ago" +%Y-%m-%d)
OUTPUT_DIR="$PROJECT_ROOT/ops/daily-data/$TODAY"
mkdir -p "$OUTPUT_DIR"

SUPABASE_URL="https://vknzzecmzsfmohglpfgm.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrbnp6ZWNtenNmbW9oZ2xwZmdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4MDQ3MzIsImV4cCI6MjA4ODM4MDczMn0.zFAGZH-lDcL-GwyMkR-9sSV8pJToVzomsJ_fuXZIoDo"

echo "📅 日报素材采集 — $TODAY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── ① Supabase: 最近 48h 新收录 Skills（按 stars 降序） ──
echo "📊 [1/3] 拉取 Supabase 新 Skills..."
curl -s "${SUPABASE_URL}/rest/v1/skills?select=repo_full_name,description,stars,prev_stars,star_momentum,category,first_seen,created_at,author_name,is_official&order=stars.desc&limit=50&first_seen=gte.${TWO_DAYS_AGO}T00:00:00&stars=gt.0" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}" \
  > "$OUTPUT_DIR/new-skills.json" 2>/dev/null

NEW_COUNT=$(python3 -c "import json; print(len(json.load(open('$OUTPUT_DIR/new-skills.json'))))" 2>/dev/null || echo 0)
echo "   ✅ 新 Skills: $NEW_COUNT 个"

# ── ② Supabase: 高增速 Skills（momentum > 0, 按增速排序） ──
echo "📈 [2/3] 拉取高增速 Skills..."
curl -s "${SUPABASE_URL}/rest/v1/skills?select=repo_full_name,description,stars,prev_stars,star_momentum,category,first_seen,created_at,author_name,is_official&order=star_momentum.desc.nullslast&limit=30&star_momentum=gt.0" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}" \
  > "$OUTPUT_DIR/top-momentum.json" 2>/dev/null

MOMENTUM_COUNT=$(python3 -c "import json; print(len(json.load(open('$OUTPUT_DIR/top-momentum.json'))))" 2>/dev/null || echo 0)
echo "   ✅ 高增速 Skills: $MOMENTUM_COUNT 个"

# ── ③ TrendRadar 热点（如果有运行） ──
echo "🔥 [3/3] 检查 TrendRadar 热点..."
TRENDRADAR_DIR="/Users/zhuyansen/TrendRadar/output"
if [ -d "$TRENDRADAR_DIR" ]; then
  LATEST_DB=$(find "$TRENDRADAR_DIR" -name "*.db" -type f 2>/dev/null | sort -r | head -1)
  if [ -n "$LATEST_DB" ]; then
    cp "$LATEST_DB" "$OUTPUT_DIR/trendradar.db" 2>/dev/null && echo "   ✅ TrendRadar 数据已复制" || echo "   ⚠️  TrendRadar 数据复制失败"
  else
    echo "   ⏭  TrendRadar 暂无数据（需先启动 Docker）"
  fi

  # 也复制最新 HTML 报告
  LATEST_HTML=$(find "$TRENDRADAR_DIR" -name "*.html" -type f 2>/dev/null | sort -r | head -1)
  if [ -n "$LATEST_HTML" ]; then
    cp "$LATEST_HTML" "$OUTPUT_DIR/trend-report.html" 2>/dev/null
    echo "   ✅ 热点报告已复制"
  fi
else
  echo "   ⏭  TrendRadar 未安装或未运行"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 素材采集完成！"
echo "📁 输出目录: $OUTPUT_DIR"
echo ""
echo "文件列表:"
ls -la "$OUTPUT_DIR/"
echo ""
echo "💡 下一步: 在 Claude Code 中说「日报」，我会基于这些素材生成报告"
