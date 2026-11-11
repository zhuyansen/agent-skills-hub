import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";
import { useQuickSearch } from "../hooks/useQuickSearch";
import { trackEvent } from "../lib/analytics";
import { readCatalogCounts } from "../lib/catalogCounts";
import type { Skill, Stats } from "../types/skill";

interface Guide {
  slug: string;
  zh: string;
  en: string;
  /** The card picture: something a tool made in the guide's test (public/home-guides/<img>.webp). */
  img?: string;
}

/** The guides at the top of the hero: the three with a test of our own that search sends the
 *  most people to (GSC, 28 days to 2026-11-08: 1,642 / 839 / 84 clicks). Each card shows what
 *  the test produced: two of the image test's mascots, the first slide of the PPT test's top
 *  pick, and a frame of the video test's top pick. */
const TOP_GUIDES: readonly Guide[] = [
  { slug: "image-generation", img: "image", zh: "AI 生图", en: "AI Image Generation" },
  { slug: "ppt-presentation", img: "ppt", zh: "PPT 生成", en: "PPT & Slides" },
  { slug: "claude-video-skills", img: "video", zh: "Claude 视频", en: "Claude Video" },
];

/** The card pictures are 480x240 files; the attributes reserve the 2:1 box before they load. */
const CARD_IMG_WIDTH = 480;
const CARD_IMG_HEIGHT = 240;

/** Under the search box: the next six guides by the same clicks (54 down to 17). These were
 *  search keywords (mcp-server, langchain, …) that opened a result list, not a guide. */
const MORE_GUIDES: readonly Guide[] = [
  { slug: "telegram-bot", zh: "Telegram 机器人", en: "Telegram Bots" },
  { slug: "code-review", zh: "代码审查", en: "Code Review" },
  { slug: "anti-slop", zh: "去 AI 味", en: "Anti-Slop" },
  { slug: "skill-management-tools", zh: "Skill 管理", en: "Skill Managers" },
  { slug: "ai-design", zh: "AI 设计", en: "AI Design" },
  { slug: "codex-skills", zh: "Codex 技能", en: "Codex Skills" },
];

const guideHref = (slug: string, zh: boolean) => `/best/${slug}/${zh ? "zh/" : ""}`;

/** How many tools the guide's own test covers, counted at build time (vite.config.ts). */
function testedLabel(slug: string, zh: boolean): string | null {
  const n = __GUIDE_TESTED__[slug];
  if (!n) return null;
  return zh ? `实测 ${n} 个` : `${n} tested`;
}

/** Which hero guide links get clicked, to judge the two rows and pick who stays (GA4). */
const trackGuideClick = (slug: string, row: "top" | "more") =>
  trackEvent("hero_guide_click", { guide: slug, row });

/** The real counts as of the last build, shown until the stats arrive: with as many digits
 *  as the live ones, the first paint keeps its line breaks when they land. A 17,000
 *  stand-in put the title on one more line on a 412px phone once "258,000+" came, moving
 *  the page below it 38px (CLS 0.049). */
const BUILD_COUNTS = readCatalogCounts();

/** Stand-ins for a page without the build's counts (the dev server, or a build whose
 *  counting step failed), near the live ones on 11-02 (258,645 / 95,449 / 34,347 / 67,116). */
const FALLBACK_COUNTS = {
  total: 258_000,
  mcp: 95_000,
  claude: 34_000,
  agent: 67_000,
} as const;

/** A category's count: live once the stats arrive, else as of the last build, else the stand-in. */
function categoryCount(stats: Stats | null, name: string, fallback: number): number {
  return stats?.categories.find((c) => c.name === name)?.count ?? BUILD_COUNTS?.categories[name] ?? fallback;
}

/** One of the three guide cards: a picture from the guide's test, its name, how many it tested. */
function GuideCard({ guide, zh }: { guide: Guide; zh: boolean }) {
  const title = zh ? guide.zh : guide.en;
  return (
    <a
      href={guideHref(guide.slug, zh)}
      onClick={() => trackGuideClick(guide.slug, "top")}
      className="block overflow-hidden rounded-xl text-left bg-[var(--bg-card)]/70 backdrop-blur border border-[var(--border)] hover:border-indigo-400/60 transition-colors"
    >
      <img
        src={`/home-guides/${guide.img}.webp`}
        alt={zh ? `「${title}」实测里做出来的东西` : `Made in our ${title} test`}
        width={CARD_IMG_WIDTH}
        height={CARD_IMG_HEIGHT}
        decoding="async"
        className="block w-full h-auto aspect-[2/1] object-cover"
      />
      <span className="block px-2 py-1.5 sm:px-3 sm:py-2">
        <span className="block text-[13px] sm:text-sm font-medium leading-tight text-[var(--text-1)]">{title}</span>
        <span className="block mt-0.5 text-[11px] sm:text-xs text-[var(--text-3)]">{testedLabel(guide.slug, zh)}</span>
      </span>
    </a>
  );
}

interface Props {
  stats: Stats | null;
  onSearch: (query: string) => void;
}

export function HeroSection({ stats, onSearch }: Props) {
  const { t, lang } = useI18n();
  const isZh = lang === "zh";
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const search = useQuickSearch();
  const { view, items: results, active: activeIdx, containerRef } = search;
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (v: string) => {
    setQuery(v);
    search.type(v);
  };

  const openSkill = (skill: Skill) => {
    navigate(`/skill/${skill.repo_full_name}/`);
    search.close();
  };

  const handleEnter = () => {
    if (search.activeItem) return openSkill(search.activeItem);
    if (!query.trim()) return;
    onSearch(query);
    search.close();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") return search.close();
    if (e.key !== "Enter" && e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    e.preventDefault();
    if (e.key === "Enter") handleEnter();
    else search.move(e.key === "ArrowDown" ? 1 : -1);
  };

  const totalSkills = stats?.total_skills ?? BUILD_COUNTS?.total ?? FALLBACK_COUNTS.total;
  const countDisplay = `${Math.floor(totalSkills / 1000).toLocaleString()},000+`;

  const mcpCount = categoryCount(stats, "mcp-server", FALLBACK_COUNTS.mcp);
  const claudeCount = categoryCount(stats, "claude-skill", FALLBACK_COUNTS.claude);
  const agentCount = categoryCount(stats, "agent-tool", FALLBACK_COUNTS.agent);

  return (
    <section className="hero-gradient full-bleed px-4 pt-8 pb-12 sm:pt-20 sm:pb-16 mb-8 relative z-20">
      <div className="max-w-3xl mx-auto text-center relative z-10">
        {/* The three guides with our own test results, where the hero used to open with empty
            padding and an enterprise banner (Enterprise stays in the header and below the search). */}
        <nav aria-label={isZh ? "热门场景" : "Popular guides"} className="mb-8">
          <div className="grid grid-cols-3 gap-2 sm:gap-3">
            {TOP_GUIDES.map((g) => (
              <GuideCard key={g.slug} guide={g} zh={isZh} />
            ))}
          </div>
          <a
            href={isZh ? "/best/zh/" : "/best/"}
            onClick={() => trackGuideClick("all", "top")}
            className="inline-block mt-3 text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            {isZh ? "全部场景 →" : "All guides →"}
          </a>
        </nav>

        {/* Main headline */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-gray-900 dark:text-white tracking-[-0.03em] leading-[1.05] mb-5">
          {t("hero.title").replace("{count}", countDisplay)}
        </h1>
        <p className="text-base sm:text-lg text-[var(--text-2)] mb-9 max-w-xl mx-auto leading-relaxed">
          {t("hero.subtitle")}
        </p>

        {/* Search bar */}
        <div className="relative max-w-2xl mx-auto mb-5" ref={containerRef}>
          <svg
            className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500 z-10"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => handleChange(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={search.open}
            placeholder={t("hero.searchPlaceholder")}
            aria-label="Search skills"
            className="w-full pl-12 pr-12 py-4 border border-gray-200 dark:border-gray-700 rounded-2xl bg-white dark:bg-gray-800/80 text-gray-900 dark:text-gray-100 text-base shadow-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow hover:shadow-xl backdrop-blur-sm"
          />
          {query && (
            <button
              onClick={() => {
                setQuery("");
                search.clear();
              }}
              className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 cursor-pointer z-10"
              aria-label="Clear"
            >
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}

          {/* Dropdown */}
          {view !== "closed" && view !== "empty" && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl overflow-hidden z-50">
              {view === "searching" && (
                <div className="px-4 py-4 text-center">
                  <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
                </div>
              )}
              {view === "results" && (
                <div className="max-h-72 overflow-y-auto">
                  {results.map((skill, i) => (
                    <div
                      key={skill.id}
                      onClick={() => openSkill(skill)}
                      onMouseEnter={() => search.hover(i)}
                      className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-colors ${i === activeIdx ? "bg-indigo-50 dark:bg-indigo-900/30" : "hover:bg-gray-50 dark:hover:bg-gray-700"}`}
                    >
                      <img
                        src={skill.author_avatar_url}
                        alt={skill.author_name}
                        width={32}
                        height={32}
                        className="w-8 h-8 rounded-full shrink-0"
                      />
                      <div className="flex-1 min-w-0 text-left">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
                            {skill.repo_name}
                          </span>
                          <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">
                            {skill.author_name}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                          {skill.description}
                        </p>
                      </div>
                      <span className="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-0.5 shrink-0">
                        <svg
                          className="w-3.5 h-3.5 text-amber-400"
                          fill="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                        </svg>
                        {skill.stars >= 1000
                          ? `${(skill.stars / 1000).toFixed(1)}k`
                          : skill.stars.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              {view === "none" && (
                <div className="px-4 py-4 text-center text-sm text-gray-500">
                  {t("explore.noResults")}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Audit funnel entry — parallel to search: "find a skill" vs "vet a repo" */}
        <div className="-mt-1 mb-6 text-sm">
          <Link
            to="/analyzer/"
            className="font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            {isZh
              ? "🔍 或粘贴任意 GitHub 仓库 → 免费安全审计"
              : "🔍 or paste any GitHub repo → free security audit"}
          </Link>
        </div>

        {/* More guides */}
        <div className="flex flex-wrap items-center justify-center gap-2 mb-8">
          <span className="text-xs text-gray-400 dark:text-gray-500 font-medium">
            {isZh ? "更多场景" : "More guides"}:
          </span>
          {MORE_GUIDES.map((g) => (
            <a
              key={g.slug}
              href={guideHref(g.slug, isZh)}
              onClick={() => trackGuideClick(g.slug, "more")}
              className="px-3 py-1 text-xs font-medium bg-white/80 dark:bg-gray-800/80 text-gray-500 dark:text-gray-300 rounded-full border border-gray-200/80 dark:border-gray-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 hover:text-indigo-600 dark:hover:text-indigo-400 hover:border-indigo-300 dark:hover:border-indigo-700 transition-all cursor-pointer"
            >
              {isZh ? g.zh : g.en}
            </a>
          ))}
        </div>

        {/* Key stats — one disciplined treatment, no rainbow.
            Clickable: Clarity heatmap (2026-07-04) showed users dead-clicking
            these numbers expecting them to filter — give them what they want. */}
        <div className="flex items-center justify-center gap-6 sm:gap-10">
          {[
            {
              value: totalSkills.toLocaleString(),
              label: "Skills",
              to: "/?tab=explore",
            },
            {
              value: mcpCount.toLocaleString(),
              label: "MCP Servers",
              to: "/?tab=explore&category=mcp-server",
            },
            {
              value: claudeCount.toLocaleString(),
              label: "Claude Skills",
              to: "/?tab=explore&category=claude-skill",
            },
            {
              value: agentCount.toLocaleString(),
              label: "Agent Tools",
              to: "/?tab=explore&category=agent-tool",
              hideMobile: true,
            },
          ].map((s, i) => (
            <div key={s.label} className="flex items-center gap-6 sm:gap-10">
              {i > 0 && (
                <div
                  className={`w-px h-8 bg-[var(--border)] ${s.hideMobile ? "hidden sm:block" : ""}`}
                />
              )}
              <Link
                to={s.to}
                className={`text-center group/stat cursor-pointer ${s.hideMobile ? "hidden sm:block" : ""}`}
              >
                <div className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white tabular-nums group-hover/stat:text-indigo-600 dark:group-hover/stat:text-indigo-400 transition-colors">
                  {s.value}
                  <span className="text-[var(--text-3)]">+</span>
                </div>
                <div className="text-[11px] uppercase tracking-wider text-[var(--text-3)] mt-1 group-hover/stat:text-[var(--text-2)] transition-colors">
                  {s.label}
                </div>
              </Link>
            </div>
          ))}
        </div>

        {/* B-path Trust Signals — under the catalog stats, above the fold */}
        <div className="mt-12 pt-10 border-t border-[var(--border)]">
          <div className="eyebrow mb-5">
            {isZh
              ? "AI Agent 与 MCP 部署的信任层"
              : "Trust Layer for AI Agent & MCP Deployment"}
          </div>
          {/* Clickable (Clarity dead-click fix): each stat routes to its
              evidence — the report, the freshness feed, the enterprise pitch. */}
          <div className="grid grid-cols-3 gap-4 sm:gap-8 max-w-xl mx-auto">
            {[
              {
                value: "26.1%",
                href: "/blog/securing-117k-ai-skills/",
                hard: true, // static blog page — bypass React Router
                label: isZh
                  ? "的 agent skill 含安全漏洞"
                  : "of agent skills contain security vulnerabilities",
              },
              {
                value: "8h",
                href: "/?tab=overview#recent",
                hard: false,
                label: isZh
                  ? "全量 skill 目录刷新一次"
                  : "refresh on the entire skill catalog",
              },
              {
                value: "$10K+",
                href: "/enterprise/",
                hard: false,
                label: isZh
                  ? "部署前审计每次事故省下"
                  : "saved per incident with pre-deploy audit",
              },
            ].map((s) => {
              const cls =
                "block group/trust cursor-pointer rounded-lg -m-2 p-2 hover:bg-[var(--bg-elev)] transition-colors";
              const inner = (
                <>
                  <div className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white tabular-nums group-hover/trust:text-indigo-600 dark:group-hover/trust:text-indigo-400 transition-colors">
                    {s.value}
                  </div>
                  <div className="text-[11px] sm:text-xs text-[var(--text-3)] mt-1.5 leading-snug">
                    {s.label}
                  </div>
                </>
              );
              return s.hard ? (
                <a key={s.value} href={s.href} className={cls}>
                  {inner}
                </a>
              ) : (
                <Link key={s.value} to={s.href} className={cls}>
                  {inner}
                </Link>
              );
            })}
          </div>
          {/* Source attribution — honesty: the vuln stat is citable research */}
          <div className="mt-3 text-[10px] text-[var(--text-3)]">
            {isZh ? "漏洞率来自 " : "Vulnerability rate from "}
            <a
              href="https://arxiv.org/abs/2601.10338"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-[var(--text-2)] transition-colors"
            >
              Liu et al., 2026 (n=31,132 skills)
            </a>
          </div>

          {/* Compliance-framework band — the procurement-language wedge */}
          <div className="mt-7 flex flex-wrap items-center justify-center gap-2">
            <span className="text-[11px] text-[var(--text-3)]">
              {isZh ? "对齐合规框架" : "Audited against"}
            </span>
            {["SOC 2", "ISO/IEC 42001", "EU AI Act", "GDPR"].map((f) => (
              <a
                key={f}
                href="/enterprise/"
                className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-[var(--bg-elev)] text-[var(--text-2)] border border-[var(--border)] hover:border-indigo-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
              >
                {f}
              </a>
            ))}
          </div>
          <div className="mt-7 flex flex-wrap justify-center items-center gap-3 text-sm">
            <a
              href="/enterprise/"
              className="inline-flex items-center px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition-colors shadow-sm"
            >
              {isZh ? "企业审计 →" : "Enterprise audit →"}
            </a>
            <a
              href="#trending"
              className="inline-flex items-center px-5 py-2.5 text-[var(--text-2)] hover:text-[var(--text-1)] font-medium border border-[var(--border)] hover:border-[var(--border-strong)] rounded-lg transition-colors"
            >
              {isZh ? "浏览免费目录" : "Browse free catalog"}
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
