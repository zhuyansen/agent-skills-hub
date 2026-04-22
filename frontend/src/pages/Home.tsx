import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { fetchSkills } from "../api/client";
import { CategoryFilter } from "../components/CategoryFilter";

const DashboardStats = lazy(() =>
  import("../components/DashboardStats").then((m) => ({
    default: m.DashboardStats,
  })),
);
import { HeroSection } from "../components/HeroSection";
import { LazySection } from "../components/LazySection";
import { HallOfFame } from "../components/HallOfFame";
import { RecentlyUpdated } from "../components/RecentlyUpdated";
import { Pagination } from "../components/Pagination";
import { SearchBar } from "../components/SearchBar";
import {
  SkeletonCards,
  SkeletonTrending,
  SkeletonList,
  SkeletonHallOfFame,
} from "../components/SkeletonCards";
import { SkillCard } from "../components/SkillCard";
import { SkillDetailPanel } from "../components/SkillDetailPanel";
import { SkillTable } from "../components/SkillTable";
import { ScenarioWorkflows } from "../components/ScenarioWorkflows";
import { SkillWorkflows } from "../components/SkillWorkflows";
import { PlatformRecommendations } from "../components/PlatformRecommendations";
import { SortControls } from "../components/SortControls";
import { SkillsMasters } from "../components/SkillsMasters";
import { fetchMasters, fetchOrgBuilders } from "../api/client";
import type { Master, OrgBuilder } from "../api/client";
import { TopRatedSection } from "../components/TopRatedSection";
import { TrendingSection } from "../components/TrendingSection";
import { ViewToggle } from "../components/ViewToggle";
import { SubmitSkill } from "../components/SubmitSkill";
import { NewsletterSubscribe } from "../components/NewsletterSubscribe";

import { NewThisWeek } from "../components/NewThisWeek";
import { FAQSection } from "../components/FAQSection";
import { FilterSidebar } from "../components/FilterSidebar";
import { InstallGuide } from "../components/InstallGuide";
import { EcosystemNav } from "../components/EcosystemNav";
import { ScenarioTagCloud } from "../components/ScenarioTagCloud";
import { ProblemSection } from "../components/ProblemSection";
import { HowItWorksSection } from "../components/HowItWorksSection";
import { SubcategoryChips } from "../components/SubcategoryChips";
import { getCategoriesForLayer } from "../utils/ecosystem";
import { inferSubcategory } from "../utils/subcategories";
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

  // Prefetch Masters data eagerly (don't wait for LazySection)
  const [prefetchedMasters, setPrefetchedMasters] = useState<
    Master[] | undefined
  >();
  const [prefetchedOrgs, setPrefetchedOrgs] = useState<
    OrgBuilder[] | undefined
  >();
  useEffect(() => {
    let cancelled = false;
    fetchMasters()
      .then((data) => {
        if (!cancelled) {
          const cleaned = data
            .map((m) => ({
              ...m,
              top_repos: (m.top_repos || []).filter((r) => r.stars > 0),
            }))
            .filter(
              (m) => m.total_stars > 0 || m.x_followers > 0 || !m.discovered,
            );
          setPrefetchedMasters(cleaned);
        }
      })
      .catch(() => {});
    fetchOrgBuilders()
      .then((data) => {
        if (!cancelled)
          setPrefetchedOrgs(data.filter((o) => o.total_stars > 0));
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  // Explore tab data
  const [data, setData] = useState<PaginatedSkills | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [subcategory, setSubcategory] = useState<string | null>(null);

  // Clear subcategory when category changes
  useEffect(() => {
    setSubcategory(null);
  }, [params.category]);

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
    return () => {
      cancelled = true;
    };
  }, [params, tab]);

  // Skill detail panel (for overview sections)
  const [detailSkill, setDetailSkill] = useState<Skill | null>(null);

  const handleOpenRepo = useCallback((skill: Skill) => {
    window.open(skill.repo_url, "_blank", "noopener");
  }, []);

  const handleShowDetail = useCallback(
    (skill: Skill) => {
      // Navigate using slug (owner/repo) for SEO-friendly URLs
      navigate(`/skill/${skill.repo_full_name}/`);
    },
    [navigate],
  );

  const handleNavigateSkill = useCallback(
    async (skillId: number) => {
      navigate(`/skill/${skillId}/`);
    },
    [navigate],
  );

  const totalSkills =
    landingData?.stats?.total_skills ?? stats?.total_skills ?? 54000;
  const skillCount = `${Math.floor(totalSkills / 1000).toLocaleString()},000+`;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Helmet>
        <title>
          AgentSkillsHub — Claude Skills / MCP Server / Agent Tools Directory
        </title>
        <meta
          name="description"
          content={`The open-source directory for Claude Skills, MCP Servers & Agent Tools. ${skillCount} skills · quality-scored on 10 dimensions · refreshed every 8 hours. Find, compare, install.`}
        />
        <meta
          property="og:title"
          content="AgentSkillsHub — Claude Skills / MCP Server / Agent Tools Directory"
        />
        <meta
          property="og:description"
          content={`${skillCount} Claude Skills, MCP Servers & Agent Tools — quality-scored, filtered, refreshed every 8 hours.`}
        />
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
            <EcosystemNav
              onSelectCategory={(category) => {
                updateParams({ category });
                setTab("explore");
              }}
              onSelectLayer={(layer) => {
                updateParams({
                  category: getCategoriesForLayer(layer).join(","),
                });
                setTab("explore");
              }}
            />
            <ScenarioTagCloud />
            <ProblemSection />
            <HowItWorksSection />
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
            <div id="categories" className="scroll-mt-44">
              <LazySection>
                <SkillWorkflows />
              </LazySection>
            </div>
            <div id="top-rated" className="scroll-mt-44">
              <LazySection>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
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
            </div>
            <div id="masters" className="scroll-mt-44">
              <LazySection>
                <SkillsMasters
                  prefetchedMasters={prefetchedMasters}
                  prefetchedOrgs={prefetchedOrgs}
                />
              </LazySection>
            </div>
            <div id="newsletter" className="scroll-mt-44">
              <LazySection>
                <NewsletterSubscribe />
              </LazySection>
            </div>
            <div id="recent" className="scroll-mt-44">
              <LazySection>
                <RecentlyUpdated
                  onSelect={handleOpenRepo}
                  onShowDetail={handleShowDetail}
                  initialData={landingData?.recently_updated}
                />
              </LazySection>
            </div>
            <LazySection>
              <Suspense
                fallback={
                  <div className="h-64 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl" />
                }
              >
                <DashboardStats
                  stats={landingData?.stats ?? stats}
                  initialLanguages={landingData?.languages}
                  initialTrending={landingData?.trending}
                />
              </Suspense>
            </LazySection>
            <LazySection>
              <InstallGuide />
            </LazySection>
            <div id="workflows" className="scroll-mt-44">
              <LazySection>
                <ScenarioWorkflows />
              </LazySection>
            </div>
            <div id="platforms">
              <LazySection>
                <PlatformRecommendations />
              </LazySection>
            </div>
            <LazySection>
              <FAQSection />
            </LazySection>
            <div id="submit-skill">
              <LazySection minHeight="100px">
                <SubmitSkill />
              </LazySection>
            </div>
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
                  onSortOrderChange={(sort_order) =>
                    updateParams({ sort_order })
                  }
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
                <span className="text-xs text-gray-400 dark:text-gray-500">
                  {t("explore.size")}
                </span>
                {["micro", "small", "medium", "large"].map((s) => (
                  <button
                    key={s}
                    onClick={() =>
                      updateParams({
                        size_category:
                          params.size_category === s ? undefined : s,
                      })
                    }
                    className={`px-2.5 py-1 text-xs rounded-full border transition-colors cursor-pointer ${
                      params.size_category === s
                        ? "bg-blue-600 text-white border-blue-600"
                        : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:border-blue-300"
                    }`}
                  >
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </button>
                ))}
                <span className="text-xs text-gray-300 dark:text-gray-600 mx-1">
                  |
                </span>
                <span className="text-xs text-gray-400 dark:text-gray-500">
                  {t("explore.platform")}
                </span>
                {["python", "node", "go", "docker", "claude", "mcp"].map(
                  (p) => (
                    <button
                      key={p}
                      onClick={() =>
                        updateParams({
                          platform: params.platform === p ? undefined : p,
                        })
                      }
                      className={`px-2.5 py-1 text-xs rounded-full border transition-colors cursor-pointer ${
                        params.platform === p
                          ? "bg-blue-600 text-white border-blue-600"
                          : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:border-blue-300"
                      }`}
                    >
                      {p.charAt(0).toUpperCase() + p.slice(1)}
                    </button>
                  ),
                )}
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
                {/* Subcategory chips — show when category is selected */}
                {params.category && (
                  <SubcategoryChips
                    category={params.category}
                    selected={subcategory}
                    onSelect={setSubcategory}
                  />
                )}

                {/* Error */}
                {error && (
                  <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm">
                    {error}
                  </div>
                )}

                {/* Loading Skeleton */}
                {loading && <SkeletonCards count={6} />}

                {/* Results */}
                {!loading &&
                  data &&
                  data.items.length > 0 &&
                  (() => {
                    const filteredItems = subcategory
                      ? data.items.filter(
                          (s) => inferSubcategory(s) === subcategory,
                        )
                      : data.items;
                    return (
                      <>
                        <div className="text-sm text-gray-400 dark:text-gray-500 mb-3">
                          {t("explore.showing")}{" "}
                          {subcategory ? `${filteredItems.length} / ` : ""}
                          {(data.page - 1) * data.page_size + 1}-
                          {Math.min(data.page * data.page_size, data.total)}{" "}
                          {t("explore.of")} {data.total.toLocaleString()}{" "}
                          {t("explore.skills")}
                        </div>
                        {view === "card" ? (
                          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 stagger-children">
                            {filteredItems.map((skill) => (
                              <SkillCard
                                key={skill.id}
                                skill={skill}
                                onSelect={handleOpenRepo}
                                onShowDetail={handleShowDetail}
                              />
                            ))}
                          </div>
                        ) : (
                          <SkillTable
                            skills={filteredItems}
                            onSelect={handleOpenRepo}
                            onShowDetail={handleShowDetail}
                          />
                        )}
                        <Pagination
                          page={data.page}
                          totalPages={data.total_pages}
                          onPageChange={setPage}
                        />
                      </>
                    );
                  })()}

                {/* Empty State */}
                {!loading && data && data.items.length === 0 && (
                  <div className="text-center py-16">
                    <svg
                      className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-3"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="1.5"
                        d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
                      />
                    </svg>
                    <h3 className="text-lg font-medium text-gray-700 dark:text-gray-200">
                      {t("explore.noResults")}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      {t("explore.noResultsHint")}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
        {/* Commercialization CTA banner — visible just above the footer */}
        <section className="mt-10 mb-6">
          <div className="grid md:grid-cols-2 gap-4">
            <a
              href="/verified-creator/"
              className="group bg-gradient-to-br from-emerald-50 to-white dark:from-emerald-950/30 dark:to-gray-900 border border-emerald-200 dark:border-emerald-900 rounded-xl p-5 hover:shadow-md transition-all"
            >
              <div className="flex items-start gap-3">
                <div className="flex-none w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900/50 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <path d="M12 2L4 6v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V6l-8-4zm-1.4 14.6L6 12l1.4-1.4 3.2 3.2 6.2-6.2L18.2 9l-7.6 7.6z" />
                  </svg>
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-1 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition">
                    Skill 作者？加入 Verified Creator →
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                    认证徽章 + Trending 加权 + 作者数据面板 +
                    咨询撮合。首批邀请制 ¥699/年。
                  </p>
                </div>
              </div>
            </a>
            <a
              href="/business/"
              className="group bg-gradient-to-br from-blue-50 to-white dark:from-blue-950/30 dark:to-gray-900 border border-blue-200 dark:border-blue-900 rounded-xl p-5 hover:shadow-md transition-all"
            >
              <div className="flex items-start gap-3">
                <div className="flex-none w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 flex items-center justify-center text-lg">
                  🏢
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-1 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition">
                    企业用户？看看 For Business →
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                    安全审计 + SBOM + 合规标签 + 私有镜像。给法务和技术决策者的
                    Skill 目录。
                  </p>
                </div>
              </div>
            </a>
          </div>
        </section>
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
