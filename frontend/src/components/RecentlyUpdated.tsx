import { useEffect, useState } from "react";
import { fetchRecentlyUpdated } from "../api/client";
import { useI18n } from "../i18n/I18nContext";
import type { Skill } from "../types/skill";
import { formatStars, timeAgo } from "../utils/time";
import { ProjectTypeBadge } from "./ProjectTypeBadge";

interface Props {
  onSelect?: (skill: Skill) => void;
  onShowDetail?: (skill: Skill) => void;
  initialData?: Skill[];
}

export function RecentlyUpdated({ onSelect: _onSelect, onShowDetail, initialData }: Props) {
  const { t } = useI18n();
  const [items, setItems] = useState<Skill[]>(initialData ?? []);

  useEffect(() => {
    if (initialData && initialData.length > 0) setItems(initialData);
  }, [initialData]);

  useEffect(() => {
    if (items.length > 0) return;
    fetchRecentlyUpdated(8).then(setItems).catch(console.error);
  }, [items.length]);

  if (items.length === 0) return null;

  return (
    <section className="mb-10">
      <div className="flex items-center gap-2 mb-4">
        <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182"/></svg>
        <h2 className="text-lg font-bold text-gray-900">{t("recentlyUpdated.title")}</h2>
        <span className="text-sm text-gray-400 hidden sm:inline">{t("recentlyUpdated.subtitle")}</span>
      </div>
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden divide-y divide-gray-50">
        {items.map((skill) => (
          <div
            key={skill.id}
            onClick={() => onShowDetail?.(skill)}
            className="flex items-center gap-3 px-4 py-3 hover:bg-green-50/40 transition-colors cursor-pointer group"
          >
            {/* Avatar */}
            <img
              src={skill.author_avatar_url}
              alt={skill.author_name} loading="lazy"
              className="w-9 h-9 rounded-full border border-gray-100"
            />

            {/* Name + Description */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span
                  onClick={(e) => {
                    e.stopPropagation();
                    window.open(skill.repo_url, "_blank", "noopener");
                  }}
                  className="font-semibold text-sm text-gray-900 hover:text-green-600 hover:underline transition-colors truncate cursor-pointer"
                >
                  {skill.repo_name}
                </span>
                <ProjectTypeBadge type={skill.project_type} />
                {skill.language && (
                  <span className="px-1.5 py-0.5 text-[10px] rounded bg-gray-100 text-gray-500 hidden sm:inline">
                    {skill.language}
                  </span>
                )}
              </div>
              <span className="text-xs text-gray-400 truncate block">{skill.author_name}</span>
            </div>

            {/* Stars */}
            <div className="flex items-center gap-1 text-sm text-gray-500">
              <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
              {formatStars(skill.stars)}
            </div>

            {/* Time badge */}
            <span className="flex items-center gap-1 text-xs text-green-600 font-medium whitespace-nowrap">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              {timeAgo(skill.last_commit_at)}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
