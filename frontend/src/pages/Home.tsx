import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { fetchSkills } from "../api/client";
import { CategoryFilter } from "../components/CategoryFilter";
import { DashboardStats } from "../components/DashboardStats";
import { HeroSection } from "../components/HeroSection";
import { LazySection } from "../components/LazySection";
import { HallOfFame } from "../components/HallOfFame";
import { RecentlyUpdated } from "../components/RecentlyUpdated";
import { Pagination } from "../components/Pagination";
import { SearchBar } from "../components/SearchBar";
import { SkeletonCards, SkeletonTrending, SkeletonList, SkeletonHallOfFame } from "../components/SkeletonCards";
import { SkillCard } from "../components/SkillCard";
import { SkillDetailPanel } from "../components/SkillDetailPanel";
import { SkillTable } from "../components/SkillTable";
import { ScenarioWorkflows } from "../components/ScenarioWorkflows";
import { SkillWorkflows } from "../components/SkillWorkflows";
import { PlatformRecommendations } from "../components/PlatformRecommendations";
import { SortControls } from "../components/SortControls";
import { SkillsMasters } from "../components/SkillsMasters";
import { TopRatedSection } from "../components/TopRatedSection";
import { TrendingSection } from "../components/TrendingSection";
import { ViewToggle } from "../components/ViewToggle";
import { SubmitSkill } from "../components/SubmitSkill";
import { NewsletterSubscribe } from "../components/NewsletterSubscribe";
import { NewsletterInline } from "../components/NewsletterInline";
import { NewThisWeek } from "../components/NewThisWeek";
import { FAQSection } from "../components/FAQSection";
import { FilterSidebar } from "../components/FilterSidebar";
import { SiteHeader } from "../components/SiteHeader";
import { ScrollToTop } from "../components/ScrollToTop";
import { SiteFooter } from "../components/SiteFooter";
import { useI18n } from "../i18n/I18nContext";
import { useUrlParams } from "../hooks/useUrlParams";
import { useStats } from "../hooks/useStats";
import { useLandingData } from "../hooks/useLandingData";
import type { PaginatedSkills, Skill } from "../types/skill";

export function Home() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const { params, tab, setTab, updateParams, setPage } = useUrlParams();
  const { stats, categories } = useStats();
  const { data: landingData, loading: landingLoading } = useLandingData();
  const [view, setView] = useState<"card" | "table">("card");

  // Explore tab data
  const [data, setData] = useState<PaginatedSkills | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch explore data when params change & tab is explore
  useEffect(() => {
    if (tab !== "explore") return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchSkills(params)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [params, tab]);

  // Skill detail panel (for overview sections)
  const [detailSkill, setDetailSkill] = useState<Skill | null>(null);

  const handleOpenRepo = useCallback((skill: Skill) => {
    window.open(skill.repo_url, "_blank", "noopener");
  }, []);

  const handleShowDetail = useCallback((skill: Skill) => {
    // Navigate using slug (owner/repo) for SEO-friendly URLs
    navigate(`/skill/${skill.repo_full_name}`);
  }, [navigate]);

  const handleNavigateSkill = useCallback(async (skillId: number) => {
    navigate(`/skill/${skillId}`);
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Helmet>
        <title>Agent Skills Hub - Discover Agent Skills, Tools & MCP Servers</title>
        <meta name="description" content="Discover, compare and explore 7800+ open-source Agent Skills, AI tools, MCP servers and Claude skills." />
        <meta property="og:title" content="Agent Skills Hub - Discover Agent Skills, Tools & MCP Servers" />
        <meta property="og:description" content="Discover, compare and explore 7800+ open-source Agent Skills, AI tools, MCP servers and Claude skills." />
        <meta property="og:type" content="website" />
        <meta name="twitter:card" content="summary_large_image" />
      </Helmet>

      <SiteHeader showTabs tab={tab} onTabChange={setTab} />

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Overview Tab */}
        {tab === "overview" && (
          <div className="animate-fade-in-up">
            {/* Hero: headline + search + trending tags + key stats */}
            <HeroSection
              stats={landingData?.stats ?? stats}
              onSearch={(query) => {
                updateParams({ search: query });
                setTab("explore");
              }}
            />
            <div id="trending" className="scroll-mt-44">
              {landingLoading && !landingData ? (
                <SkeletonTrending />
              ) : (
                <TrendingSection
                  onSelect={handleOpenRepo}
                  onShowDetail={handleShowDetail}
                  initialHot={landingData?.trending}
                  initialRising={landingData?.rising}
                />
              )}
            </div>
            <LazySection>
              <NewThisWeek onShowDetail={handleShowDetail} />
            </LazySection>
            <LazySection>
              <div id="categories" className="scroll-mt-44">
                <SkillWorkflows />
              </div>
            </LazySection>
            <LazySection>
              <NewsletterInline />
            </LazySection>
            <LazySection>
              <div id="top-rated" className="scroll-mt-44 grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
                {landingLoading && !landingData ? (
                  <>
                    <SkeletonList />
                    <SkeletonHallOfFame />
                  </>
                ) : (
                  <>
                    <TopRatedSection
                      onSelect={handleOpenRepo}
                      onShowDetail={handleShowDetail}
                      initialData={landingData?.top_rated}
                    />
                    <HallOfFame
                      onSelect={handleOpenRepo}
                      onShowDetail={handleShowDetail}
                      initialData={landingData?.hall_of_fame}
                    />
                  </>
                )}
              </div>
            </LazySection>
            <LazySection>
              <div id="masters" className="scroll-mt-44">
                <SkillsMasters />
              </div>
            </LazySection>
            <LazySection>
              <div id="newsletter" className="scroll-mt-44">
                <NewsletterSubscribe />
              </div>
            </LazySection>
            <LazySection>
              <div id="recent" className="scroll-mt-44">
                <RecentlyUpdated
                  onSelect={handleOpenRepo}
                  onShowDetail={handleShowDetail}
                  initialData={landingData?.recently_updated}
                />
              </div>
            </LazySection>
            <LazySection>
              <DashboardStats
                stats={landingData?.stats ?? stats}
                initialLanguages={landingData?.languages}
                initialTrending={landingData?.trending}
              />
            </LazySection>
            <LazySection>
              <div id="workflows" className="scroll-mt-44">
                <ScenarioWorkflows />
              </div>
            </LazySection>
            <LazySection>
              <div id="platforms">
                <PlatformRecommendations />
              </div>
            </LazySection>
            <LazySection>
              <FAQSection />
            </LazySection>
            <LazySection minHeight="100px">
              <div id="submit-skill">
                <SubmitSkill />
              </div>
            </LazySection>
          </div>
        )}

        {/* Explore Tab */}
        {tab === "explore" && (
          <>
            {/* Top Controls */}
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

            {/* Mobile-only inline filters (hidden on lg+) */}
            <div className="lg:hidden">
              <div className="mb-4">
                <CategoryFilter
                  categories={categories}
                  selected={params.category || ""}
                  onSelect={(category) => updateParams({ category })}
                />
              </div>
              <div className="flex flex-wrap items-center gap-2 mb-6">
                <span className="text-xs text-gray-400">{t("explore.size")}</span>
                {["micro", "small", "medium", "large"].map((s) => (
                  <button
                    key={s}
                    onClick={() => updateParams({ size_category: params.size_category === s ? undefined : s })}
                    className={`px-2.5 py-1 text-xs rounded-full border transition-colors cursor-pointer ${
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
                    className={`px-2.5 py-1 text-xs rounded-full border transition-colors cursor-pointer ${
                      params.platform === p
                        ? "bg-blue-600 text-white border-blue-600"
                        : "bg-white text-gray-600 border-gray-200 hover:border-blue-300"
                    }`}
                  >
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Desktop: Sidebar + Content */}
            <div className="flex gap-6">
              {/* Sidebar — desktop only */}
              <div className="hidden lg:block">
                <FilterSidebar
                  params={params}
                  onUpdate={updateParams}
                  categories={categories}
                />
              </div>

              {/* Main content */}
              <div className="flex-1 min-w-0">
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
                      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 stagger-children">
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
              </div>
            </div>
          </>
        )}
      </main>

      {/* Skill Detail Panel (for panel-based viewing, kept for backward compat) */}
      {detailSkill && (
        <SkillDetailPanel
          skill={detailSkill}
          onClose={() => setDetailSkill(null)}
          onNavigateSkill={handleNavigateSkill}
        />
      )}

      <ScrollToTop />
      <SiteFooter />
    </div>
  );
}
