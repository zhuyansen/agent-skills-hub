import { useEffect, useState } from "react";
import { fetchMostStarred } from "../api/client";
import { useI18n } from "../i18n/I18nContext";
import type { Skill } from "../types/skill";
import { formatStars } from "../utils/time";
import { ScoreBadge } from "./ScoreBadge";

interface Props {
  onSelect?: (skill: Skill) => void;
  onShowDetail?: (skill: Skill) => void;
  initialData?: Skill[];
}

export function HallOfFame({ onSelect: _onSelect, onShowDetail, initialData }: Props) {
  const { t } = useI18n();
  const [items, setItems] = useState<Skill[]>(initialData ?? []);
  const [expanded, setExpanded] = useState(false);

  // Sync prop → state when landing data arrives asynchronously
  useEffect(() => {
    if (initialData && initialData.length > 0) setItems(initialData);
  }, [initialData]);

  // Fallback: fetch independently if no initial data
  useEffect(() => {
    if (items.length > 0) return;
    fetchMostStarred(10).then(setItems).catch(console.error);
  }, [items.length]);

  if (items.length === 0) return null;

  const top3 = items.slice(0, 3);
  const rest = items.slice(3);

  return (
    <section className="mb-10">
      <div className="flex items-center gap-2 mb-4">
        <svg className="w-5 h-5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M16.5 3.5h3a1 1 0 011 1v2a3 3 0 01-3 3h-1M7.5 3.5h-3a1 1 0 00-1 1v2a3 3 0 003 3h1M8 3.5h8v5a4 4 0 01-8 0v-5zM10 14.5v2.5h4v-2.5M8 20h8"/></svg>
        <h2 className="text-lg font-bold text-gray-900">{t("hallOfFame.title")}</h2>
        <span className="text-sm text-gray-400">{t("hallOfFame.subtitle")}</span>
      </div>

      {/* Top 3 Podium */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
        {top3.map((skill, i) => {
          const rankColors = ["bg-amber-400 text-white", "bg-gray-400 text-white", "bg-orange-400 text-white"];
          const borders = ["border-amber-300 bg-amber-50/50", "border-gray-300 bg-gray-50/50", "border-orange-200 bg-orange-50/30"];
          return (
            <div
              key={skill.id}
              onClick={() => onShowDetail?.(skill)}
              className={`border-2 ${borders[i]} rounded-xl p-5 hover:shadow-lg transition-all cursor-pointer`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className={`w-7 h-7 rounded-full ${rankColors[i]} text-xs font-bold flex items-center justify-center shadow-sm`}>{i + 1}</span>
                <ScoreBadge score={skill.score} size="sm" />
              </div>
              <div className="flex items-center gap-2 mb-1">
                <img src={skill.author_avatar_url} alt={skill.author_name} loading="lazy" width={20} height={20} className="w-5 h-5 rounded-full" />
                <span className="text-xs text-gray-500">{skill.author_name}</span>
              </div>
              <h3
                onClick={(e) => {
                  e.stopPropagation();
                  window.open(skill.repo_url, "_blank", "noopener");
                }}
                className="font-bold text-gray-900 truncate hover:text-blue-600 hover:underline cursor-pointer"
              >
                {skill.repo_name}
              </h3>
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">{skill.description || "No description"}</p>
              <div className="mt-3 flex items-center gap-1 text-sm">
                <svg className="w-4 h-4 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                </svg>
                <strong>{skill.stars.toLocaleString()}</strong>
              </div>
            </div>
          );
        })}
      </div>

      {/* 4-10 Compact List */}
      <div className={`bg-white border border-gray-200 rounded-xl divide-y divide-gray-100${!expanded ? " hidden sm:block" : ""}`}>
        {rest.map((skill, i) => (
          <div
            key={skill.id}
            onClick={() => onShowDetail?.(skill)}
            className="flex items-center gap-4 px-4 py-3 hover:bg-gray-50 transition-colors cursor-pointer"
          >
            <span className="text-sm font-bold text-gray-400 w-6 text-center">{i + 4}</span>
            <img src={skill.author_avatar_url} alt={skill.author_name} loading="lazy" width={28} height={28} className="w-7 h-7 rounded-full" />
            <div className="flex-1 min-w-0">
              <span
                onClick={(e) => {
                  e.stopPropagation();
                  window.open(skill.repo_url, "_blank", "noopener");
                }}
                className="font-medium text-sm text-gray-900 hover:text-blue-600 hover:underline cursor-pointer"
              >
                {skill.repo_name}
              </span>
              <span className="text-xs text-gray-400 ml-2">{skill.author_name}</span>
            </div>
            <span className="px-2 py-0.5 text-xs rounded-full bg-indigo-50 text-indigo-600 hidden sm:inline">
              {skill.category}
            </span>
            <div className="flex items-center gap-1 text-sm text-gray-500 w-20 justify-end">
              <svg className="w-3.5 h-3.5 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
              {formatStars(skill.stars)}
            </div>
          </div>
        ))}
      </div>
      {rest.length > 0 && !expanded && (
        <button
          onClick={() => setExpanded(true)}
          className="sm:hidden w-full py-2.5 mt-2 text-xs text-blue-500 font-medium cursor-pointer"
        >
          {t("common.showAll").replace("{count}", String(rest.length + 3))}
        </button>
      )}
    </section>
  );
}
