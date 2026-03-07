import { useEffect, useState } from "react";
import { fetchTrending, fetchRising } from "../api/client";
import { useI18n } from "../i18n/I18nContext";
import type { Skill } from "../types/skill";
import { formatStars, timeAgo } from "../utils/time";

function formatVelocity(stars: number, createdAt: string | null): string {
  if (!createdAt) return "";
  const ageDays = Math.max((Date.now() - new Date(createdAt).getTime()) / 86400000, 1);
  const v = stars / ageDays;
  if (v >= 1000) return `${(v / 1000).toFixed(1)}k/day`;
  if (v >= 1) return `${v.toFixed(0)}/day`;
  return `${(v * 7).toFixed(0)}/week`;
}

interface Props {
  onSelect?: (skill: Skill) => void;
  onShowDetail?: (skill: Skill) => void;
}

export function TrendingSection({ onSelect: _onSelect, onShowDetail }: Props) {
  const { t } = useI18n();
  const [hot, setHot] = useState<Skill[]>([]);
  const [rising, setRising] = useState<Skill[]>([]);
  const [tab, setTab] = useState<"hot" | "rising">("hot");
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    fetchTrending(10).then(setHot).catch(console.error);
    fetchRising(7, 10).then(setRising).catch(console.error);
  }, []);

  const allItems = tab === "hot" ? hot : rising;
  const items = showAll ? allItems : allItems.slice(0, 5);
  if (hot.length === 0 && rising.length === 0) return null;

  return (
    <section className="mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-4">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-orange-500" fill="currentColor" viewBox="0 0 24 24"><path d="M12 23c-3.866 0-7-3.134-7-7 0-3.037 1.952-5.877 5-8 .928-.646 1.713-1.397 2.3-2.3.395-.608.7-1.28.7-2.2 0 3 2 5.5 2 5.5s1-1.5 1-3.5c3.048 2.123 5 4.963 5 8 0 3.866-3.134 7-7 7zm0-2c2.761 0 5-2.239 5-5 0-1.555-.629-3.06-1.693-4.32C14.44 13.08 13 14.5 12 14.5s-2.44-1.42-3.307-2.82C7.629 12.94 7 14.445 7 16c0 2.761 2.239 5 5 5z"/></svg>
          <h2 className="text-lg font-bold text-gray-900">{t("trending.title")}</h2>
          <span className="text-sm text-gray-400 hidden sm:inline">{t("trending.subtitle")}</span>
        </div>
        {/* Sub-tabs */}
        <div className="flex sm:ml-auto bg-gray-100 rounded-lg p-0.5 self-start">
          <button
            onClick={() => { setTab("hot"); setShowAll(false); }}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
              tab === "hot" ? "bg-white text-orange-600 shadow-sm" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            <svg className="w-3 h-3 inline -mt-0.5 mr-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"/></svg>
            {t("trending.starVelocity")}
          </button>
          <button
            onClick={() => { setTab("rising"); setShowAll(false); }}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
              tab === "rising" ? "bg-white text-green-600 shadow-sm" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            <svg className="w-3 h-3 inline -mt-0.5 mr-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 21c0-4-3-7-7-7 4 0 7-3 7-7 0 4 3 7 7 7-4 0-7 3-7 7z"/></svg>
            {t("trending.newThisWeek")}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {items.map((skill, i) => (
          <div
            key={skill.id}
            onClick={() => onShowDetail?.(skill)}
            className="relative bg-white border border-gray-200 rounded-xl p-4 hover:shadow-md hover:border-orange-200 hover:-translate-y-0.5 transition-all cursor-pointer group"
          >
            {/* Rank badge */}
            <div className={`absolute -top-2 -left-2 w-7 h-7 rounded-full text-white text-xs flex items-center justify-center font-bold shadow-md ${
              i < 3 ? "bg-gradient-to-br from-orange-400 to-red-500" : "bg-gray-400"
            }`}>
              {i + 1}
            </div>

            {/* Author with avatar */}
            <div className="flex items-center gap-2 mb-2">
              <img
                src={skill.author_avatar_url}
                alt=""
                className="w-8 h-8 rounded-full border border-gray-100"
              />
              <div className="min-w-0 flex-1">
                <span className="text-xs text-gray-500 truncate block">{skill.author_name}</span>
                {tab === "hot" && (
                  <span className="text-[10px] text-orange-500 font-semibold">
                    {formatVelocity(skill.stars, skill.created_at)}
                  </span>
                )}
              </div>
            </div>

            <h3
              onClick={(e) => {
                e.stopPropagation();
                window.open(skill.repo_url, "_blank", "noopener");
              }}
              className="font-semibold text-sm text-gray-900 truncate hover:text-orange-600 hover:underline transition-colors cursor-pointer"
            >
              {skill.repo_name}
            </h3>
            <p className="text-xs text-gray-400 mt-1 line-clamp-2">
              {skill.description || "No description"}
            </p>

            <div className="flex items-center justify-between mt-3 text-xs text-gray-400">
              <span className="flex items-center gap-1">
                <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                </svg>
                <strong className="text-gray-700">
                  {formatStars(skill.stars)}
                </strong>
              </span>
              <span>{timeAgo(tab === "hot" ? skill.last_commit_at : skill.created_at)}</span>
            </div>
          </div>
        ))}
      </div>

      {allItems.length > 5 && (
        <div className="flex justify-center mt-4">
          <button
            onClick={() => setShowAll(!showAll)}
            className="px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
          >
            {showAll ? t("trending.showLess") : t("trending.showMore")}
          </button>
        </div>
      )}
    </section>
  );
}
