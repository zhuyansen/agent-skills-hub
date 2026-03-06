import { useCallback, useState } from "react";
import { fetchSkillDetail } from "../api/client";
import { AuthButton } from "../components/AuthButton";
import { CategoryFilter } from "../components/CategoryFilter";
import { DashboardStats } from "../components/DashboardStats";
import { HallOfFame } from "../components/HallOfFame";
import { LanguageToggle } from "../components/LanguageToggle";
import { RecentlyUpdated } from "../components/RecentlyUpdated";
import { Pagination } from "../components/Pagination";
import { SearchBar } from "../components/SearchBar";
import { SkeletonCards } from "../components/SkeletonCards";
import { SkillCard } from "../components/SkillCard";
import { SkillDetailPanel } from "../components/SkillDetailPanel";
import { SkillTable } from "../components/SkillTable";
import { SkillWorkflows } from "../components/SkillWorkflows";
import { PlatformRecommendations } from "../components/PlatformRecommendations";
import { SortControls } from "../components/SortControls";
import { SkillsMasters } from "../components/SkillsMasters";
import { TopRatedSection } from "../components/TopRatedSection";
import { TrendingSection } from "../components/TrendingSection";
import { ViewToggle } from "../components/ViewToggle";
import { useI18n } from "../i18n/I18nContext";
import { useSkills } from "../hooks/useSkills";
import { useStats } from "../hooks/useStats";
import { timeAgo } from "../utils/time";
import type { Skill } from "../types/skill";

type Tab = "overview" | "explore";

export function Home() {
  const { t } = useI18n();
  const { data, loading, error, params, updateParams, setPage } = useSkills();
  const { stats, categories } = useStats();
  const [view, setView] = useState<"card" | "table">("card");
  const [tab, setTab] = useState<Tab>("overview");

  const [detailSkill, setDetailSkill] = useState<Skill | null>(null);

  const handleOpenRepo = useCallback((skill: Skill) => {
    window.open(skill.repo_url, "_blank", "noopener");
  }, []);

  const handleShowDetail = useCallback((skill: Skill) => {
    setDetailSkill(skill);
  }, []);

  const handleNavigateSkill = useCallback(async (skillId: number) => {
    try {
      const detail = await fetchSkillDetail(skillId);
      setDetailSkill(detail as unknown as Skill);
    } catch (err) {
      console.error("Failed to navigate to skill:", err);
    }
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-white via-white to-blue-50/50 border-b border-gray-200 sticky top-0 z-10 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 py-3 sm:py-4">
          <div className="flex items-center justify-between mb-3">
            <div className="min-w-0">
              <h1 className="text-lg sm:text-xl font-bold text-gray-900 flex items-center gap-2">
                <svg className="w-6 h-6 sm:w-7 sm:h-7 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="10" rx="2" strokeWidth="1.5"/><circle cx="9" cy="16" r="1.5" fill="currentColor"/><circle cx="15" cy="16" r="1.5" fill="currentColor"/><path d="M12 2v4M8 7h8a2 2 0 012 2v2H6V9a2 2 0 012-2z" strokeWidth="1.5" strokeLinecap="round"/></svg>
                <span className="truncate">Agent Skills Hub</span>
                <span className="ml-1 px-2 py-0.5 text-[10px] rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 text-white font-semibold tracking-wide uppercase shrink-0">Beta</span>
              </h1>
              <p className="text-xs sm:text-sm text-gray-500 mt-0.5 hidden sm:block">
                {t("header.subtitle")}
              </p>
            </div>
            <div className="flex items-center gap-2 sm:gap-3 shrink-0">
              <span className="text-sm text-gray-400 items-center gap-1.5 hidden sm:flex">
                <span className="w-2 h-2 rounded-full bg-green-400" />
                {t("header.lastUpdated")} {stats ? timeAgo(stats.last_sync_at) : "..."}
              </span>
              {/* GitHub repo link */}
              <a
                href="https://github.com/ZhuYansen/agent-skills-hub"
                target="_blank"
                rel="noopener noreferrer"
                className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-300"
                title="GitHub"
                aria-label="GitHub repository"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                </svg>
              </a>
              {/* X (Twitter) link */}
              <a
                href="https://x.com/GoSailGlobal"
                target="_blank"
                rel="noopener noreferrer"
                className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-300"
                title="X (Twitter)"
                aria-label="Follow on X"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
              </a>
              <LanguageToggle />
              <AuthButton />
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center gap-1 border-b border-gray-100 -mb-3 sm:-mb-4 pb-0">
            <button
              onClick={() => setTab("overview")}
              className={`px-3 sm:px-4 py-2 sm:py-2.5 text-sm font-medium border-b-2 transition-colors ${
                tab === "overview"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              <svg className="w-4 h-4 inline -mt-0.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"/></svg>
              {t("tab.overview")}
            </button>
            <button
              onClick={() => setTab("explore")}
              className={`px-3 sm:px-4 py-2 sm:py-2.5 text-sm font-medium border-b-2 transition-colors ${
                tab === "explore"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              <svg className="w-4 h-4 inline -mt-0.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/></svg>
              {t("tab.explore")}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Overview Tab */}
        {tab === "overview" && (
          <div className="animate-fade-in-up">
            <DashboardStats stats={stats} />
            <TrendingSection onSelect={handleOpenRepo} onShowDetail={handleShowDetail} />
            <RecentlyUpdated onSelect={handleOpenRepo} onShowDetail={handleShowDetail} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <TopRatedSection onSelect={handleOpenRepo} onShowDetail={handleShowDetail} />
              <HallOfFame onSelect={handleOpenRepo} onShowDetail={handleShowDetail} />
            </div>
            <SkillWorkflows />
            <PlatformRecommendations />
            <SkillsMasters />
          </div>
        )}

        {/* Explore Tab */}
        {tab === "explore" && (
          <>
            {/* Controls */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-4">
              <div className="w-full sm:w-64">
                <SearchBar
                  value={params.search || ""}
                  onChange={(search) => updateParams({ search })}
                />
              </div>
              <div className="flex items-center gap-3 flex-1">
                <SortControls
                  sortBy={params.sort_by}
                  sortOrder={params.sort_order}
                  onSortByChange={(sort_by) => updateParams({ sort_by })}
                  onSortOrderChange={(sort_order) => updateParams({ sort_order })}
                />
                <ViewToggle view={view} onChange={setView} />
              </div>
            </div>

            {/* Category Filter */}
            <div className="mb-4">
              <CategoryFilter
                categories={categories}
                selected={params.category || ""}
                onSelect={(category) => updateParams({ category })}
              />
            </div>

            {/* Platform / Size Filters */}
            <div className="flex flex-wrap items-center gap-2 mb-6">
              <span className="text-xs text-gray-400">{t("explore.size")}</span>
              {["micro", "small", "medium", "large"].map((s) => (
                <button
                  key={s}
                  onClick={() => updateParams({ size_category: params.size_category === s ? undefined : s })}
                  className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                    params.size_category === s
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-gray-600 border-gray-200 hover:border-blue-300"
                  }`}
                >
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              ))}
              <span className="text-xs text-gray-300 mx-1">|</span>
              <span className="text-xs text-gray-400">{t("explore.platform")}</span>
              {["python", "node", "go", "docker", "claude", "mcp"].map((p) => (
                <button
                  key={p}
                  onClick={() => updateParams({ platform: params.platform === p ? undefined : p })}
                  className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                    params.platform === p
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-gray-600 border-gray-200 hover:border-blue-300"
                  }`}
                >
                  {p.charAt(0).toUpperCase() + p.slice(1)}
                </button>
              ))}
            </div>

            {/* Error */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            {/* Loading Skeleton */}
            {loading && <SkeletonCards count={6} />}

            {/* Results */}
            {!loading && data && data.items.length > 0 && (
              <>
                <div className="text-sm text-gray-400 mb-3">
                  {t("explore.showing")} {(data.page - 1) * data.page_size + 1}-
                  {Math.min(data.page * data.page_size, data.total)} {t("explore.of")}{" "}
                  {data.total.toLocaleString()} {t("explore.skills")}
                </div>
                {view === "card" ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 stagger-children">
                    {data.items.map((skill) => (
                      <SkillCard key={skill.id} skill={skill} onSelect={handleOpenRepo} onShowDetail={handleShowDetail} />
                    ))}
                  </div>
                ) : (
                  <SkillTable skills={data.items} onSelect={handleOpenRepo} onShowDetail={handleShowDetail} />
                )}
                <Pagination
                  page={data.page}
                  totalPages={data.total_pages}
                  onPageChange={setPage}
                />
              </>
            )}

            {/* Empty State */}
            {!loading && data && data.items.length === 0 && (
              <div className="text-center py-16">
                <svg className="w-10 h-10 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/></svg>
                <h3 className="text-lg font-medium text-gray-700">{t("explore.noResults")}</h3>
                <p className="text-sm text-gray-500 mt-1">
                  {t("explore.noResultsHint")}
                </p>
              </div>
            )}
          </>
        )}
      </main>

      {/* Skill Detail Panel */}
      {detailSkill && (
        <SkillDetailPanel
          skill={detailSkill}
          onClose={() => setDetailSkill(null)}
          onNavigateSkill={handleNavigateSkill}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white mt-12">
        <div className="max-w-7xl mx-auto px-4 py-5 flex flex-col sm:flex-row items-center justify-between gap-2 text-sm text-gray-400">
          <span className="flex items-center gap-1.5">
            {t("footer.source")}
            <span className="mx-1">·</span>
            by{" "}
            <a
              href="https://x.com/GoSailGlobal"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-600 transition-colors"
            >
              Jason Zhu
            </a>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            {t("footer.autoUpdated")}
          </span>
        </div>
      </footer>
    </div>
  );
}
