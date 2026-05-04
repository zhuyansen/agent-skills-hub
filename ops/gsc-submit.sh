#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# GSC Request-Indexing 辅助工具（方案一 · 手动粘贴版）
#
# GSC 的 "请求编入索引" 没有公开深链——URL 必须手动在搜索框粘贴。
# 本工具只做一件事：把今天 Top 10 URL 整理干净 + 复制到剪贴板，
# 然后自动打开 GSC 首页。你去顶部搜索框粘 → 回车 → 点按钮，
# 重复 10 次（每个约 30 秒 · 总 5 分钟）。
#
# 用法 1 · 从 owner/repo 列表：
#   ./ops/gsc-submit.sh \
#     owner1/repo1 owner2/repo2 ... owner10/repo10
#
# 用法 2 · 从 IndexNow 的 --urls 逗号字符串：
#   ./ops/gsc-submit.sh --from-urls \
#     "https://agentskillshub.top/skill/a/b/,..."
#
# 用法 3 · 不打开浏览器，只生成 markdown：
#   ./ops/gsc-submit.sh --no-open owner1/repo1 ...
#
# 产出：
#   ops/daily-data/YYYY-MM-DD/gsc-today.md  · 10 个 URL 的 markdown 清单
#   剪贴板 · 10 个 URL 一次性复制（macOS pbcopy）
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TODAY=$(date +%Y-%m-%d)
OUT_DIR="$PROJECT_ROOT/ops/daily-data/$TODAY"
mkdir -p "$OUT_DIR"

SITE="agentskillshub.top"
GSC_HOME="https://search.google.com/search-console/"

OPEN_BROWSER=1
FROM_URLS=""
REPOS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-open) OPEN_BROWSER=0; shift ;;
    --from-urls) FROM_URLS="$2"; shift 2 ;;
    -*) echo "unknown flag: $1" >&2; exit 1 ;;
    *) REPOS+=("$1"); shift ;;
  esac
done

# If --from-urls was passed, extract owner/repo from each URL
if [[ -n "$FROM_URLS" ]]; then
  IFS=',' read -ra URL_ARR <<< "$FROM_URLS"
  for url in "${URL_ARR[@]}"; do
    path="${url#https://${SITE}/skill/}"
    path="${path%/}"
    REPOS+=("$path")
  done
fi

if [[ ${#REPOS[@]} -eq 0 ]]; then
  echo "ERR: 需要传入 owner/repo 或 --from-urls" >&2
  echo "示例: $0 alchaincyf/hermes-agent-orange-book TesslateAI/OpenSail ..." >&2
  exit 1
fi

MD_FILE="$OUT_DIR/gsc-today.md"

# ── Build URL list ────────────────────────────────
URLS=()
for repo in "${REPOS[@]}"; do
  URLS+=("https://${SITE}/skill/${repo}/")
done

# ── Generate Markdown ────────────────────────────────
{
  echo "# GSC 请求编入索引 · $TODAY"
  echo ""
  echo "## 操作步骤"
  echo ""
  echo "1. 在 GSC 顶部搜索框粘贴下面一条 URL → 回车"
  echo "2. 等 20-30 秒等检测完成"
  echo "3. 点蓝色的 **"请求编入索引"** 按钮"
  echo "4. 关掉弹窗，返回第 1 步粘下一条"
  echo ""
  echo "⏱️  全部 10 个约 5 分钟。URL 已经复制到剪贴板（macOS）。"
  echo ""
  echo "## 今日 10 个 URL"
  echo ""
  echo '```'
  printf '%s\n' "${URLS[@]}"
  echo '```'
  echo ""
  echo "## 单独复制（一行一个）"
  echo ""
  i=1
  for u in "${URLS[@]}"; do
    echo "$i. \`$u\`"
    i=$((i+1))
  done
} > "$MD_FILE"

# ── Copy all URLs to clipboard (macOS) ───────────────
if command -v pbcopy &>/dev/null; then
  printf '%s\n' "${URLS[@]}" | pbcopy
  CLIPBOARD_MSG="✅ 10 个 URL 已复制到剪贴板"
else
  CLIPBOARD_MSG="⚠️  pbcopy 不可用（非 macOS？），请手动从 $MD_FILE 复制"
fi

echo "📋 $CLIPBOARD_MSG"
echo ""
echo "📝 Markdown 清单已生成:"
echo "   $MD_FILE"
echo ""

# ── Open GSC home page + markdown ────────────────────
if [[ $OPEN_BROWSER -eq 1 ]]; then
  echo "🚀 正在打开 GSC 首页..."
  open "$GSC_HOME"
  echo ""
  echo "💡 在 GSC 顶部搜索框 ⌘V 粘贴第一个 URL 开始。"
  echo "   剪贴板里是 10 个 URL，每次取一行粘。"
fi
