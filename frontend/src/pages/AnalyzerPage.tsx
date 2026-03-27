import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { useI18n } from "../i18n/I18nContext";
import { scanReadme, fetchGitHubRepo, type ScanResult, type FlagDetail } from "../utils/securityScanner";
import { supabase } from "../lib/supabase";

const GRADE_CONFIG: Record<string, { label: string; labelZh: string; color: string; bg: string; border: string; icon: string }> = {
  safe: { label: "Safe", labelZh: "安全", color: "text-green-600 dark:text-green-400", bg: "bg-green-50 dark:bg-green-900/20", border: "border-green-200 dark:border-green-800", icon: "✓" },
  caution: { label: "Caution", labelZh: "注意", color: "text-amber-600 dark:text-amber-400", bg: "bg-amber-50 dark:bg-amber-900/20", border: "border-amber-200 dark:border-amber-800", icon: "⚠" },
  unsafe: { label: "Unsafe", labelZh: "风险", color: "text-red-600 dark:text-red-400", bg: "bg-red-50 dark:bg-red-900/20", border: "border-red-200 dark:border-red-800", icon: "✕" },
  reject: { label: "Reject", labelZh: "拒绝", color: "text-red-700 dark:text-red-300", bg: "bg-red-100 dark:bg-red-900/40", border: "border-red-300 dark:border-red-700", icon: "⛔" },
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: "bg-red-200 dark:bg-red-900/50 text-red-800 dark:text-red-200",
  high: "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300",
  medium: "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300",
  low: "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300",
};

const TRUST_TIER_CONFIG: Record<number, { label: string; labelZh: string; color: string; icon: string }> = {
  1: { label: "Official Org", labelZh: "官方组织", color: "text-green-600 dark:text-green-400", icon: "🏛️" },
  2: { label: "Known Security Team", labelZh: "知名安全团队", color: "text-blue-600 dark:text-blue-400", icon: "🛡️" },
  3: { label: "High-Star + Licensed", labelZh: "高星 + 有许可证", color: "text-indigo-600 dark:text-indigo-400", icon: "⭐" },
  4: { label: "Moderate Trust", labelZh: "中等信任", color: "text-amber-600 dark:text-amber-400", icon: "📋" },
  5: { label: "Unknown Source", labelZh: "未知来源", color: "text-red-600 dark:text-red-400", icon: "❓" },
};

interface FullResult {
  repo: { full_name: string; stars: number; description: string; license: string | null; repo_url: string; category: string | null };
  indexed: boolean;
  scan: ScanResult;
  quality: { score: number; completeness: number; clarity: number; specificity: number; examples: number; agent_readiness: number } | null;
}

type HistoryItem = { url: string; grade: string; time: number };

function loadHistory(): HistoryItem[] {
  try { return JSON.parse(sessionStorage.getItem("analyzer_history") || "[]"); } catch { return []; }
}
function saveHistory(item: HistoryItem) {
  const h = loadHistory().filter(x => x.url !== item.url);
  h.unshift(item);
  sessionStorage.setItem("analyzer_history", JSON.stringify(h.slice(0, 5)));
}

function parseGitHubUrl(url: string): string | null {
  const m = url.trim().match(/(?:https?:\/\/)?github\.com\/([^/]+\/[^/]+?)(?:\.git)?\/?$/);
  return m ? m[1] : null;
}

export function AnalyzerPage() {
  const { lang } = useI18n();
  const [searchParams] = useSearchParams();
  const [repoUrl, setRepoUrl] = useState(searchParams.get("repo") || "");
  const [result, setResult] = useState<FullResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history] = useState<HistoryItem[]>(loadHistory);

  useEffect(() => { window.scrollTo(0, 0); }, []);

  const doScan = useCallback(async (inputUrl: string) => {
    const fullName = parseGitHubUrl(inputUrl);
    if (!fullName) { setError(lang === "zh" ? "请输入有效的 GitHub 仓库 URL" : "Please enter a valid GitHub repo URL"); return; }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // 1. Check if already indexed in Supabase
      let indexed = false;
      let quality = null;
      let category: string | null = null;
      let existingGrade: string | null = null;
      let existingFlags: string[] = [];

      try {
        const sb = supabase;
        if (sb) {
          const { data } = await sb
            .from("skills")
            .select("category,quality_score,quality_completeness,quality_clarity,quality_specificity,quality_examples,quality_agent_readiness,security_grade,security_flags")
            .eq("repo_full_name", fullName)
            .maybeSingle();
          if (data) {
            indexed = true;
            category = data.category;
            quality = {
              score: data.quality_score || 0,
              completeness: data.quality_completeness || 0,
              clarity: data.quality_clarity || 0,
              specificity: data.quality_specificity || 0,
              examples: data.quality_examples || 0,
              agent_readiness: data.quality_agent_readiness || 0,
            };
            existingGrade = data.security_grade;
            try { existingFlags = JSON.parse(data.security_flags || "[]"); } catch { /* ignore */ }
          }
        }
      } catch { /* Supabase not available, continue */ }

      // 2. Fetch from GitHub API
      const gh = await fetchGitHubRepo(fullName);

      // 3. Run browser-side security scan
      const scan = scanReadme(gh.readme, gh.author, gh.stars, gh.license);

      // If we had existing scan from DB and README was empty on GitHub, use DB data
      if (!gh.readme && existingGrade && existingGrade !== "unknown") {
        scan.grade = existingGrade as ScanResult["grade"];
        scan.flags = existingFlags;
      }

      const fullResult: FullResult = {
        repo: {
          full_name: fullName,
          stars: gh.stars,
          description: gh.description,
          license: gh.license,
          repo_url: gh.repoUrl,
          category,
        },
        indexed,
        scan,
        quality,
      };

      setResult(fullResult);
      saveHistory({ url: inputUrl, grade: scan.grade, time: Date.now() });
    } catch (err: any) {
      setError(err.message || "Analysis failed");
    } finally {
      setLoading(false);
    }
  }, [lang]);

  const handleScan = useCallback((e?: React.FormEvent) => {
    e?.preventDefault();
    if (repoUrl.trim()) doScan(repoUrl.trim());
  }, [repoUrl, doScan]);

  // Auto-scan if ?repo= param
  useEffect(() => {
    const repo = searchParams.get("repo");
    if (repo && !result && !loading) {
      setRepoUrl(repo);
      doScan(repo);
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
            {isZh ? "SlowMist 安全框架驱动 · 11 类红旗检测" : "SlowMist Framework · 11 Red-Flag Categories"}
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            {isZh ? "Skill 安全分析器" : "Skill Security Analyzer"}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 max-w-lg mx-auto">
            {isZh
              ? "粘贴 GitHub 仓库 URL，即时分析安全风险。纯浏览器端运行，无需后端。"
              : "Paste a GitHub repo URL for instant security analysis. Runs entirely in your browser."}
          </p>
        </div>

        {/* Search */}
        <form onSubmit={handleScan} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6 shadow-sm">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              <input
                type="text" value={repoUrl} onChange={e => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repo"
                className="w-full pl-10 pr-4 py-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <button type="submit" disabled={loading || !repoUrl.trim()}
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium text-sm hover:bg-indigo-700 transition-colors disabled:opacity-50 flex items-center gap-2 cursor-pointer whitespace-nowrap">
              {loading ? (
                <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />{isZh ? "扫描中..." : "Scanning..."}</>
              ) : (
                <><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>{isZh ? "开始扫描" : "Scan Now"}</>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 mb-6">
            <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
          </div>
        )}

        {result && <ResultsDisplay result={result} isZh={isZh} />}

        {!result && history.length > 0 && (
          <div className="mt-8">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">{isZh ? "最近扫描" : "Recent Scans"}</h3>
            <div className="space-y-2">
              {history.map((h, i) => {
                const gc = GRADE_CONFIG[h.grade] || GRADE_CONFIG.caution;
                return (
                  <button key={i} onClick={() => { setRepoUrl(h.url); }}
                    className="w-full flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-indigo-400 transition-colors text-left cursor-pointer">
                    <span className="text-sm text-gray-700 dark:text-gray-300 truncate">{h.url}</span>
                    <span className={`text-xs font-medium ${gc.color}`}>{gc.icon} {isZh ? gc.labelZh : gc.label}</span>
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

function ResultsDisplay({ result, isZh }: { result: FullResult; isZh: boolean }) {
  const { scan, repo, quality } = result;
  const gc = GRADE_CONFIG[scan.grade] || GRADE_CONFIG.caution;
  const tc = TRUST_TIER_CONFIG[scan.trustTier] || TRUST_TIER_CONFIG[5];

  return (
    <div className="space-y-6">
      {/* Grade Card */}
      <div className={`${gc.bg} border ${gc.border} rounded-xl p-6`}>
        <div className="flex items-start gap-4">
          <div className={`w-16 h-16 rounded-full border-4 ${gc.border} flex items-center justify-center shrink-0`}>
            <span className={`text-2xl font-bold ${gc.color}`}>{gc.icon}</span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-1 flex-wrap">
              <h2 className={`text-xl font-bold ${gc.color}`}>{isZh ? gc.labelZh : gc.label}</h2>
              {result.indexed && (
                <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600">{isZh ? "已收录" : "Indexed"}</span>
              )}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              {scan.flags.length === 0
                ? (isZh ? "未检测到危险模式，该仓库通过安全扫描。" : "No dangerous patterns detected. This repository passed the security scan.")
                : (isZh ? `检测到 ${scan.flags.length} 个安全标记，请查看下方详细报告。` : `${scan.flags.length} security flag(s) detected. See detailed report below.`)}
            </p>
          </div>
        </div>
      </div>

      {/* Trust Tier + Repo Info */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{isZh ? "仓库信息" : "Repository Info"}</h3>
          <a href={repo.repo_url} target="_blank" rel="noopener noreferrer" className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline">
            {isZh ? "查看 GitHub →" : "View on GitHub →"}
          </a>
        </div>

        {/* Trust Tier */}
        <div className="mb-4 p-3 rounded-lg bg-gray-50 dark:bg-gray-800 flex items-center gap-3">
          <span className="text-lg">{tc.icon}</span>
          <div>
            <span className="text-[10px] uppercase tracking-wider text-gray-400 font-medium">{isZh ? "信任层级" : "Trust Tier"}</span>
            <p className={`text-sm font-bold ${tc.color}`}>Tier {scan.trustTier}: {isZh ? tc.labelZh : tc.label}</p>
          </div>
          <div className="ml-auto flex gap-1">
            {[1, 2, 3, 4, 5].map(t => (
              <div key={t} className={`w-2 h-6 rounded-sm ${t <= scan.trustTier
                ? (scan.trustTier <= 2 ? "bg-green-400" : scan.trustTier <= 3 ? "bg-blue-400" : scan.trustTier <= 4 ? "bg-amber-400" : "bg-red-400")
                : "bg-gray-200 dark:bg-gray-700"}`} />
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
          <div><span className="text-gray-500 dark:text-gray-400 text-xs">{isZh ? "仓库" : "Repo"}</span><p className="font-medium text-gray-900 dark:text-white truncate">{repo.full_name}</p></div>
          <div><span className="text-gray-500 dark:text-gray-400 text-xs">Stars</span><p className="font-medium text-gray-900 dark:text-white">⭐ {repo.stars?.toLocaleString()}</p></div>
          <div><span className="text-gray-500 dark:text-gray-400 text-xs">{isZh ? "许可证" : "License"}</span><p className="font-medium text-gray-900 dark:text-white">{repo.license || "N/A"}</p></div>
          <div><span className="text-gray-500 dark:text-gray-400 text-xs">{isZh ? "分类" : "Category"}</span><p className="font-medium text-gray-900 dark:text-white">{repo.category || "N/A"}</p></div>
        </div>
        {repo.description && <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">{repo.description}</p>}
      </div>

      {/* Security Report */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">{isZh ? "安全审查报告" : "Security Audit Report"}</h3>

        {scan.flagDetails.length > 0 ? (
          <div className="space-y-2">
            {scan.flagDetails.map((flag: FlagDetail, i: number) => (
              <div key={i} className="flex items-start gap-2 p-2.5 rounded-lg bg-gray-50 dark:bg-gray-800">
                <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded shrink-0 ${SEVERITY_COLORS[flag.severity] || SEVERITY_COLORS.medium}`}>
                  {flag.severity.toUpperCase()}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-gray-700 dark:text-gray-300">{flag.description}</p>
                  <p className="text-[10px] text-gray-400 font-mono mt-0.5">{flag.name}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 rounded-lg bg-green-50 dark:bg-green-900/20 text-center">
            <span className="text-green-600 dark:text-green-400 text-sm font-medium">
              ✓ {isZh ? "未检测到危险模式 (11 类红旗均通过)" : "No dangerous patterns detected (all 11 red-flag categories passed)"}
            </span>
          </div>
        )}
      </div>

      {/* Quality */}
      {quality && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">{isZh ? "质量评分" : "Quality Score"}</h3>
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
                  <div className="text-lg font-bold text-gray-900 dark:text-white">{key === "score" ? val.toFixed(1) : `${pct}%`}</div>
                  <div className="text-[10px] text-gray-500 dark:text-gray-400">{label}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {result.indexed && (
        <div className="text-center">
          <Link to={`/skill/${repo.full_name}/`} className="inline-flex items-center gap-1.5 text-sm text-indigo-600 dark:text-indigo-400 hover:underline">
            {isZh ? "查看完整详情页 →" : "View full detail page →"}
          </Link>
        </div>
      )}

      <div className="text-center text-[11px] text-gray-400 dark:text-gray-500">
        {isZh ? "安全框架灵感来源: SlowMist Agent Security Framework" : "Security framework inspired by SlowMist Agent Security Framework"}
        {" · "}
        <a href="https://github.com/slowmist/slowmist-agent-security" target="_blank" rel="noopener noreferrer" className="hover:text-indigo-500">GitHub →</a>
      </div>
    </div>
  );
}
