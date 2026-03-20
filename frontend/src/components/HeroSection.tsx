import { useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
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
  const { t } = useI18n();
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
        .then((items) => { setResults(items); setSearching(false); })
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
        navigate(`/skill/${results[activeIdx].repo_full_name}`);
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
  const mcpCount = stats?.categories.find((c) => c.name === "mcp-server")?.count ?? 6500;
  const claudeCount = stats?.categories.find((c) => c.name === "claude-skill")?.count ?? 2200;
  const agentCount = stats?.categories.find((c) => c.name === "agent-tool")?.count ?? 5000;

  return (
    <section className="hero-gradient -mx-4 px-4 pt-10 pb-8 sm:pt-14 sm:pb-10 mb-6">
      <div className="max-w-3xl mx-auto text-center relative z-10">
        {/* Main headline */}
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white tracking-tight mb-3">
          {t("hero.title").replace("{count}", countDisplay)}
        </h2>
        <p className="text-base sm:text-lg text-gray-500 dark:text-gray-400 mb-8 max-w-2xl mx-auto">
          {t("hero.subtitle")}
        </p>

        {/* Search bar */}
        <div className="relative max-w-2xl mx-auto mb-5" ref={containerRef}>
          <svg
            className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500 z-10"
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => handleChange(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => { if (query.trim() || results.length > 0) setShowDropdown(true); }}
            placeholder={t("hero.searchPlaceholder")}
            aria-label="Search skills"
            className="w-full pl-12 pr-12 py-4 border border-gray-200 dark:border-gray-700 rounded-2xl bg-white dark:bg-gray-800/80 text-gray-900 dark:text-gray-100 text-base shadow-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow hover:shadow-xl backdrop-blur-sm"
          />
          {query && (
            <button
              onClick={() => { setQuery(""); setResults([]); setShowDropdown(false); }}
              className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 cursor-pointer z-10"
              aria-label="Clear"
            >
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
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
                      onClick={() => { navigate(`/skill/${skill.repo_full_name}`); setShowDropdown(false); }}
                      onMouseEnter={() => setActiveIdx(i)}
                      className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-colors ${i === activeIdx ? "bg-indigo-50 dark:bg-indigo-900/30" : "hover:bg-gray-50 dark:hover:bg-gray-700"}`}
                    >
                      <img src={skill.author_avatar_url} alt="" width={32} height={32} className="w-8 h-8 rounded-full shrink-0" />
                      <div className="flex-1 min-w-0 text-left">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">{skill.repo_name}</span>
                          <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">{skill.author_name}</span>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{skill.description}</p>
                      </div>
                      <span className="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-0.5 shrink-0">
                        <svg className="w-3.5 h-3.5 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                        </svg>
                        {skill.stars >= 1000 ? `${(skill.stars / 1000).toFixed(1)}k` : skill.stars.toLocaleString()}
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
          <span className="text-xs text-gray-400 dark:text-gray-500 font-medium">{t("hero.trending")}:</span>
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

        {/* Key stats */}
        <div className="flex items-center justify-center gap-6 sm:gap-10">
          <div className="text-center">
            <div className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">{totalSkills.toLocaleString()}+</div>
            <div className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">Skills</div>
          </div>
          <div className="w-px h-8 bg-gray-300 dark:bg-gray-700" />
          <div className="text-center">
            <div className="text-xl sm:text-2xl font-bold text-indigo-600 dark:text-indigo-400">{mcpCount.toLocaleString()}+</div>
            <div className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">MCP Servers</div>
          </div>
          <div className="w-px h-8 bg-gray-300 dark:bg-gray-700" />
          <div className="text-center">
            <div className="text-xl sm:text-2xl font-bold text-blue-600 dark:text-blue-400">{claudeCount.toLocaleString()}+</div>
            <div className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">Claude Skills</div>
          </div>
          <div className="w-px h-8 bg-gray-300 dark:bg-gray-700 hidden sm:block" />
          <div className="text-center hidden sm:block">
            <div className="text-xl sm:text-2xl font-bold text-emerald-600 dark:text-emerald-400">{agentCount.toLocaleString()}+</div>
            <div className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">Agent Tools</div>
          </div>
        </div>
      </div>
    </section>
  );
}
