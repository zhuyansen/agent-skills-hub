import { useEffect, useState, useCallback } from "react";
import { fetchTrending, fetchRising, fetchTrendingWeeks, fetchTrendingHistory } from "../api/client";
import { useI18n } from "../i18n/I18nContext";
import type { Skill } from "../types/skill";
import type { WeeklyTrendingEntry, TrendingWeek } from "../types/skill";
import { formatStars, timeAgo } from "../utils/time";

function formatWeekRange(weekStart: string, weekEnd: string): string {
  const start = new Date(weekStart + "T00:00:00");
  const end = new Date(weekEnd + "T00:00:00");
  const opts: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" };
  const startStr = start.toLocaleDateString("en-US", opts);
  const endStr = end.toLocaleDateString("en-US", { ...opts, year: "numeric" });
  return `${startStr} – ${endStr}`;
}

interface Props {
  onSelect?: (skill: Skill) => void;
  onShowDetail?: (skill: Skill) => void;
  initialHot?: Skill[];
  initialRising?: Skill[];
}

export function TrendingSection({ onSelect: _onSelect, onShowDetail, initialHot, initialRising }: Props) {
  const { t } = useI18n();
  const [hot, setHot] = useState<Skill[]>(initialHot ?? []);
  const [rising, setRising] = useState<Skill[]>(initialRising ?? []);
  const [tab, setTab] = useState<"rising" | "history">("rising");

  // History state
  const [weeks, setWeeks] = useState<TrendingWeek[]>([]);
  const [weeksLoaded, setWeeksLoaded] = useState(false);
  const [weekIdx, setWeekIdx] = useState(0);
  const [historyItems, setHistoryItems] = useState<WeeklyTrendingEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [risingExpanded, setRisingExpanded] = useState(false);

  useEffect(() => {
    if (initialHot && initialHot.length > 0) setHot(initialHot);
  }, [initialHot]);

  useEffect(() => {
    if (initialRising && initialRising.length > 0) setRising(initialRising);
  }, [initialRising]);

  useEffect(() => {
    if (hot.length > 0) return;
    fetchTrending(10).then(setHot).catch(console.error);
  }, [hot.length]);

  useEffect(() => {
    if (rising.length > 0) return;
    fetchRising(7, 10).then(setRising).catch(console.error);
  }, [rising.length]);

  // Load available weeks when history tab is first selected
  useEffect(() => {
    if (tab !== "history" || weeksLoaded) return;
    setWeeksLoaded(true);
    fetchTrendingWeeks()
      .then((w) => {
        setWeeks(w);
        setWeekIdx(0);
      })
      .catch(console.error);
  }, [tab, weeksLoaded]);

  // Load history data when week changes
  const loadHistory = useCallback(
    async (idx: number) => {
      if (weeks.length === 0 || idx < 0 || idx >= weeks.length) return;
      setHistoryLoading(true);
      try {
        const data = await fetchTrendingHistory(weeks[idx].week_start);
        setHistoryItems(data);
      } catch (e) {
        console.error(e);
        setHistoryItems([]);
      } finally {
        setHistoryLoading(false);
      }
    },
    [weeks],
  );

  useEffect(() => {
    if (tab === "history" && weeks.length > 0) {
      loadHistory(weekIdx);
    }
  }, [tab, weekIdx, weeks, loadHistory]);

  const items = tab === "rising" ? rising : [];
  if (hot.length === 0 && rising.length === 0) return null;

  const currentWeek = weeks[weekIdx];
  const canPrev = weekIdx < weeks.length - 1;
  const canNext = weekIdx > 0;

  return (
    <section className="mb-10">
      <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-4">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-orange-500" fill="currentColor" viewBox="0 0 24 24"><path d="M12 23c-3.866 0-7-3.134-7-7 0-3.037 1.952-5.877 5-8 .928-.646 1.713-1.397 2.3-2.3.395-.608.7-1.28.7-2.2 0 3 2 5.5 2 5.5s1-1.5 1-3.5c3.048 2.123 5 4.963 5 8 0 3.866-3.134 7-7 7zm0-2c2.761 0 5-2.239 5-5 0-1.555-.629-3.06-1.693-4.32C14.44 13.08 13 14.5 12 14.5s-2.44-1.42-3.307-2.82C7.629 12.94 7 14.445 7 16c0 2.761 2.239 5 5 5z"/></svg>
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t("trending.title")}</h2>
          <span className="text-sm text-gray-400 dark:text-gray-500 hidden sm:inline">{t("trending.subtitle")}</span>
        </div>
        {/* Sub-tabs */}
        <div className="flex sm:ml-auto bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5 self-start">
          <button
            onClick={() => setTab("rising")}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
              tab === "rising" ? "bg-white dark:bg-gray-700 text-green-600 shadow-sm" : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
            }`}
          >
            <svg className="w-3 h-3 inline -mt-0.5 mr-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 21c0-4-3-7-7-7 4 0 7-3 7-7 0 4 3 7 7 7-4 0-7 3-7 7z"/></svg>
            {t("trending.newThisWeek")}
          </button>
          <button
            onClick={() => setTab("history")}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
              tab === "history" ? "bg-white dark:bg-gray-700 text-orange-600 shadow-sm" : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
            }`}
          >
            <svg className="w-3 h-3 inline -mt-0.5 mr-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"/></svg>
            {t("trending.starVelocityHistory")}
          </button>
        </div>
      </div>

      {/* Week navigator for history tab */}
      {tab === "history" && weeks.length > 0 && currentWeek && (
        <div className="flex items-center justify-center gap-3 mb-4">
          <button
            onClick={() => canPrev && setWeekIdx(weekIdx + 1)}
            disabled={!canPrev}
            className={`p-1.5 rounded-lg transition-colors ${
              canPrev ? "hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300" : "text-gray-300 dark:text-gray-600 cursor-not-allowed"
            }`}
            title={t("trending.prevWeek")}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-200 min-w-[180px] text-center">
            {formatWeekRange(currentWeek.week_start, currentWeek.week_end)}
          </span>
          <button
            onClick={() => canNext && setWeekIdx(weekIdx - 1)}
            disabled={!canNext}
            className={`p-1.5 rounded-lg transition-colors ${
              canNext ? "hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300" : "text-gray-300 dark:text-gray-600 cursor-not-allowed"
            }`}
            title={t("trending.nextWeek")}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
          {weekIdx !== 0 && (
            <button
              onClick={() => setWeekIdx(0)}
              className="text-xs text-orange-500 hover:text-orange-600 font-medium ml-1"
            >
              {t("trending.currentWeek")}
            </button>
          )}
        </div>
      )}

      {/* History loading / empty state */}
      {tab === "history" && historyLoading && (
        <div className="text-center py-8 text-gray-400 dark:text-gray-500 text-sm">Loading...</div>
      )}
      {tab === "history" && !historyLoading && weeks.length === 0 && (
        <div className="text-center py-8 text-gray-400 dark:text-gray-500 text-sm">{t("trending.noHistory")}</div>
      )}

      {/* Grid: rising tab */}
      {tab === "rising" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {items.map((skill, i) => (
            <div
              key={skill.id}
              onClick={() => onShowDetail?.(skill)}
              className={`relative bg-white dark:bg-gray-800/80 border border-gray-200 dark:border-gray-700 rounded-xl p-4 hover:shadow-md hover:border-orange-200 dark:hover:border-orange-500 hover:-translate-y-0.5 transition-all cursor-pointer group${i >= 4 && !risingExpanded ? " hidden sm:block" : ""}`}
            >
              {/* Rank badge */}
              <div className={`absolute -top-2 -left-2 w-7 h-7 rounded-full text-white text-xs flex items-center justify-center font-bold shadow-md ${
                i < 3 ? "bg-gradient-to-br from-green-400 to-emerald-500" : "bg-gray-400"
              }`}>
                {i + 1}
              </div>

              {/* Author with avatar */}
              <div className="flex items-center gap-2 mb-2">
                <img
                  src={skill.author_avatar_url}
                  alt={skill.author_name} loading="lazy"
                  width={32} height={32}
                  className="w-8 h-8 rounded-full border border-gray-100 dark:border-gray-700"
                />
                <div className="min-w-0 flex-1">
                  <span className="text-xs text-gray-500 dark:text-gray-400 truncate block">{skill.author_name}</span>
                </div>
              </div>

              <h3
                onClick={(e) => {
                  e.stopPropagation();
                  window.open(skill.repo_url, "_blank", "noopener");
                }}
                className="font-semibold text-sm text-gray-900 dark:text-gray-100 truncate hover:text-orange-600 hover:underline transition-colors cursor-pointer"
              >
                {skill.repo_name}
              </h3>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1 line-clamp-2">
                {skill.description || "No description"}
              </p>

              <div className="flex items-center justify-between mt-3 text-xs text-gray-400 dark:text-gray-500">
                <span className="flex items-center gap-1">
                  <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                  </svg>
                  <strong className="text-gray-700 dark:text-gray-200">
                    {formatStars(skill.stars)}
                  </strong>
                </span>
                <span>{timeAgo(skill.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
      {tab === "rising" && items.length > 4 && !risingExpanded && (
        <button
          onClick={() => setRisingExpanded(true)}
          className="sm:hidden w-full py-2.5 mt-2 text-xs text-blue-500 font-medium cursor-pointer"
        >
          {t("common.showAll").replace("{count}", String(items.length))}
        </button>
      )}

      {/* Grid: history tab */}
      {tab === "history" && !historyLoading && historyItems.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {historyItems.map((entry) => (
            <div
              key={`${entry.rank}-${entry.skill_id}`}
              onClick={() => {
                // Construct a minimal Skill-like object for the detail panel
                const skillLike = {
                  id: entry.skill_id,
                  repo_full_name: entry.repo_full_name,
                  repo_name: entry.repo_name,
                  repo_url: entry.repo_url,
                  description: entry.description,
                  author_name: entry.author_name,
                  author_avatar_url: entry.author_avatar_url,
                  stars: entry.stars,
                  category: entry.category,
                  created_at: entry.created_at_snap,
                  last_commit_at: entry.last_commit_at_snap,
                } as Skill;
                onShowDetail?.(skillLike);
              }}
              className="relative bg-white dark:bg-gray-800/80 border border-gray-200 dark:border-gray-700 rounded-xl p-4 hover:shadow-md hover:border-orange-200 dark:hover:border-orange-500 hover:-translate-y-0.5 transition-all cursor-pointer group"
            >
              {/* Rank badge */}
              <div className={`absolute -top-2 -left-2 w-7 h-7 rounded-full text-white text-xs flex items-center justify-center font-bold shadow-md ${
                entry.rank <= 3 ? "bg-gradient-to-br from-orange-400 to-red-500" : "bg-gray-400"
              }`}>
                {entry.rank}
              </div>

              {/* Author with avatar */}
              <div className="flex items-center gap-2 mb-2">
                <img
                  src={entry.author_avatar_url}
                  alt={entry.author_name} loading="lazy"
                  width={32} height={32}
                  className="w-8 h-8 rounded-full border border-gray-100 dark:border-gray-700"
                />
                <div className="min-w-0 flex-1">
                  <span className="text-xs text-gray-500 dark:text-gray-400 truncate block">{entry.author_name}</span>
                  <span className="text-[10px] text-orange-500 font-semibold">
                    {entry.star_velocity >= 1000
                      ? `${(entry.star_velocity / 1000).toFixed(1)}k/day`
                      : entry.star_velocity >= 1
                        ? `${entry.star_velocity.toFixed(0)}/day`
                        : `${(entry.star_velocity * 7).toFixed(0)}/week`}
                  </span>
                </div>
              </div>

              <h3
                onClick={(e) => {
                  e.stopPropagation();
                  window.open(entry.repo_url, "_blank", "noopener");
                }}
                className="font-semibold text-sm text-gray-900 dark:text-gray-100 truncate hover:text-orange-600 hover:underline transition-colors cursor-pointer"
              >
                {entry.repo_name}
              </h3>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1 line-clamp-2">
                {entry.description || "No description"}
              </p>

              <div className="flex items-center justify-between mt-3 text-xs text-gray-400 dark:text-gray-500">
                <span className="flex items-center gap-1">
                  <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                  </svg>
                  <strong className="text-gray-700 dark:text-gray-200">
                    {formatStars(entry.stars)}
                  </strong>
                </span>
                <span>{timeAgo(entry.last_commit_at_snap)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
