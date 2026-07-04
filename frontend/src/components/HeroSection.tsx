import { useCallback, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { fetchQuickSearch } from "../api/client";
import { useI18n } from "../i18n/I18nContext";
import type { Skill, Stats } from "../types/skill";

const TRENDING_TAGS = [
  "mcp-server",
  "claude-skill",
  "langchain",
  "browser-use",
  "coding-agent",
  "openai",
];

interface Props {
  stats: Stats | null;
  onSearch: (query: string) => void;
}

export function HeroSection({ stats, onSearch }: Props) {
  const { t, lang } = useI18n();
  const isZh = lang === "zh";
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Skill[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const [searching, setSearching] = useState(false);
  const searchTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const doSearch = useCallback((q: string) => {
    clearTimeout(searchTimer.current);
    if (!q.trim()) {
      setResults([]);
      setSearching(false);
      return;
    }
    setSearching(true);
    searchTimer.current = setTimeout(() => {
      fetchQuickSearch(q, 6)
        .then((items) => {
          setResults(items);
          setSearching(false);
        })
        .catch(() => setSearching(false));
    }, 200);
  }, []);

  const handleChange = (v: string) => {
    setQuery(v);
    setActiveIdx(-1);
    setShowDropdown(true);
    doSearch(v);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (activeIdx >= 0 && activeIdx < results.length) {
        navigate(`/skill/${results[activeIdx].repo_full_name}/`);
        setShowDropdown(false);
      } else if (query.trim()) {
        onSearch(query);
        setShowDropdown(false);
      }
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((p) => Math.min(p + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((p) => Math.max(p - 1, -1));
    } else if (e.key === "Escape") {
      setShowDropdown(false);
    }
  };

  const handleTagClick = (tag: string) => {
    setQuery(tag);
    onSearch(tag);
  };

  const totalSkills = stats?.total_skills ?? 17000;
  const countDisplay = `${Math.floor(totalSkills / 1000).toLocaleString()},000+`;

  // Extract category counts
  const mcpCount =
    stats?.categories.find((c) => c.name === "mcp-server")?.count ?? 6500;
  const claudeCount =
    stats?.categories.find((c) => c.name === "claude-skill")?.count ?? 2200;
  const agentCount =
    stats?.categories.find((c) => c.name === "agent-tool")?.count ?? 5000;

  return (
    <section className="hero-gradient full-bleed px-4 pt-16 pb-12 sm:pt-24 sm:pb-16 mb-8 relative z-20">
      <div className="max-w-3xl mx-auto text-center relative z-10">
        {/* B-path: thin enterprise banner — high signal, doesn't touch H1/SEO */}
        <a
          href="/enterprise/"
          className="group inline-flex items-center gap-2 px-3.5 py-1.5 mb-8 rounded-full text-xs font-medium bg-[var(--bg-card)]/70 backdrop-blur text-[var(--text-2)] border border-[var(--border)] hover:border-indigo-400/60 transition-colors"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
          <span className="font-semibold text-indigo-600 dark:text-indigo-400">
            New
          </span>
          Enterprise audit packages now available
          <span className="text-[var(--text-3)] transition-transform group-hover:translate-x-0.5">
            →
          </span>
        </a>

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
            onFocus={() => {
              if (query.trim() || results.length > 0) setShowDropdown(true);
            }}
            placeholder={t("hero.searchPlaceholder")}
            aria-label="Search skills"
            className="w-full pl-12 pr-12 py-4 border border-gray-200 dark:border-gray-700 rounded-2xl bg-white dark:bg-gray-800/80 text-gray-900 dark:text-gray-100 text-base shadow-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow hover:shadow-xl backdrop-blur-sm"
          />
          {query && (
            <button
              onClick={() => {
                setQuery("");
                setResults([]);
                setShowDropdown(false);
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
          {showDropdown && (query.trim() || results.length > 0) && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl overflow-hidden z-50">
              {searching && (
                <div className="px-4 py-4 text-center">
                  <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
                </div>
              )}
              {!searching && results.length > 0 && (
                <div className="max-h-72 overflow-y-auto">
                  {results.map((skill, i) => (
                    <div
                      key={skill.id}
                      onClick={() => {
                        navigate(`/skill/${skill.repo_full_name}/`);
                        setShowDropdown(false);
                      }}
                      onMouseEnter={() => setActiveIdx(i)}
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
              {!searching && query.trim() && results.length === 0 && (
                <div className="px-4 py-4 text-center text-sm text-gray-500">
                  {t("explore.noResults")}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Trending tags */}
        <div className="flex flex-wrap items-center justify-center gap-2 mb-8">
          <span className="text-xs text-gray-400 dark:text-gray-500 font-medium">
            {t("hero.trending")}:
          </span>
          {TRENDING_TAGS.map((tag) => (
            <button
              key={tag}
              onClick={() => handleTagClick(tag)}
              className="px-3 py-1 text-xs font-medium bg-white/80 dark:bg-gray-800/80 text-gray-500 dark:text-gray-300 rounded-full border border-gray-200/80 dark:border-gray-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 hover:text-indigo-600 dark:hover:text-indigo-400 hover:border-indigo-300 dark:hover:border-indigo-700 transition-all cursor-pointer"
            >
              {tag}
            </button>
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
