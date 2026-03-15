import { useEffect, useState } from "react";
import { fetchSkillDetail } from "../api/client";
import { useI18n } from "../i18n/I18nContext";
import type { Skill, SkillDetail } from "../types/skill";
import { QualityRadar } from "./QualityRadar";
import { ScoreBadge } from "./ScoreBadge";
import { ProjectTypeBadge } from "./ProjectTypeBadge";
import { PlatformBadges } from "./PlatformBadges";
import { SizeBadge } from "./SizeBadge";

interface Props {
  skill: Skill;
  onClose: () => void;
  onNavigateSkill?: (skillId: number) => void;
}

export function SkillDetailPanel({ skill, onClose, onNavigateSkill }: Props) {
  const { t } = useI18n();
  const [detail, setDetail] = useState<SkillDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchSkillDetail(skill.id)
      .then(setDetail)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [skill.id]);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const data = detail ?? skill;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 dark:bg-black/50 z-40"
        onClick={onClose}
      />

      {/* Panel — full-screen on mobile, side panel on md+ */}
      <div className="fixed inset-0 md:inset-auto md:top-0 md:right-0 md:h-full md:w-full md:max-w-md bg-white dark:bg-gray-900 shadow-2xl z-50 animate-slide-in overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-5 py-4 flex items-center gap-3 z-10">
          <ScoreBadge score={data.score} size="sm" />
          <div className="flex-1 min-w-0">
            <h2 className="font-bold text-gray-900 dark:text-gray-100 truncate">{data.repo_name}</h2>
            <div className="flex items-center gap-2 mt-0.5">
              <img src={data.author_avatar_url} alt="" className="w-4 h-4 rounded-full" />
              <span className="text-xs text-gray-500 dark:text-gray-400">{data.author_name}</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="px-5 py-4 space-y-6">
          {/* Description */}
          {data.description && (
            <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{data.description}</p>
          )}

          {/* Metadata badges */}
          <div className="flex flex-wrap gap-2">
            <span className="px-2.5 py-1 text-xs rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-800">
              {data.category}
            </span>
            <ProjectTypeBadge type={data.project_type} />
            {data.language && (
              <span className="px-2.5 py-1 text-xs rounded-full bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-100 dark:border-gray-700">
                {data.language}
              </span>
            )}
            {data.size_category && data.size_category !== "unknown" && (
              <SizeBadge sizeCategory={data.size_category} sizeKb={data.repo_size_kb} />
            )}
          </div>

          {/* Platforms */}
          {data.platforms && data.platforms !== "[]" && (
            <div>
              <h4 className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-2">
                {t("explore.platform")}
              </h4>
              <PlatformBadges platforms={data.platforms} max={8} />
            </div>
          )}

          {/* Stats row */}
          <div className="grid grid-cols-4 gap-3">
            {[
              { label: t("detail.stars"), value: data.stars.toLocaleString(), icon: "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" },
              { label: t("detail.forks"), value: data.forks.toLocaleString(), icon: "M6 3a3 3 0 00-3 3v2.6a3 3 0 001 2.24V18a3 3 0 003 3h10a3 3 0 003-3v-7.16A3 3 0 0021 8.6V6a3 3 0 00-3-3H6z" },
              { label: t("detail.issues"), value: data.open_issues.toLocaleString(), icon: "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" },
              { label: t("detail.tokens"), value: data.estimated_tokens > 0 ? `~${(data.estimated_tokens / 1000).toFixed(0)}k` : "-", icon: "M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" },
            ].map((stat) => (
              <div key={stat.label} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-center">
                <svg className="w-4 h-4 mx-auto text-gray-400 dark:text-gray-500 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={stat.icon} />
                </svg>
                <div className="text-sm font-bold text-gray-900 dark:text-gray-100">{stat.value}</div>
                <div className="text-[10px] text-gray-400 dark:text-gray-500">{stat.label}</div>
              </div>
            ))}
          </div>

          {/* Quality Radar */}
          <div>
            <h4 className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-3">
              {t("detail.qualityAnalysis")}
            </h4>
            <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 flex justify-center">
              <QualityRadar
                completeness={data.quality_completeness}
                clarity={data.quality_clarity}
                specificity={data.quality_specificity}
                examples={data.quality_examples}
                structure={data.readme_structure_score}
                agentReadiness={data.quality_agent_readiness}
                size="md"
              />
            </div>
          </div>

          {/* Quality Score Breakdown */}
          <div>
            <h4 className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-3">
              {t("detail.scoreBreakdown")}
            </h4>
            <div className="space-y-2">
              {[
                { label: t("detail.completeness"), value: data.quality_completeness },
                { label: t("detail.clarity"), value: data.quality_clarity },
                { label: t("detail.specificity"), value: data.quality_specificity },
                { label: t("detail.examples"), value: data.quality_examples },
                { label: t("detail.structure"), value: data.readme_structure_score },
                { label: t("detail.agentReadiness"), value: data.quality_agent_readiness },
              ].map((dim) => (
                <div key={dim.label} className="flex items-center gap-3">
                  <span className="text-xs text-gray-500 dark:text-gray-400 w-28">{dim.label}</span>
                  <div className="flex-1 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full transition-all"
                      style={{ width: `${(dim.value ?? 0) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium text-gray-700 dark:text-gray-300 w-8 text-right">
                    {((dim.value ?? 0) * 100).toFixed(0)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Compatible Skills */}
          {loading ? (
            <div className="text-center py-4">
              <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">{t("detail.loading")}</p>
            </div>
          ) : detail?.compatible_skills && detail.compatible_skills.length > 0 ? (
            <div>
              <h4 className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-3">
                {t("detail.compatibleSkills")}
              </h4>
              <div className="space-y-2">
                {detail.compatible_skills.map((cs) => (
                  <div
                    key={cs.skill_id}
                    onClick={() => onNavigateSkill?.(cs.skill_id)}
                    className={`flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg ${
                      onNavigateSkill ? "cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors" : ""
                    }`}
                  >
                    <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center text-xs font-bold shrink-0">
                      {cs.skill_score.toFixed(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100 block truncate">
                        {cs.skill_name}
                      </span>
                      <span className="text-xs text-gray-400 dark:text-gray-500 block truncate">{cs.reason}</span>
                    </div>
                    <span className="text-xs text-green-600 dark:text-green-400 font-medium whitespace-nowrap">
                      {(cs.compatibility_score * 100).toFixed(0)}% {t("detail.match")}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {/* GitHub Button */}
          <a
            href={data.repo_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 w-full py-3 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-xl hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors font-medium text-sm"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            {t("detail.viewOnGitHub")}
          </a>
        </div>
      </div>
    </>
  );
}
