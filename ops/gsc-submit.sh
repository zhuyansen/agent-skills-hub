#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# GSC Request-Indexing 辅助工具
#
# 用法 1 · 打开所有 10 个 GSC 检查页面（批量标签）：
#   ./ops/gsc-submit.sh --open \
#     owner1/repo1 owner2/repo2 ... owner10/repo10
#
# 用法 2 · 只生成 markdown 文件 + HTML 批量打开器：
#   ./ops/gsc-submit.sh \
#     owner1/repo1 owner2/repo2 ... owner10/repo10
#
# 用法 3 · 从 IndexNow 的 --urls 参数格式读取：
#   ./ops/gsc-submit.sh --from-urls \
#     "https://agentskillshub.top/skill/a/b/,https://..."
#
# 产出：
#   ops/daily-data/YYYY-MM-DD/gsc-today.md  · 可复制的 10 个链接
#   ops/daily-data/YYYY-MM-DD/gsc-today.html · 点一下批量开 10 个标签
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TODAY=$(date +%Y-%m-%d)
OUT_DIR="$PROJECT_ROOT/ops/daily-data/$TODAY"
mkdir -p "$OUT_DIR"

SITE="agentskillshub.top"
RESOURCE="sc-domain%3A${SITE}"
GSC_BASE="https://search.google.com/search-console/inspect?resource_id=${RESOURCE}&id="

OPEN_BROWSER=0
FROM_URLS=""
REPOS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --open) OPEN_BROWSER=1; shift ;;
    --from-urls) FROM_URLS="$2"; shift 2 ;;
    -*) echo "unknown flag: $1" >&2; exit 1 ;;
    *) REPOS+=("$1"); shift ;;
  esac
done

# If --from-urls was passed, extract owner/repo from each URL
if [[ -n "$FROM_URLS" ]]; then
  IFS=',' read -ra URL_ARR <<< "$FROM_URLS"
  for url in "${URL_ARR[@]}"; do
    # Strip https://SITE/skill/ prefix and trailing slash
    path="${url#https://${SITE}/skill/}"
    path="${path%/}"
    REPOS+=("$path")
  done
fi

if [[ ${#REPOS[@]} -eq 0 ]]; then
  echo "ERR: 需要传入 owner/repo 或 --from-urls" >&2
  exit 1
fi

# URL-encode helper (macOS-compatible)
urlencode() {
  local s="$1"
  python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$s"
}

MD_FILE="$OUT_DIR/gsc-today.md"
HTML_FILE="$OUT_DIR/gsc-today.html"

# ── Generate Markdown ────────────────────────────────
{
  echo "# GSC 请求编入索引 · $TODAY"
  echo ""
  echo "点开每个链接 → 等 30s 自动检测 → 右上角点 **"请求编入索引"**"
  echo ""
  echo "或者打开 \`gsc-today.html\` 一键批量开 10 个标签。"
  echo ""
  echo "| # | Skill | GSC 链接 |"
  echo "|--:|:-----|:----|"
  i=1
  for repo in "${REPOS[@]}"; do
    full_url="https://${SITE}/skill/${repo}/"
    encoded=$(urlencode "$full_url")
    gsc_url="${GSC_BASE}${encoded}"
    echo "| $i | \`$repo\` | [inspect]($gsc_url) |"
    i=$((i+1))
  done
} > "$MD_FILE"

# ── Generate HTML tab-opener ─────────────────────────
cat > "$HTML_FILE" << HEADER
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>GSC · $TODAY · 批量打开 10 个标签</title>
  <style>
    body { font-family: -apple-system, system-ui, sans-serif; max-width: 720px;
           margin: 40px auto; padding: 0 20px; color: #1e293b; }
    h1 { font-size: 22px; }
    .hero { background: #0a0e1a; color: #fff; padding: 24px; border-radius: 12px;
            text-align: center; margin-bottom: 24px; }
    button { background: #4f46e5; color: #fff; border: 0; padding: 14px 28px;
             border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }
    button:hover { background: #4338ca; }
    ol { padding-left: 20px; }
    li { margin: 8px 0; }
    a { color: #4f46e5; text-decoration: none; word-break: break-all; }
    a:hover { text-decoration: underline; }
    .note { background: #fef3c7; padding: 12px; border-radius: 8px; font-size: 13px;
            color: #92400e; margin-top: 16px; }
  </style>
</head>
<body>
  <div class="hero">
    <h1 style="margin: 0 0 12px 0; color: #fff;">GSC 批量请求编入索引 · $TODAY</h1>
    <p style="margin: 0 0 20px 0; color: #94a3b8;">点下面按钮，10 个标签一次打开</p>
    <button onclick="openAll()">🚀 Open All 10 Tabs</button>
  </div>

  <div class="note">
    ⚠️ 浏览器会弹出"此网站想要打开多个标签"——点允许。之后逐个标签等检测完成 → 点"请求编入索引"。
  </div>

  <h2>或手动点击：</h2>
  <ol>
HEADER

for repo in "${REPOS[@]}"; do
  full_url="https://${SITE}/skill/${repo}/"
  encoded=$(urlencode "$full_url")
  gsc_url="${GSC_BASE}${encoded}"
  echo "    <li><a href=\"$gsc_url\" target=\"_blank\">$repo</a></li>" >> "$HTML_FILE"
done

cat >> "$HTML_FILE" << FOOTER
  </ol>

  <script>
    const urls = [
FOOTER

for repo in "${REPOS[@]}"; do
  full_url="https://${SITE}/skill/${repo}/"
  encoded=$(urlencode "$full_url")
  gsc_url="${GSC_BASE}${encoded}"
  echo "      '$gsc_url'," >> "$HTML_FILE"
done

cat >> "$HTML_FILE" << 'FINAL'
    ];
    function openAll() {
      urls.forEach((url, i) => {
        // Stagger 50ms to avoid popup blocker
        setTimeout(() => window.open(url, '_blank'), i * 50);
      });
    }
  </script>
</body>
</html>
FINAL

echo "✅ 生成:"
echo "   $MD_FILE"
echo "   $HTML_FILE"
echo ""

# ── Auto-open HTML file if --open flag ───────────────
if [[ $OPEN_BROWSER -eq 1 ]]; then
  echo "🚀 正在打开批量开 tab 的 HTML 文件..."
  open "$HTML_FILE"
  echo "   点页面上 \"Open All 10 Tabs\" 按钮即可。"
fi
