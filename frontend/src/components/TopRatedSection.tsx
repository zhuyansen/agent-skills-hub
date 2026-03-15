import { useEffect, useState } from "react";
import { fetchTopRated } from "../api/client";
import { useI18n } from "../i18n/I18nContext";
import type { Skill } from "../types/skill";
import { formatStars, timeAgo } from "../utils/time";
import { ScoreBadge } from "./ScoreBadge";

interface Props {
  onSelect?: (skill: Skill) => void;
  onShowDetail?: (skill: Skill) => void;
  initialData?: Skill[];
}

export function TopRatedSection({ onSelect: _onSelect, onShowDetail, initialData }: Props) {
  const { t } = useI18n();
  const [items, setItems] = useState<Skill[]>(initialData ?? []);

  useEffect(() => {
    if (initialData && initialData.length > 0) setItems(initialData);
  }, [initialData]);

  useEffect(() => {
    if (items.length > 0) return;
    fetchTopRated(10).then(setItems).catch(console.error);
  }, [items.length]);

  if (items.length === 0) return null;

  return (
    <section className="mb-10">
      <div className="flex items-center gap-2 mb-4">
        <svg className="w-5 h-5 text-amber-400" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t("topRated.title")}</h2>
        <span className="text-sm text-gray-400 dark:text-gray-500">{t("topRated.subtitle")}</span>
        <span className="relative group">
          <svg className="w-4 h-4 text-gray-300 dark:text-gray-600 cursor-help" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 text-xs text-white bg-gray-800 dark:bg-gray-700 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
            {t("topRated.tooltip")}
          </span>
        </span>
      </div>
      <div className="bg-white dark:bg-gray-800/80 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden divide-y divide-gray-50 dark:divide-gray-800">
        {items.map((skill, i) => (
          <div
            key={skill.id}
            onClick={() => onShowDetail?.(skill)}
            className="flex items-center gap-3 px-4 py-3 hover:bg-blue-50/40 dark:hover:bg-gray-800 transition-colors cursor-pointer group"
          >
            <span className={`text-sm font-bold w-6 text-center ${i < 3 ? "text-blue-600" : "text-gray-400 dark:text-gray-500"}`}>
              {i + 1}
            </span>
            <ScoreBadge score={skill.score} size="sm" showTier />
            <img src={skill.author_avatar_url} alt={skill.author_name} loading="lazy" width={28} height={28} className="w-7 h-7 rounded-full border border-gray-100 dark:border-gray-800" />
            <div className="flex-1 min-w-0">
              <span
                onClick={(e) => {
                  e.stopPropagation();
                  window.open(skill.repo_url, "_blank", "noopener");
                }}
                className="font-medium text-sm text-gray-900 dark:text-gray-100 hover:text-blue-600 hover:underline transition-colors truncate block cursor-pointer"
              >
                {skill.repo_name}
              </span>
              <span className="text-xs text-gray-400 dark:text-gray-500">{skill.author_name}</span>
            </div>
            <span className="px-2 py-0.5 text-[10px] rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 hidden md:inline">
              {skill.category}
            </span>
            <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 w-16 justify-end">
              <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
              {formatStars(skill.stars)}
            </div>
            <span className="text-xs text-gray-400 dark:text-gray-500 w-14 text-right hidden sm:block">
              {timeAgo(skill.last_commit_at)}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
