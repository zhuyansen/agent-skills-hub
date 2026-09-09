import { useCallback, useMemo, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Link, useSearchParams } from "react-router-dom";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { useI18n } from "../i18n/I18nContext";
import { trackEvent } from "../lib/analytics";
import { sbFetchOrgAudit, type OrgAuditRow } from "../api/supabaseClient";

// Local, self-contained grade styling — mirrors AnalyzerPage's GRADE_CONFIG but
// adds the "unknown" (not-yet-graded) tier that a whole-org view surfaces.
const GRADE_META: Record<
  string,
  { label: string; labelZh: string; color: string; dot: string }
> = {
  safe: {
    label: "Safe",
    labelZh: "安全",
    color: "text-green-600 dark:text-green-400",
    dot: "bg-green-500",
  },
  caution: {
    label: "Caution",
    labelZh: "注意",
    color: "text-amber-600 dark:text-amber-400",
    dot: "bg-amber-500",
  },
  unsafe: {
    label: "Unsafe",
    labelZh: "风险",
    color: "text-red-600 dark:text-red-400",
    dot: "bg-red-500",
  },
  reject: {
    label: "Reject",
    labelZh: "拒绝",
    color: "text-red-700 dark:text-red-300",
    dot: "bg-red-700",
  },
  unknown: {
    label: "Not graded",
    labelZh: "未评级",
    color: "text-gray-500 dark:text-gray-400",
    dot: "bg-gray-400",
  },
};

const GRADE_ORDER = ["unsafe", "reject", "caution", "safe", "unknown"];
const FREE_ROWS = 8;
const CLUB_URL = "https://jasonzhu.ai/zh/club";

function gradeKey(g: string | null): string {
  const k = (g || "unknown").toLowerCase();
  return k in GRADE_META ? k : "unknown";
}

export function OrgAuditPage() {
  const { lang } = useI18n();
  const zh = lang === "zh";
  const [params, setParams] = useSearchParams();
  const [owner, setOwner] = useState(params.get("owner") ?? "");
  const [rows, setRows] = useState<OrgAuditRow[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ran, setRan] = useState("");

  // Pro is honor-system here (the data is public per-skill): a key in
  // localStorage unlocks the full table + CSV export; everyone sees the summary
  // and the top rows free.
  const hasPro = (() => {
    try {
      return !!localStorage.getItem("pro_key");
    } catch {
      return false;
    }
  })();

  const run = useCallback(
    async (raw: string) => {
      const clean = raw.trim().replace(/^@/, "").replace(/\/.*$/, "");
      if (!clean || loading) return;
      setLoading(true);
      setError(null);
      setParams({ owner: clean }, { replace: true });
      try {
        const data = await sbFetchOrgAudit(clean);
        setRows(data);
        setRan(clean);
        trackEvent("org_audit_run", { owner: clean, total: data.length });
      } catch {
        setError(
          zh
            ? "查询失败,请稍后重试。"
            : "Lookup failed — please try again in a moment.",
        );
        setRows(null);
      } finally {
        setLoading(false);
      }
    },
    [loading, setParams, zh],
  );

  const summary = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const r of rows ?? []) {
      const k = gradeKey(r.security_grade);
      counts[k] = (counts[k] || 0) + 1;
    }
    return counts;
  }, [rows]);

  const gradedCount = useMemo(
    () =>
      (rows ?? []).filter((r) => gradeKey(r.security_grade) !== "unknown")
        .length,
    [rows],
  );

  const visibleRows = useMemo(() => {
    if (!rows) return [];
    return hasPro ? rows : rows.slice(0, FREE_ROWS);
  }, [rows, hasPro]);

  const hiddenCount = (rows?.length ?? 0) - visibleRows.length;

  const exportCsv = useCallback(() => {
    if (!rows || !hasPro) return;
    const header = "repo,grade,quality_score,stars,category";
    const body = rows
      .map((r) =>
        [
          r.repo_full_name,
          r.security_grade || "unknown",
          r.quality_score ?? "",
          r.stars,
          r.category || "",
        ].join(","),
      )
      .join("\n");
    const blob = new Blob([`${header}\n${body}`], {
      type: "text/csv;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${ran}-security-audit.csv`;
    a.click();
    URL.revokeObjectURL(url);
    trackEvent("org_audit_export", { owner: ran, total: rows.length });
  }, [rows, hasPro, ran]);

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-950">
      <Helmet>
        <title>
          {zh
            ? "批量安全审计 · 审计整个 GitHub 组织 | Agent Skills Hub"
            : "Batch Security Audit · Vet a whole GitHub org | Agent Skills Hub"}
        </title>
        <meta
          name="description"
          content={
            zh
              ? "输入一个 GitHub 组织或用户,一次查看它所有已收录 skill 与 MCP server 的安全评级。"
              : "Enter a GitHub org or user to see security grades for every one of its indexed skills and MCP servers at once."
          }
        />
        <meta name="robots" content="noindex" />
      </Helmet>

      <SiteHeader />

      <main className="flex-1 w-full max-w-4xl mx-auto px-4 py-10">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight mb-2">
          {zh ? "批量审计整个组织" : "Audit an entire organization"}
        </h1>
        <p className="text-sm text-[var(--text-2)] mb-6 max-w-2xl">
          {zh
            ? "输入一个 GitHub 组织或用户名,一次看它所有已收录 skill 的安全评级 —— 不用一个个查。"
            : "Enter a GitHub org or username to see the security grade of every skill it ships — vet your whole stack in one shot instead of one repo at a time."}
        </p>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            run(owner);
          }}
          className="flex flex-col sm:flex-row gap-2 mb-8"
        >
          <input
            type="text"
            value={owner}
            onChange={(e) => setOwner(e.target.value)}
            placeholder={zh ? "如 anthropics" : "e.g. anthropics"}
            aria-label={zh ? "GitHub 组织或用户" : "GitHub org or user"}
            className="flex-1 px-4 py-3 rounded-xl border border-gray-300 dark:border-white/15 bg-white dark:bg-white/5 text-gray-900 dark:text-white placeholder-gray-400 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
          />
          <button
            type="submit"
            disabled={loading || !owner.trim()}
            className="shrink-0 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors cursor-pointer"
          >
            {loading
              ? zh
                ? "审计中…"
                : "Auditing…"
              : zh
                ? "审计"
                : "Audit"}
          </button>
        </form>

        {error && (
          <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300 mb-6">
            {error}
          </div>
        )}

        {rows && !loading && rows.length === 0 && (
          <div className="p-6 rounded-xl border border-gray-200 dark:border-[var(--border)] bg-white dark:bg-[var(--bg-card)] text-sm text-[var(--text-2)]">
            {zh
              ? `我们的目录里还没有 “${ran}” 的已收录 skill。它的仓库可能尚未被索引 —— `
              : `No indexed skills found for “${ran}” yet. Its repos may not be in the catalog — `}
            <Link
              to="/submit/"
              className="text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              {zh ? "提交收录" : "submit it"}
            </Link>
            {zh ? "。" : "."}
          </div>
        )}

        {rows && rows.length > 0 && (
          <>
            {/* Summary */}
            <div className="mb-6">
              <div className="flex items-baseline justify-between mb-3">
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                  {zh ? `${ran} · ${rows.length} 个已收录 skill` : `${ran} · ${rows.length} indexed skills`}
                </h2>
                <span className="text-xs text-[var(--text-3)]">
                  {zh
                    ? `${gradedCount} 个已评级`
                    : `${gradedCount} graded`}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {GRADE_ORDER.filter((k) => summary[k]).map((k) => (
                  <span
                    key={k}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-white dark:bg-[var(--bg-card)] border border-gray-200 dark:border-[var(--border)] ${GRADE_META[k].color}`}
                  >
                    <span className={`w-2 h-2 rounded-full ${GRADE_META[k].dot}`} />
                    {(zh ? GRADE_META[k].labelZh : GRADE_META[k].label)} · {summary[k]}
                  </span>
                ))}
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-[var(--border)] bg-white dark:bg-[var(--bg-card)]">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-[var(--border)] text-left text-xs uppercase tracking-wider text-[var(--text-3)]">
                    <th className="px-4 py-3 font-medium">{zh ? "仓库" : "Repo"}</th>
                    <th className="px-4 py-3 font-medium">{zh ? "评级" : "Grade"}</th>
                    <th className="px-4 py-3 font-medium text-right">{zh ? "质量" : "Quality"}</th>
                    <th className="px-4 py-3 font-medium text-right">Stars</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleRows.map((r) => {
                    const k = gradeKey(r.security_grade);
                    return (
                      <tr
                        key={r.repo_full_name}
                        className="border-b border-gray-100 dark:border-white/5 last:border-0 hover:bg-gray-50 dark:hover:bg-white/5"
                      >
                        <td className="px-4 py-3">
                          <Link
                            to={`/skill/${r.repo_full_name}/`}
                            className="font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
                          >
                            {r.repo_name}
                          </Link>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center gap-1.5 font-semibold ${GRADE_META[k].color}`}>
                            <span className={`w-2 h-2 rounded-full ${GRADE_META[k].dot}`} />
                            {zh ? GRADE_META[k].labelZh : GRADE_META[k].label}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums text-[var(--text-2)]">
                          {r.quality_score != null ? Math.round(r.quality_score) : "—"}
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums text-[var(--text-2)]">
                          {r.stars.toLocaleString()}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {/* Pro gate for the remaining rows */}
              {hiddenCount > 0 && (
                <div className="p-5 border-t border-gray-200 dark:border-[var(--border)] bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-950/40 dark:to-purple-950/20 text-center">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                    {zh
                      ? `还有 ${hiddenCount} 个 skill —— 用 Pro 看全表并导出 CSV`
                      : `${hiddenCount} more skills — see the full table and export CSV with Pro`}
                  </p>
                  <p className="text-xs text-[var(--text-3)] mb-3">
                    {zh
                      ? "每个评级在它自己的 skill 页都免费可见;Pro 给你的是「一次看整个组织 + 导出」的便利。"
                      : "Every grade is free on its own skill page — Pro gives you the whole org at once, plus export."}
                  </p>
                  <Link
                    to="/pro/"
                    onClick={() =>
                      trackEvent("org_audit_pro_click", { owner: ran, hidden: hiddenCount })
                    }
                    className="inline-flex items-center px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-colors"
                  >
                    {zh ? "解锁全表 —— 免费试 3 次 →" : "Unlock full table — 3 free tries →"}
                  </Link>
                </div>
              )}
            </div>

            {/* Pro-only export */}
            {hasPro && (
              <div className="mt-4 flex items-center gap-3">
                <button
                  onClick={exportCsv}
                  className="inline-flex items-center px-4 py-2 rounded-lg border border-gray-300 dark:border-white/15 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors cursor-pointer"
                >
                  {zh ? "导出 CSV" : "Export CSV"}
                </button>
                <span className="text-xs text-[var(--text-3)]">
                  {zh ? "Pro 已激活" : "Pro active"}
                </span>
              </div>
            )}

            <p className="mt-6 text-xs text-[var(--text-3)]">
              {zh
                ? "评级来自装前静态扫描(SlowMist 分类法,11 类红旗),不是人工深审。数据每 8 小时刷新。"
                : "Grades come from a pre-install static scan (SlowMist taxonomy, 11 red-flag categories), not a manual deep audit. Data refreshes every 8h."}
              {" "}
              <a href={CLUB_URL} className="text-indigo-600 dark:text-indigo-400 hover:underline" target="_blank" rel="noopener noreferrer">
                {zh ? "关于 Pro" : "About Pro"}
              </a>
            </p>
          </>
        )}
      </main>

      <SiteFooter />
    </div>
  );
}
