import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchQuickSearch } from "../api/client";
import { useI18n } from "../i18n/I18nContext";
import { useRecentSearches } from "../hooks/useRecentSearches";
import type { Skill } from "../types/skill";

interface Props {
  value: string;
  onChange: (value: string) => void;
}

const HOT_KEYWORDS = ["mcp-server", "claude", "agent", "codex", "python", "typescript"];

export function SearchBar({ value, onChange }: Props) {
  const { t } = useI18n();
  const navigate = useNavigate();
  const { searches: recentSearches, addSearch, clearSearches } = useRecentSearches();
  const [local, setLocal] = useState(value);
  const [results, setResults] = useState<Skill[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const [searching, setSearching] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const searchTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setLocal(value);
  }, [value]);

  // Cleanup timers on unmount
  useEffect(() => () => {
    clearTimeout(timer.current);
    clearTimeout(searchTimer.current);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const doQuickSearch = useCallback((query: string) => {
    clearTimeout(searchTimer.current);
    if (!query.trim()) {
      setResults([]);
      setSearching(false);
      return;
    }
    setSearching(true);
    searchTimer.current = setTimeout(() => {
      fetchQuickSearch(query, 6)
        .then((items) => {
          setResults(items);
          setSearching(false);
        })
        .catch(() => {
          setSearching(false);
        });
    }, 200);
  }, []);

  const handleChange = (v: string) => {
    setLocal(v);
    setActiveIdx(-1);
    setShowDropdown(true);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => onChange(v), 400);
    doQuickSearch(v);
  };

  const handleClear = () => {
    setLocal("");
    setResults([]);
    setShowDropdown(false);
    clearTimeout(timer.current);
    onChange("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown || results.length === 0) {
      if (e.key === "Enter") {
        setShowDropdown(false);
        // Record search
        if (local.trim()) addSearch(local.trim());
      }
      return;
    }
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setActiveIdx((prev) => Math.min(prev + 1, results.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setActiveIdx((prev) => Math.max(prev - 1, -1));
        break;
      case "Enter":
        e.preventDefault();
        if (activeIdx >= 0 && activeIdx < results.length) {
          navigate(`/skill/${results[activeIdx].repo_full_name}`);
          setShowDropdown(false);
          addSearch(results[activeIdx].repo_name);
        } else {
          setShowDropdown(false);
          if (local.trim()) addSearch(local.trim());
        }
        break;
      case "Escape":
        setShowDropdown(false);
        break;
    }
  };

  const handleFocus = () => {
    setShowDropdown(true);
  };

  const handleHotKeyword = (keyword: string) => {
    setLocal(keyword);
    onChange(keyword);
    doQuickSearch(keyword);
    setShowDropdown(true);
    addSearch(keyword);
    inputRef.current?.focus();
  };

  return (
    <div className="relative" ref={containerRef}>
      <svg
        className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500 z-10"
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
        value={local}
        onChange={(e) => handleChange(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={handleFocus}
        placeholder={t("explore.search")}
        aria-label="Search skills"
        className="w-full pl-10 pr-9 py-2.5 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
      {local && (
        <button
          onClick={handleClear}
          className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 cursor-pointer z-10"
          aria-label="Clear search"
        >
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}

      {/* Dropdown */}
      {showDropdown && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden z-50">
          {/* Recent searches when empty */}
          {!local.trim() && recentSearches.length > 0 && (
            <div className="px-3 py-2 border-b border-gray-100 dark:border-gray-700">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-gray-400 dark:text-gray-500 uppercase tracking-wide">{t("search.recent")}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    clearSearches();
                  }}
                  className="text-[10px] text-gray-400 dark:text-gray-500 hover:text-red-500 transition-colors cursor-pointer"
                >
                  {t("search.clearRecent")}
                </button>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {recentSearches.map((query) => (
                  <button
                    key={query}
                    onClick={() => handleHotKeyword(query)}
                    className="px-2 py-0.5 text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-md hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors cursor-pointer flex items-center gap-1"
                  >
                    <svg className="w-2.5 h-2.5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {query}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Hot keywords when empty */}
          {!local.trim() && (
            <div className="px-3 py-2.5 border-b border-gray-100 dark:border-gray-700">
              <span className="text-[10px] text-gray-400 dark:text-gray-500 uppercase tracking-wide">{t("search.hotKeywords")}</span>
              <div className="flex flex-wrap gap-1.5 mt-1.5">
                {HOT_KEYWORDS.map((kw) => (
                  <button
                    key={kw}
                    onClick={() => handleHotKeyword(kw)}
                    className="px-2 py-0.5 text-xs bg-gray-50 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-md hover:bg-blue-50 dark:hover:bg-blue-900/30 hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer"
                  >
                    {kw}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Loading */}
          {searching && local.trim() && (
            <div className="px-3 py-4 text-center">
              <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
            </div>
          )}

          {/* Results */}
          {!searching && results.length > 0 && (
            <div className="max-h-72 overflow-y-auto">
              {results.map((skill, i) => (
                <div
                  key={skill.id}
                  onClick={() => {
                    navigate(`/skill/${skill.repo_full_name}`);
                    setShowDropdown(false);
                    addSearch(skill.repo_name);
                  }}
                  onMouseEnter={() => setActiveIdx(i)}
                  className={`flex items-center gap-3 px-3 py-2.5 cursor-pointer transition-colors ${
                    i === activeIdx ? "bg-blue-50 dark:bg-blue-900/30" : "hover:bg-gray-50 dark:hover:bg-gray-700"
                  }`}
                >
                  <img src={skill.author_avatar_url} alt="" width={28} height={28} className="w-7 h-7 rounded-full shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                        {skill.repo_name}
                      </span>
                      <span className="text-[10px] text-gray-400 dark:text-gray-500 shrink-0">
                        {skill.author_name}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{skill.description}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-0.5">
                      <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                      </svg>
                      {skill.stars.toLocaleString()}
                    </span>
                    <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                      skill.score >= 70 ? "bg-green-50 dark:bg-green-900/30 text-green-600" :
                      skill.score >= 40 ? "bg-blue-50 dark:bg-blue-900/30 text-blue-600" :
                      "bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400"
                    }`}>
                      {skill.score.toFixed(0)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* No results */}
          {!searching && local.trim() && results.length === 0 && (
            <div className="px-3 py-4 text-center text-sm text-gray-400 dark:text-gray-500">
              {t("explore.noResults")}
            </div>
          )}

          {/* Keyboard hint */}
          {results.length > 0 && (
            <div className="px-3 py-1.5 border-t border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 flex items-center gap-3 text-[10px] text-gray-400 dark:text-gray-500">
              <span className="flex items-center gap-1">
                <kbd className="px-1 py-0.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-[9px]">↑↓</kbd>
                {t("search.navigate")}
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1 py-0.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-[9px]">Enter</kbd>
                {t("search.select")}
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1 py-0.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-[9px]">Esc</kbd>
                {t("search.close")}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
