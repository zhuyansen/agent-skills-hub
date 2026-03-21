import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { useI18n } from "../i18n/I18nContext";
import { analyzeRepo } from "../api/client";
import type { AnalyzerResult, LLMFinding } from "../types/analyzer";

const GRADE_CONFIG: Record<string, { label: string; labelZh: string; color: string; bg: string; border: string; icon: string }> = {
  safe: {
    label: "Safe", labelZh: "安全",
    color: "text-green-600 dark:text-green-400",
    bg: "bg-green-50 dark:bg-green-900/20",
    border: "border-green-200 dark:border-green-800",
    icon: "✓",
  },
  caution: {
    label: "Caution", labelZh: "注意",
    color: "text-amber-600 dark:text-amber-400",
    bg: "bg-amber-50 dark:bg-amber-900/20",
    border: "border-amber-200 dark:border-amber-800",
    icon: "⚠",
  },
  unsafe: {
    label: "Unsafe", labelZh: "风险",
    color: "text-red-600 dark:text-red-400",
    bg: "bg-red-50 dark:bg-red-900/20",
    border: "border-red-200 dark:border-red-800",
    icon: "✕",
  },
};

const SEVERITY_COLORS: Record<string, string> = {
  high: "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300",
  medium: "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300",
  low: "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300",
};

type HistoryItem = { url: string; grade: string; time: number };

function loadHistory(): HistoryItem[] {
  try {
    return JSON.parse(sessionStorage.getItem("analyzer_history") || "[]");
  } catch { return []; }
}

function saveHistory(item: HistoryItem) {
  const history = loadHistory().filter(h => h.url !== item.url);
  history.unshift(item);
  sessionStorage.setItem("analyzer_history", JSON.stringify(history.slice(0, 5)));
}

export function AnalyzerPage() {
  const { lang } = useI18n();
  const [searchParams] = useSearchParams();
  const [repoUrl, setRepoUrl] = useState(searchParams.get("repo") || "");
  const [result, setResult] = useState<AnalyzerResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history] = useState<HistoryItem[]>(loadHistory);

  useEffect(() => { window.scrollTo(0, 0); }, []);

  const handleScan = useCallback(async (e?: React.FormEvent) => {
    e?.preventDefault();
    const url = repoUrl.trim();
    if (!url) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await analyzeRepo(url);
      setResult(data);
      saveHistory({
        url,
        grade: data.security.final_grade,
        time: Date.now(),
      });
    } catch (err: any) {
      setError(err.message || "Analysis failed");
    } finally {
      setLoading(false);
    }
  }, [repoUrl]);

  // Auto-scan if repo param provided
  useEffect(() => {
    const repo = searchParams.get("repo");
    if (repo && !result && !loading) {
      setRepoUrl(repo);
      // Small delay to let state update
      setTimeout(() => {
        analyzeRepo(repo).then(data => {
          setResult(data);
          saveHistory({ url: repo, grade: data.security.final_grade, time: Date.now() });
        }).catch(err => setError(err.message));
      }, 100);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const isZh = lang === "zh";

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Helmet>
        <title>{isZh ? "安全分析器" : "Security Analyzer"} — Agent Skills Hub</title>
        <meta name="description" content={isZh ? "分析任何 GitHub 仓库的安全风险" : "Analyze security risks of any GitHub repository"} />
      </Helmet>

      <SiteHeader breadcrumb={[{ label: isZh ? "安全分析器" : "Security Analyzer" }]} />

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 text-xs font-medium mb-4">
            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 1a1 1 0 011 1v.586l5.707 2.853A1 1 0 0117 6.414V10a7 7 0 01-7 7 7 7 0 01-7-7V6.414a1 1 0 01.293-.975L9 2.586V2a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            {isZh ? "AI 驱动安全扫描" : "AI-Powered Security Scanning"}
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            {isZh ? "Skill 安全分析器" : "Skill Security Analyzer"}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 max-w-lg mx-auto">
            {isZh
              ? "粘贴任何 GitHub 仓库 URL，即时分析其安全风险。结合规则引擎 + Claude AI 深度分析。"
              : "Paste any GitHub repository URL for instant security analysis. Combines rule engine + Claude AI deep analysis."}
          </p>
        </div>

        {/* Search Form */}
        <form onSubmit={handleScan} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6 shadow-sm">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              <input
                type="text"
                value={repoUrl}
                onChange={e => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repo"
                className="w-full pl-10 pr-4 py-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !repoUrl.trim()}
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium text-sm hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 cursor-pointer whitespace-nowrap"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  {isZh ? "扫描中..." : "Scanning..."}
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  {isZh ? "开始扫描" : "Scan Now"}
                </>
              )}
            </button>
          </div>
        </form>

        {/* Error */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 mb-6">
            <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Results */}
        {result && <AnalyzerResults result={result} isZh={isZh} />}

        {/* Recent History */}
        {!result && history.length > 0 && (
          <div className="mt-8">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
              {isZh ? "最近扫描" : "Recent Scans"}
            </h3>
            <div className="space-y-2">
              {history.map((h, i) => {
                const gc = GRADE_CONFIG[h.grade] || GRADE_CONFIG.caution;
                return (
                  <button
                    key={i}
                    onClick={() => { setRepoUrl(h.url); }}
                    className="w-full flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-indigo-400 transition-colors text-left cursor-pointer"
                  >
                    <span className="text-sm text-gray-700 dark:text-gray-300 truncate">{h.url}</span>
                    <span className={`text-xs font-medium ${gc.color}`}>
                      {gc.icon} {isZh ? gc.labelZh : gc.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </main>

      <SiteFooter />
    </div>
  );
}

function AnalyzerResults({ result, isZh }: { result: AnalyzerResult; isZh: boolean }) {
  const { security, repo, quality } = result;
  const gc = GRADE_CONFIG[security.final_grade] || GRADE_CONFIG.caution;

  return (
    <div className="space-y-6">
      {/* Main Grade Card */}
      <div className={`${gc.bg} border ${gc.border} rounded-xl p-6`}>
        <div className="flex items-start gap-4">
          {/* Grade Circle */}
          <div className={`w-16 h-16 rounded-full border-4 ${gc.border} flex items-center justify-center shrink-0`}>
            <span className={`text-2xl font-bold ${gc.color}`}>{gc.icon}</span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-1">
              <h2 className={`text-xl font-bold ${gc.color}`}>
                {isZh ? gc.labelZh : gc.label}
              </h2>
              {security.llm_analysis?.confidence != null && (
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {isZh ? "置信度" : "Confidence"}: {Math.round(security.llm_analysis.confidence * 100)}%
                </span>
              )}
              {result.indexed && (
                <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400">
                  {isZh ? "已收录" : "Indexed"}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
              {security.llm_analysis?.risk_summary || (isZh ? "规则扫描完成" : "Rule-based scan completed")}
            </p>
            {security.llm_analysis?.recommendation && (
              <p className="text-xs text-gray-500 dark:text-gray-400 italic">
                {security.llm_analysis.recommendation}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Repo Info */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            {isZh ? "仓库信息" : "Repository Info"}
          </h3>
          <a
            href={repo.repo_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            {isZh ? "查看 GitHub →" : "View on GitHub →"}
          </a>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
          <div>
            <span className="text-gray-500 dark:text-gray-400 text-xs">{isZh ? "仓库" : "Repo"}</span>
            <p className="font-medium text-gray-900 dark:text-white truncate">{repo.full_name}</p>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400 text-xs">Stars</span>
            <p className="font-medium text-gray-900 dark:text-white">⭐ {repo.stars?.toLocaleString()}</p>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400 text-xs">{isZh ? "许可证" : "License"}</span>
            <p className="font-medium text-gray-900 dark:text-white">{repo.license || "N/A"}</p>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400 text-xs">{isZh ? "分类" : "Category"}</span>
            <p className="font-medium text-gray-900 dark:text-white">{repo.category || "N/A"}</p>
          </div>
        </div>
        {repo.description && (
          <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">{repo.description}</p>
        )}
      </div>

      {/* Analysis Details */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">
          {isZh ? "扫描详情" : "Scan Details"}
        </h3>

        {/* Rule vs LLM comparison */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
            <span className="text-[10px] uppercase tracking-wider text-gray-400 font-medium">{isZh ? "规则引擎" : "Rule Engine"}</span>
            <p className={`text-sm font-bold mt-1 ${(GRADE_CONFIG[security.rule_grade] || GRADE_CONFIG.caution).color}`}>
              {(GRADE_CONFIG[security.rule_grade] || GRADE_CONFIG.caution).icon} {isZh ? (GRADE_CONFIG[security.rule_grade] || GRADE_CONFIG.caution).labelZh : (GRADE_CONFIG[security.rule_grade] || GRADE_CONFIG.caution).label}
            </p>
          </div>
          <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
            <span className="text-[10px] uppercase tracking-wider text-gray-400 font-medium">Claude AI</span>
            {security.llm_grade ? (
              <p className={`text-sm font-bold mt-1 ${(GRADE_CONFIG[security.llm_grade] || GRADE_CONFIG.caution).color}`}>
                {(GRADE_CONFIG[security.llm_grade] || GRADE_CONFIG.caution).icon} {isZh ? (GRADE_CONFIG[security.llm_grade] || GRADE_CONFIG.caution).labelZh : (GRADE_CONFIG[security.llm_grade] || GRADE_CONFIG.caution).label}
              </p>
            ) : (
              <p className="text-sm text-gray-400 mt-1">{isZh ? "未分析" : "Not analyzed"}</p>
            )}
          </div>
        </div>

        {/* Flags */}
        {security.flags.length > 0 && (
          <div className="mb-4">
            <span className="text-xs text-gray-500 dark:text-gray-400 mb-2 block">{isZh ? "检测到的模式" : "Detected Patterns"}</span>
            <div className="flex flex-wrap gap-1.5">
              {security.flags.map((flag, i) => (
                <span key={i} className="px-2 py-0.5 text-xs rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 font-mono">
                  {flag}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* LLM Findings */}
        {security.llm_analysis?.findings && security.llm_analysis.findings.length > 0 && (
          <div>
            <span className="text-xs text-gray-500 dark:text-gray-400 mb-2 block">{isZh ? "AI 发现" : "AI Findings"}</span>
            <div className="space-y-2">
              {security.llm_analysis.findings.map((finding: LLMFinding, i: number) => (
                <div key={i} className="flex items-start gap-2 p-2 rounded-lg bg-gray-50 dark:bg-gray-800">
                  <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded ${SEVERITY_COLORS[finding.severity] || SEVERITY_COLORS.low}`}>
                    {finding.severity.toUpperCase()}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-700 dark:text-gray-300">{finding.description}</p>
                    {finding.mitigation && (
                      <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5 italic">{finding.mitigation}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Quality (if indexed) */}
      {quality && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">
            {isZh ? "质量评分" : "Quality Score"}
          </h3>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
            {[
              { key: "score", label: isZh ? "综合" : "Overall" },
              { key: "completeness", label: isZh ? "完整度" : "Completeness" },
              { key: "clarity", label: isZh ? "清晰度" : "Clarity" },
              { key: "specificity", label: isZh ? "具体性" : "Specificity" },
              { key: "examples", label: isZh ? "示例" : "Examples" },
              { key: "agent_readiness", label: isZh ? "Agent 就绪" : "Agent Ready" },
            ].map(({ key, label }) => {
              const val = (quality as any)[key] ?? 0;
              const pct = key === "score" ? val : Math.round(val * 100);
              return (
                <div key={key} className="text-center">
                  <div className="text-lg font-bold text-gray-900 dark:text-white">
                    {key === "score" ? val.toFixed(1) : `${pct}%`}
                  </div>
                  <div className="text-[10px] text-gray-500 dark:text-gray-400">{label}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Link to detail if indexed */}
      {result.indexed && (
        <div className="text-center">
          <Link
            to={`/skill/${repo.full_name}`}
            className="inline-flex items-center gap-1.5 text-sm text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            {isZh ? "查看完整详情页 →" : "View full detail page →"}
          </Link>
        </div>
      )}
    </div>
  );
}
