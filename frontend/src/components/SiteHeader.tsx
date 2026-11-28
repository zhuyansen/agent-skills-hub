import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { BrowseMenu } from "./BrowseMenu";
import { LanguageToggle } from "./LanguageToggle";
import { ThemeToggle } from "./ThemeToggle";
import { useI18n } from "../i18n/I18nContext";
import { HeaderMoreMenu } from "./HeaderMoreMenu";
import { subscribe } from "../api/client";

interface Props {
  /** Show tab navigation (only on Home page) */
  showTabs?: boolean;
  tab?: "overview" | "explore";
  onTabChange?: (tab: "overview" | "explore") => void;
  /** Breadcrumb items for detail pages */
  breadcrumb?: { label: string }[];
}

export function SiteHeader({ showTabs, tab, onTabChange, breadcrumb }: Props) {
  const { t, lang } = useI18n();
  const [showNewsletterPopup, setShowNewsletterPopup] = useState(false);
  const [nlEmail, setNlEmail] = useState("");
  const [nlStatus, setNlStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [nlMessage, setNlMessage] = useState("");
  const nlRef = useRef<HTMLDivElement>(null);
  const subNavRef = useRef<HTMLDivElement>(null);

  // Close newsletter popup on Escape
  useEffect(() => {
    if (!showNewsletterPopup) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setShowNewsletterPopup(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [showNewsletterPopup]);

  // Auto-close after success
  useEffect(() => {
    if (nlStatus === "success") {
      const timer = setTimeout(() => {
        setShowNewsletterPopup(false);
        // Reset after close animation
        setTimeout(() => {
          setNlStatus("idle");
          setNlEmail("");
        }, 300);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [nlStatus]);

  const handleNlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nlEmail.trim() || nlStatus === "loading") return;
    setNlStatus("loading");
    setNlMessage("");
    try {
      const res = await subscribe(nlEmail.trim());
      if (res.status === "already" || res.status === "success") {
        setNlStatus("success");
        setNlMessage(res.message || t("newsletter.success"));
        setNlEmail("");
      } else {
        throw new Error(res.message);
      }
    } catch (err: unknown) {
      setNlStatus("error");
      setNlMessage(err instanceof Error ? err.message : t("newsletter.error"));
    }
  };

  return (
    <header className="bg-white/95 dark:bg-[#0b1020]/95 border-b border-gray-200 dark:border-white/[0.08] sticky top-0 z-40 backdrop-blur-md">
      <div className="max-w-[1680px] mx-auto px-4 py-2.5">
        <div className={`flex items-center justify-between ${showTabs || (breadcrumb && breadcrumb.length > 0) ? "mb-2" : ""}`}>
          <div className="min-w-0">
            <Link to="/" className="flex items-center gap-2 group">
              {/* min-w-0 down the flex chain so the name truncates instead of
                  running under the icons on the right (11-01: at 375px the
                  favorites and GitHub icons covered "AgentSkillsHub"). */}
              <span className="text-lg sm:text-xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2 min-w-0">
                <svg
                  className="w-6 h-6 sm:w-7 sm:h-7 shrink-0"
                  viewBox="350.95 190.72 133.48 133.48"
                  aria-hidden="true"
                >
                  <path
                    fill="#641efd"
                    d="M429.29,217.89h16.29c8.41,0,15.23,6.82,15.23,15.23v12.92c0,2.63,2.14,4.77,4.77,4.77h8.48c2.63,0,4.77-2.14,4.77-4.77v-16.19c0-16.98-13.77-30.75-30.75-30.75h-18.79c-2.63,0-4.77,2.14-4.77,4.77v9.25c0,2.63,2.14,4.77,4.77,4.77Z"
                  />
                  <path
                    fill="#641efd"
                    d="M375.24,246.04v-12.92c0-8.41,6.82-15.23,15.23-15.23h16.98c2.63,0,4.77-2.14,4.77-4.77v-9.25c0-2.63-2.14-4.77-4.77-4.77h-19.56c-16.98,0-30.75,13.77-30.75,30.75v16.19c0,2.63,2.14,4.77,4.77,4.77h8.56c2.63,0,4.77-2.14,4.77-4.77Z"
                  />
                  <path
                    fill="#641efd"
                    d="M407.45,297.15h-16.98c-8.41,0-15.23-6.82-15.23-15.23v-13.96c0-2.63-2.14-4.77-4.77-4.77h-8.56c-2.63,0-4.77,2.14-4.77,4.77v17.38c0,16.98,13.77,30.75,30.75,30.75h19.56c2.63,0,4.77-2.14,4.77-4.77v-9.41c0-2.63-2.14-4.77-4.77-4.77Z"
                  />
                  <path
                    fill="#641efd"
                    d="M460.81,267.97v13.96c0,8.41-6.82,15.23-15.23,15.23h-16.29c-2.63,0-4.77,2.14-4.77,4.77v9.41c0,2.63,2.14,4.77,4.77,4.77h18.79c16.98,0,30.75-13.77,30.75-30.75v-17.38c0-2.63-2.14-4.77-4.77-4.77h-8.48c-2.63,0-4.77,2.14-4.77,4.77Z"
                  />
                  <rect
                    fill="#feaf0a"
                    x="390.25"
                    y="248.66"
                    width="18.8"
                    height="18.04"
                    rx="4.89"
                  />
                  <rect
                    fill="#feaf0a"
                    x="427.27"
                    y="248.66"
                    width="18.8"
                    height="18.04"
                    rx="4.89"
                  />
                </svg>
                <span className="truncate min-w-0 group-hover:text-blue-600 transition-colors">
                  AgentSkillsHub
                </span>
              </span>
            </Link>
          </div>
          <div className="flex items-center gap-1.5 sm:gap-2.5 shrink-0">
            {/* Browse-by-type megamenu — desktop only */}
            <BrowseMenu />
            <Link
              to="/enterprise/"
              className="hidden lg:inline-flex items-center px-2.5 py-1 text-sm text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-gray-50 dark:hover:bg-white/[0.05] rounded-lg transition-colors font-medium"
              title="Enterprise — Trust Layer for AI Agent & MCP Deployment"
            >
              Enterprise
            </Link>
            <Link
              to="/pro/"
              className="hidden lg:inline-flex items-center gap-1 px-2.5 py-1 text-sm text-amber-700 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-950/40 rounded-lg transition-colors font-semibold ring-1 ring-inset ring-amber-300/80 dark:ring-amber-700/60"
              title={
                lang === "zh"
                  ? "Pro 深度搜索 — README 全文 · 200 条 · 导出 · API"
                  : "Pro deep search — full README · 200 results · export · API"
              }
            >
              ⚡ Pro
            </Link>
            <Link
              to="/submit/#sponsor"
              className="hidden xl:inline-flex items-center gap-1.5 px-2.5 py-1 text-sm text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-300 hover:bg-gray-50 dark:hover:bg-white/[0.05] rounded-lg transition-colors font-medium"
              title={lang === "zh" ? "首页双侧边栏赞助位 · $69/月" : "Advertise on homepage side rails · $69/mo"}
            >
              <svg className="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
              </svg>
              {lang === "zh" ? "投放广告" : "Advertise"}
            </Link>
            <Link
              to="/submit/"
              className="hidden sm:inline-flex items-center gap-1 px-2.5 py-1 text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/50 rounded-lg transition-colors font-semibold"
              title={lang === "zh" ? "提交 Skill 或 $19 加急审核" : "Submit a skill or $19 Fast-Track review"}
            >
              + {lang === "zh" ? "提交" : "Submit"}
            </Link>
            {/* Favorites and GitHub: below sm they move into the "···" menu */}
            <Link
              to="/favorites/"
              className="hidden sm:flex w-8 h-8 items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-gray-400 hover:text-rose-500 focus:outline-none focus:ring-2 focus:ring-rose-300"
              title={t("header.favorites")}
              aria-label="My favorites"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
              </svg>
            </Link>
            {/* GitHub repo link */}
            <a
              href="https://github.com/ZhuYansen/agent-skills-hub"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:flex w-8 h-8 items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-300"
              title="GitHub"
              aria-label="GitHub repository"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
            </a>
            {/* Secondary links collapsed into a "···" overflow menu */}
            <HeaderMoreMenu />
            <ThemeToggle />
            <LanguageToggle />
            {/* Newsletter CTA button + popup */}
            {/* Not positioned below sm, so the popup spans the header (16px in
                from each side) instead of running off the left edge of a phone. */}
            <div className="sm:relative" ref={nlRef}>
              {/* Below sm the label is hidden and only the icon shows, so the name a screen
                  reader announces comes from aria-label (Lighthouse "button-name", 2026-11-20). */}
              <button
                onClick={() => setShowNewsletterPopup(!showNewsletterPopup)}
                aria-label={t("header.newsletter")}
                aria-expanded={showNewsletterPopup}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium cursor-pointer"
              >
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
                <span className="hidden sm:inline">
                  {t("header.newsletter")}
                </span>
              </button>
              {showNewsletterPopup && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setShowNewsletterPopup(false)}
                  />
                  <div className="absolute inset-x-4 top-13 sm:inset-x-auto sm:right-0 sm:top-10 z-50 bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 p-5 sm:w-80 animate-in fade-in slide-in-from-top-2">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                        {t("newsletter.title")}
                      </h4>
                      <button
                        onClick={() => setShowNewsletterPopup(false)}
                        aria-label={t("search.close")}
                        className="w-6 h-6 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 cursor-pointer"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      </button>
                    </div>

                    {nlStatus === "success" ? (
                      <div className="text-center py-4">
                        <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-2">
                          <svg
                            className="w-6 h-6 text-green-600 dark:text-green-400"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2.5}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                        </div>
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {t("newsletter.successTitle")}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {t("newsletter.checkEmail")}
                        </p>
                      </div>
                    ) : (
                      <>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                          {t("newsletter.subtitle")}
                        </p>
                        <form onSubmit={handleNlSubmit} className="space-y-2">
                          <input
                            type="email"
                            value={nlEmail}
                            onChange={(e) => {
                              setNlEmail(e.target.value);
                              if (nlStatus !== "idle") setNlStatus("idle");
                            }}
                            placeholder={t("newsletter.placeholder")}
                            required
                            className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                            aria-label="Email address"
                          />
                          <button
                            type="submit"
                            disabled={!nlEmail.trim() || nlStatus === "loading"}
                            className="w-full px-4 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2"
                          >
                            {nlStatus === "loading" && (
                              <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            )}
                            {t("newsletter.button")}
                          </button>
                        </form>
                        {nlStatus === "error" && (
                          <p className="text-xs text-red-500 mt-2">
                            {nlMessage}
                          </p>
                        )}
                        <p className="text-center text-[11px] text-gray-400 mt-3">
                          {t("newsletter.frequency")}
                        </p>
                      </>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Tab Navigation or Breadcrumb */}
        {showTabs && onTabChange ? (
          <div className="-mb-3 sm:-mb-4">
            <div className="relative flex items-center gap-1 border-t border-gray-100 dark:border-white/[0.06] pt-1.5 pb-1.5 overflow-x-auto scrollbar-hide">
              <button
                onClick={() => onTabChange("overview")}
                className={`px-3 py-1.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap shrink-0 cursor-pointer ${
                  tab === "overview"
                    ? "border-indigo-500 text-indigo-600 dark:text-indigo-400"
                    : "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                }`}
              >
                {t("tab.overview")}
              </button>
              <button
                onClick={() => onTabChange("explore")}
                className={`px-3 py-1.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap shrink-0 cursor-pointer ${
                  tab === "explore"
                    ? "border-indigo-500 text-indigo-600 dark:text-indigo-400"
                    : "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                }`}
              >
                {t("tab.explore")}
              </button>
              {tab === "overview" && (
                <>
                  <span className="h-4 w-px bg-gray-200 dark:bg-white/10 mx-1.5 shrink-0" aria-hidden="true" />
                  <div
                    ref={subNavRef}
                    className="flex items-center gap-1 overflow-x-auto scrollbar-hide"
                  >
                    {[
                      { id: "scenarios", label: t("nav.scenarios") },
                      { id: "trending", label: t("nav.trending") },
                      { id: "categories", label: t("nav.categories") },
                      { id: "top-rated", label: t("nav.topRated") },
                      { id: "masters", label: t("nav.masters") },
                      { id: "workflows", label: t("nav.workflows") },
                    ].map((sec) => (
                      <button
                        key={sec.id}
                        onClick={() => {
                          const el = document.getElementById(sec.id);
                          if (el) {
                            el.scrollIntoView({ behavior: "smooth", block: "start" });
                            setTimeout(() => {
                              el.scrollIntoView({ behavior: "smooth", block: "start" });
                              el.classList.add("ring-2", "ring-indigo-300", "rounded-xl");
                              setTimeout(
                                () => el.classList.remove("ring-2", "ring-indigo-300", "rounded-xl"),
                                2000,
                              );
                            }, 400);
                          }
                        }}
                        className="px-2.5 py-1 text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-300 hover:bg-gray-100 dark:hover:bg-white/[0.05] rounded-md transition-colors whitespace-nowrap shrink-0 cursor-pointer"
                      >
                        {sec.label}
                      </button>
                    ))}
                    <Link
                      to="/analyzer/"
                      className="px-2.5 py-1 text-xs text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 rounded-md transition-colors whitespace-nowrap shrink-0 font-medium flex items-center gap-1"
                    >
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M10 1a1 1 0 011 1v.586l5.707 2.853A1 1 0 0117 6.414V10a7 7 0 01-7 7 7 7 0 01-7-7V6.414a1 1 0 01.293-.975L9 2.586V2a1 1 0 011-1z"
                          clipRule="evenodd"
                        />
                      </svg>
                      {t("nav.analyzer")}
                    </Link>
                  </div>
                </>
              )}
            </div>
          </div>
        ) : breadcrumb && breadcrumb.length > 0 ? (
          <div className="flex items-center gap-2 text-sm -mb-3 sm:-mb-4 pb-2 border-b border-gray-100 dark:border-gray-800">
            <Link
              to="/"
              className="text-gray-400 hover:text-blue-600 transition-colors"
            >
              {t("tab.overview")}
            </Link>
            {breadcrumb.map((item, i) => (
              <span key={i} className="flex items-center gap-2">
                <svg
                  className="w-3 h-3 text-gray-300 dark:text-gray-600 shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
                <span className="text-gray-700 dark:text-gray-200 font-medium truncate">
                  {item.label}
                </span>
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </header>
  );
}
