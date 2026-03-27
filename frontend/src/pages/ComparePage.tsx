import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { fetchSkillDetail } from "../api/client";
import { useI18n } from "../i18n/I18nContext";
import { QualityRadar } from "../components/QualityRadar";
import { ScoreBadge } from "../components/ScoreBadge";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { useCompare } from "../hooks/useCompare";
import type { SkillDetail } from "../types/skill";

export function ComparePage() {
  const { t } = useI18n();
  const [searchParams] = useSearchParams();
  const { clearCompare } = useCompare();
  const [skills, setSkills] = useState<SkillDetail[]>([]);
  const [loading, setLoading] = useState(true);

  const ids = searchParams.get("ids")?.split(",").map(Number).filter(Boolean) || [];

  useEffect(() => {
    if (ids.length < 2) {
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all(ids.map((id) => fetchSkillDetail(id)))
      .then(setSkills)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [searchParams.get("ids")]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <SiteHeader breadcrumb={[{ label: t("compare.title") }]} />
        <div className="flex items-center justify-center py-32">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (skills.length < 2) {
    return (
      <div className="min-h-screen bg-gray-50">
        <SiteHeader breadcrumb={[{ label: t("compare.title") }]} />
        <div className="text-center py-32">
          <p className="text-gray-500">{t("compare.needMore")}</p>
        </div>
        <SiteFooter />
      </div>
    );
  }

  const rows = [
    { key: "score", label: t("compare.score"), render: (s: SkillDetail) => s.score?.toFixed(1) || "-" },
    { key: "stars", label: t("detail.stars"), render: (s: SkillDetail) => s.stars.toLocaleString() },
    { key: "forks", label: t("detail.forks"), render: (s: SkillDetail) => s.forks.toLocaleString() },
    { key: "issues", label: t("detail.issues"), render: (s: SkillDetail) => s.open_issues.toLocaleString() },
    { key: "commits", label: t("detail.commits"), render: (s: SkillDetail) => s.total_commits.toLocaleString() },
    { key: "followers", label: t("detail.followers"), render: (s: SkillDetail) => s.author_followers.toLocaleString() },
    { key: "category", label: t("table.category"), render: (s: SkillDetail) => s.category },
    { key: "language", label: "Language", render: (s: SkillDetail) => s.language || "-" },
    { key: "tokens", label: t("detail.tokens"), render: (s: SkillDetail) => s.estimated_tokens > 0 ? `~${(s.estimated_tokens / 1000).toFixed(0)}k` : "-" },
    { key: "quality", label: t("detail.qualityAnalysis"), render: (s: SkillDetail) => ((s.quality_score || 0)).toFixed(0) },
    { key: "completeness", label: t("detail.completeness"), render: (s: SkillDetail) => ((s.quality_completeness || 0) * 100).toFixed(0) + "%" },
    { key: "clarity", label: t("detail.clarity"), render: (s: SkillDetail) => ((s.quality_clarity || 0) * 100).toFixed(0) + "%" },
    { key: "agent", label: t("detail.agentReadiness"), render: (s: SkillDetail) => ((s.quality_agent_readiness || 0) * 100).toFixed(0) + "%" },
  ];

  // Find best value per row
  function getBestIdx(key: string): number {
    const numKeys = ["score", "stars", "forks", "commits", "followers", "quality", "completeness", "clarity", "agent", "tokens"];
    if (!numKeys.includes(key)) return -1;
    let best = -1;
    let bestVal = -Infinity;
    skills.forEach((s, i) => {
      let val = 0;
      switch (key) {
        case "score": val = s.score || 0; break;
        case "stars": val = s.stars; break;
        case "forks": val = s.forks; break;
        case "commits": val = s.total_commits; break;
        case "followers": val = s.author_followers; break;
        case "quality": val = s.quality_score || 0; break;
        case "completeness": val = s.quality_completeness || 0; break;
        case "clarity": val = s.quality_clarity || 0; break;
        case "agent": val = s.quality_agent_readiness || 0; break;
        case "tokens": val = s.estimated_tokens; break;
      }
      if (val > bestVal) { bestVal = val; best = i; }
    });
    return best;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Helmet>
        <title>{`Compare: ${skills.map((s) => s.repo_name).join(" vs ")} - Agent Skills Hub`}</title>
      </Helmet>

      <SiteHeader breadcrumb={[{ label: t("compare.title") }]} />

      <main className="max-w-5xl mx-auto px-4 py-6">
        {/* Radar Charts */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-4">
            {t("detail.qualityAnalysis")}
          </h2>
          <div className={`grid gap-4 ${skills.length === 2 ? "grid-cols-2" : skills.length === 3 ? "grid-cols-3" : "grid-cols-4"}`}>
            {skills.map((s) => (
              <div key={s.id} className="text-center">
                <div className="flex justify-center mb-2">
                  <QualityRadar
                    completeness={s.quality_completeness}
                    clarity={s.quality_clarity}
                    specificity={s.quality_specificity}
                    examples={s.quality_examples}
                    structure={s.readme_structure_score}
                    agentReadiness={s.quality_agent_readiness}
                    size="sm"
                  />
                </div>
                <div className="flex items-center justify-center gap-2">
                  <ScoreBadge score={s.score} size="sm" />
                  <span className="text-sm font-medium text-gray-900 truncate max-w-32">{s.repo_name}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Comparison Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden mb-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wide w-36">
                  {t("compare.metric")}
                </th>
                {skills.map((s) => (
                  <th key={s.id} className="text-center px-4 py-3">
                    <div className="flex items-center justify-center gap-2">
                      <img src={s.author_avatar_url} alt={s.author_name} className="w-5 h-5 rounded-full" />
                      <a
                        href={s.repo_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-medium text-gray-900 hover:text-blue-600 truncate max-w-28"
                      >
                        {s.repo_name}
                      </a>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const bestIdx = getBestIdx(row.key);
                return (
                  <tr key={row.key} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="px-4 py-2.5 text-xs text-gray-500 font-medium">{row.label}</td>
                    {skills.map((s, i) => (
                      <td
                        key={s.id}
                        className={`text-center px-4 py-2.5 text-sm ${
                          i === bestIdx ? "text-green-600 font-bold" : "text-gray-700"
                        }`}
                      >
                        {row.render(s)}
                        {i === bestIdx && bestIdx >= 0 && (
                          <span className="ml-1 text-green-500 text-[10px]">&#9650;</span>
                        )}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Clear compare */}
        <div className="text-center">
          <button
            onClick={() => { clearCompare(); window.history.back(); }}
            className="text-sm text-gray-400 hover:text-gray-600 transition-colors cursor-pointer"
          >
            {t("compare.clearAndBack")}
          </button>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
