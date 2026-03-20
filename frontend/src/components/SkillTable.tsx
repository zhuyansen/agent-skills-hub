import { useI18n } from "../i18n/I18nContext";
import type { Skill } from "../types/skill";
import { isNew, timeAgo } from "../utils/time";
import { getTier } from "./ScoreBadge";
import { ScoreBadge } from "./ScoreBadge";
import { SecurityBadge } from "./SecurityBadge";

interface Props {
  skills: Skill[];
  onSelect?: (skill: Skill) => void;
  onShowDetail?: (skill: Skill) => void;
}

export function SkillTable({ skills, onSelect: _onSelect, onShowDetail }: Props) {
  const { t } = useI18n();

  return (
    <div className="overflow-x-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100 dark:border-gray-800 text-left text-gray-500 dark:text-gray-400">
            <th className="px-4 py-3 font-medium">{t("table.score")}</th>
            <th className="px-4 py-3 font-medium">{t("table.name")}</th>
            <th className="px-4 py-3 font-medium hidden md:table-cell">{t("table.category")}</th>
            <th className="px-4 py-3 font-medium hidden lg:table-cell">{t("table.quality")}</th>
            <th className="px-4 py-3 font-medium text-right">{t("table.stars")}</th>
            <th className="px-4 py-3 font-medium text-right hidden sm:table-cell">{t("table.momentum")}</th>
            <th className="px-4 py-3 font-medium text-right hidden md:table-cell">{t("table.updated")}</th>
          </tr>
        </thead>
        <tbody>
          {skills.map((skill) => (
              <tr
                key={skill.id}
                onClick={() => onShowDetail?.(skill)}
                className="border-b border-gray-50 dark:border-gray-800 hover:bg-blue-50/40 dark:hover:bg-blue-900/20 transition-colors cursor-pointer"
              >
                <td className="px-4 py-3">
                  <ScoreBadge score={skill.score} size="sm" showTier />
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    <span
                      onClick={(e) => {
                        e.stopPropagation();
                        window.open(skill.repo_url, "_blank", "noopener");
                      }}
                      className="font-medium text-gray-900 dark:text-gray-100 hover:text-blue-600 hover:underline transition-colors cursor-pointer"
                    >
                      {skill.repo_name}
                    </span>
                    {isNew(skill.first_seen) && (
                      <span className="px-1 py-0.5 text-[9px] font-bold rounded bg-green-50 dark:bg-green-900/30 text-green-600">NEW</span>
                    )}
                    <SecurityBadge grade={skill.security_grade} />
                  </div>
                  <div className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{skill.author_name}</div>
                </td>
                <td className="px-4 py-3 hidden md:table-cell">
                  <span className="px-2 py-0.5 text-xs rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600">
                    {skill.category}
                  </span>
                </td>
                <td className="px-4 py-3 hidden lg:table-cell">
                  <div className="flex items-center gap-1">
                    <div className="w-16 h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          skill.quality_score >= 70 ? "bg-emerald-400" : skill.quality_score >= 40 ? "bg-blue-400" : "bg-gray-300"
                        }`}
                        style={{ width: `${Math.min(skill.quality_score, 100)}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400 tabular-nums w-6">{Math.round(skill.quality_score)}</span>
                    <span className="text-[9px] font-bold text-gray-400 dark:text-gray-500">{getTier(skill.quality_score)}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-gray-900 dark:text-gray-100">{skill.stars.toLocaleString()}</td>
                <td className="px-4 py-3 text-right hidden sm:table-cell">
                  {skill.star_momentum >= 0.05 ? (
                    <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-semibold rounded-full bg-green-50 dark:bg-green-900/30 text-green-600">
                      <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 15l7-7 7 7" />
                      </svg>
                      HOT
                    </span>
                  ) : skill.star_momentum > 0 ? (
                    <span className="text-blue-500">
                      <svg className="w-3 h-3 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 15l7-7 7 7" />
                      </svg>
                    </span>
                  ) : (
                    <span className="text-gray-300 dark:text-gray-600 text-xs">-</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right text-gray-400 dark:text-gray-500 hidden md:table-cell">
                  {timeAgo(skill.last_commit_at)}
                </td>
              </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
