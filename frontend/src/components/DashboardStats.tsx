import { useEffect, useState } from "react";
import { fetchLanguageStats, fetchTrending } from "../api/client";
import { useI18n } from "../i18n/I18nContext";
import type { Skill, Stats } from "../types/skill";
import { timeAgo } from "../utils/time";
import { CategoryPieChart } from "./charts/CategoryPieChart";
import { LanguageBarChart } from "./charts/LanguageBarChart";
import { StarTrendChart } from "./charts/StarTrendChart";

const LANG_COLORS: Record<string, string> = {
  TypeScript: "#3178c6",
  Python: "#3572A5",
  JavaScript: "#f1e05a",
  Go: "#00ADD8",
  Rust: "#dea584",
  Java: "#b07219",
  Ruby: "#701516",
  "C#": "#178600",
  Shell: "#89e051",
  Kotlin: "#A97BFF",
};

interface Props {
  stats: Stats | null;
  initialLanguages?: { language: string; count: number }[];
  initialTrending?: Skill[];
}

export function DashboardStats({ stats, initialLanguages, initialTrending }: Props) {
  const { t } = useI18n();
  const [langs, setLangs] = useState<{ language: string; count: number }[]>(initialLanguages ?? []);
  const [trendingSkills, setTrendingSkills] = useState<Skill[]>(initialTrending ?? []);
  const [showCharts, setShowCharts] = useState(false);

  // Sync props → state when landing data arrives asynchronously
  useEffect(() => {
    if (initialLanguages && initialLanguages.length > 0) setLangs(initialLanguages);
  }, [initialLanguages]);

  useEffect(() => {
    if (initialTrending && initialTrending.length > 0) setTrendingSkills(initialTrending);
  }, [initialTrending]);

  // Fallback: fetch independently if no initial data provided
  useEffect(() => {
    if (langs.length > 0) return;
    fetchLanguageStats().then(setLangs).catch(console.error);
  }, [langs.length]);

  // Lazy-load trending data when charts are expanded
  useEffect(() => {
    if (!showCharts || trendingSkills.length > 0) return;
    fetchTrending(15).then(setTrendingSkills).catch(console.error);
  }, [showCharts, trendingSkills.length]);

  if (!stats) return null;

  const totalLangs = langs.reduce((s, l) => s + l.count, 0) || 1;

  return (
    <section className="mb-10">
      {/* Stat Cards — 3 key metrics */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="bg-white border border-gray-200 rounded-xl p-3 sm:p-4">
          <div className="text-xl sm:text-2xl font-bold text-gray-900">{stats.total_skills.toLocaleString()}</div>
          <div className="text-xs sm:text-sm text-gray-500 mt-0.5">{t("stats.totalSkills")}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-3 sm:p-4">
          <div className="text-xl sm:text-2xl font-bold text-blue-600">{stats.avg_score.toFixed(1)}</div>
          <div className="text-xs sm:text-sm text-gray-500 mt-0.5">{t("stats.avgScore")}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-3 sm:p-4">
          <div className="flex items-center gap-2">
            <div className="text-xl sm:text-2xl font-bold text-green-600">{timeAgo(stats.last_sync_at)}</div>
            {stats.last_sync_status === "completed" && (
              <span className="w-2 h-2 rounded-full bg-green-400 shrink-0" title="Sync healthy" />
            )}
            {stats.last_sync_status === "running" && (
              <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse shrink-0" title="Sync running" />
            )}
            {stats.last_sync_status === "failed" && (
              <span className="w-2 h-2 rounded-full bg-red-400 shrink-0" title="Sync failed" />
            )}
          </div>
          <div className="text-xs sm:text-sm text-gray-500 mt-0.5">{t("stats.lastSync")}</div>
        </div>
      </div>

      {/* Category Distribution + Language Bar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Categories */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h3 className="font-semibold text-gray-900 mb-3">{t("stats.categoryDist")}</h3>
          <div className="space-y-2">
            {stats.categories.map((cat) => {
              const pct = ((cat.count / stats.total_skills) * 100).toFixed(1);
              return (
                <div key={cat.name} className="flex items-center gap-3">
                  <span className="text-xs text-gray-600 w-28 truncate">{cat.name}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-400 w-16 text-right">{cat.count} ({pct}%)</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Languages */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h3 className="font-semibold text-gray-900 mb-3">{t("stats.topLanguages")}</h3>
          {/* Stacked Bar */}
          <div className="flex h-4 rounded-full overflow-hidden mb-4">
            {langs.map((l) => (
              <div
                key={l.language}
                className="h-full transition-all"
                style={{
                  width: `${(l.count / totalLangs) * 100}%`,
                  backgroundColor: LANG_COLORS[l.language] || "#94a3b8",
                }}
                title={`${l.language}: ${l.count}`}
              />
            ))}
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1.5">
            {langs.map((l) => (
              <div key={l.language} className="flex items-center gap-1.5 text-xs">
                <span
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: LANG_COLORS[l.language] || "#94a3b8" }}
                />
                <span className="text-gray-600">{l.language}</span>
                <span className="text-gray-400">{l.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Toggle for interactive charts */}
      <div className="flex justify-center mt-4">
        <button
          onClick={() => setShowCharts(!showCharts)}
          className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-gray-500 hover:text-blue-600 bg-white border border-gray-200 rounded-lg hover:border-blue-200 transition-colors cursor-pointer"
        >
          <svg className={`w-3.5 h-3.5 transition-transform ${showCharts ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
          {showCharts ? t("trending.showLess") : t("chart.categoryDist")}
        </button>
      </div>

      {/* Interactive Charts (collapsible) */}
      {showCharts && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
          <CategoryPieChart categories={stats.categories} total={stats.total_skills} />
          <LanguageBarChart languages={langs} />
          {trendingSkills.length > 0 && (
            <div className="lg:col-span-2">
              <StarTrendChart skills={trendingSkills} />
            </div>
          )}
        </div>
      )}
    </section>
  );
}
