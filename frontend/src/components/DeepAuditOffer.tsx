import { Link } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";
import { trackEvent } from "../lib/analytics";

/**
 * The paid exit after a free rule-based scan — a Pro upsell, grade-aware.
 *
 * The $49 one-time concierge audit was retired 2026-07-13 (0 conversions in 28d
 * + manual fulfilment didn't scale + $49 sat in the price/audience no-man's-land
 * between individuals and enterprise). Monetization now flows into Pro, which
 * you're already pushing: full-README deep search, 200/page, export, API — the
 * self-serve deep layer for actually vetting a repo. The CTA points at /pro/,
 * where the 3-use free trial lives, chaining scan → trial → subscription.
 *
 * Copy is grade-aware (fear on flags, sign-off/evidence on green) but never
 * FUD — the Trust Layer brand can't cry wolf.
 */
const RISKY_GRADES = new Set(["caution", "unsafe", "reject"]);

export function DeepAuditOffer({
  repo,
  grade,
  flagCount = 0,
}: {
  repo?: string | null;
  grade?: string | null;
  flagCount?: number;
}) {
  const { lang } = useI18n();
  const zh = lang === "zh";
  const g = (grade || "unknown").toLowerCase();
  const risky = RISKY_GRADES.has(g);

  const headline = risky
    ? zh
      ? `检测到 ${flagCount} 个安全标记 —— 上生产前该再确认`
      : `${flagCount} security flag${flagCount === 1 ? "" : "s"} found — confirm before you ship`
    : zh
      ? "绿灯 ✓ 上生产前想要更硬的证据?"
      : "Green light ✓ Want harder evidence before you ship?";

  const pitch = risky
    ? zh
      ? "Pro 深度检索能在 13 万仓库正文里查同类问题是怎么被修的,导出证据清单、脚本化复核 —— 把「看着可疑」变成「说得清为什么」。"
      : "Pro deep search cross-checks how similar issues got fixed across 130k repos' README text, exports an evidence list, and scripts the review — turning 'looks risky' into 'here's exactly why'."
    : zh
      ? "Pro:README 全文深度检索 · 200 条/页 · CSV/JSON 导出 · API —— 给合规签核和生产决策留一份可复现的证据。"
      : "Pro: full-README deep search · 200/page · CSV/JSON export · API — a reproducible evidence trail for sign-off and production decisions.";

  return (
    <section className="mt-6 rounded-xl border border-indigo-200 dark:border-indigo-500/30 bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-indigo-950/40 dark:via-transparent dark:to-purple-950/30 p-5 sm:p-6">
      <h3 className="text-base font-bold text-gray-900 dark:text-white mb-1.5">
        {headline}
      </h3>
      <p className="text-sm text-[var(--text-2)] leading-relaxed mb-4">
        {pitch}
      </p>
      <div className="flex flex-wrap items-center gap-3">
        <Link
          to="/pro/"
          onClick={() =>
            trackEvent("audit_pro_upsell_click", {
              grade: g,
              repo: repo || undefined,
            })
          }
          className="inline-flex items-center px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-colors"
        >
          {zh
            ? "用 Pro 深挖 —— 免费试 3 次 →"
            : "Vet deeper with Pro — 3 free tries →"}
        </Link>
        <span className="text-xs text-[var(--text-3)]">
          {zh ? "基础扫描永远免费" : "Basic scan stays free"}
        </span>
      </div>
    </section>
  );
}
