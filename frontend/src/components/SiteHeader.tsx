import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { LanguageToggle } from "./LanguageToggle";
import { useI18n } from "../i18n/I18nContext";
import { useStats } from "../hooks/useStats";
import { timeAgo } from "../utils/time";

interface Props {
  /** Show tab navigation (only on Home page) */
  showTabs?: boolean;
  tab?: "overview" | "explore";
  onTabChange?: (tab: "overview" | "explore") => void;
  /** Breadcrumb items for detail pages */
  breadcrumb?: { label: string }[];
}

export function SiteHeader({ showTabs, tab, onTabChange, breadcrumb }: Props) {
  const { t } = useI18n();
  const navigate = useNavigate();
  const { stats } = useStats();
  const [showWechat, setShowWechat] = useState(false);

  const scrollToNewsletter = () => {
    const tryScroll = () => {
      const el = document.getElementById("newsletter");
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
        // Briefly highlight the section
        el.classList.add("ring-2", "ring-indigo-300");
        setTimeout(() => el.classList.remove("ring-2", "ring-indigo-300"), 2000);
        return true;
      }
      return false;
    };

    if (tryScroll()) return;

    // If newsletter section not found (on explore tab or detail page), navigate home first
    if (onTabChange) {
      onTabChange("overview");
      setTimeout(tryScroll, 300);
    } else {
      navigate("/");
      setTimeout(tryScroll, 300);
    }
  };

  return (
    <header className="bg-gradient-to-r from-white via-white to-blue-50/50 border-b border-gray-200 sticky top-0 z-10 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 py-3 sm:py-4">
        <div className="flex items-center justify-between mb-3">
          <div className="min-w-0">
            <Link to="/" className="flex items-center gap-2 group">
              <h1 className="text-lg sm:text-xl font-bold text-gray-900 flex items-center gap-2">
                <svg className="w-6 h-6 sm:w-7 sm:h-7 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="10" rx="2" strokeWidth="1.5"/><circle cx="9" cy="16" r="1.5" fill="currentColor"/><circle cx="15" cy="16" r="1.5" fill="currentColor"/><path d="M12 2v4M8 7h8a2 2 0 012 2v2H6V9a2 2 0 012-2z" strokeWidth="1.5" strokeLinecap="round"/></svg>
                <span className="truncate group-hover:text-blue-600 transition-colors">Agent Skills Hub</span>
                <span className="ml-1 px-2 py-0.5 text-[10px] rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 text-white font-semibold tracking-wide uppercase shrink-0">Beta</span>
              </h1>
            </Link>
            <p className="text-xs sm:text-sm text-gray-500 mt-0.5 hidden sm:block">
              {t("header.subtitle")}
            </p>
          </div>
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            <span className="text-sm text-gray-400 items-center gap-1.5 hidden lg:flex">
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
            {/* WeChat contact button */}
            <div className="relative">
              <button
                onClick={() => setShowWechat(!showWechat)}
                className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors text-gray-400 hover:text-green-500 focus:outline-none focus:ring-2 focus:ring-green-300 cursor-pointer"
                title={t("header.wechat")}
                aria-label="WeChat"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 01.213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 00.167-.054l1.903-1.114a.864.864 0 01.717-.098 10.16 10.16 0 002.837.403c.276 0 .543-.027.811-.05a6.13 6.13 0 01-.247-1.722c0-3.647 3.39-6.605 7.57-6.605.63 0 1.246.066 1.84.178C17.99 4.504 13.773 2.188 8.691 2.188zm-2.6 4.408c.56 0 1.016.455 1.016 1.016 0 .56-.456 1.016-1.017 1.016-.56 0-1.016-.456-1.016-1.016 0-.56.456-1.016 1.016-1.016zm5.44 0c.56 0 1.016.455 1.016 1.016 0 .56-.456 1.016-1.016 1.016-.56 0-1.016-.456-1.016-1.016 0-.56.456-1.016 1.016-1.016zm4.294 4.287c-3.65 0-6.614 2.528-6.614 5.646 0 3.118 2.963 5.646 6.614 5.646a7.8 7.8 0 002.222-.325.636.636 0 01.526.074l1.403.823a.24.24 0 00.122.04c.118 0 .213-.097.213-.215 0-.053-.021-.104-.035-.155l-.288-1.093a.432.432 0 01.156-.488c1.35-.995 2.21-2.466 2.21-4.107 0-3.118-2.963-5.646-6.614-5.646h.085zm-2.834 2.94c.411 0 .744.334.744.745a.745.745 0 11-.744-.745zm5.297 0c.411 0 .744.334.744.745a.745.745 0 11-.744-.745z"/>
                </svg>
              </button>
              {/* WeChat QR code popup */}
              {showWechat && (
                <>
                  {/* Backdrop */}
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setShowWechat(false)}
                  />
                  {/* Popup card */}
                  <div className="absolute right-0 top-10 z-50 bg-white rounded-xl shadow-2xl border border-gray-200 p-4 w-64 animate-in fade-in slide-in-from-top-2">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-medium text-gray-700">{t("header.wechatScan")}</span>
                      <button
                        onClick={() => setShowWechat(false)}
                        className="w-6 h-6 flex items-center justify-center rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-600 cursor-pointer"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                    <img
                      src="/wechat-qr.jpg"
                      alt="WeChat QR Code"
                      className="w-full rounded-lg border border-gray-100"
                    />
                    <p className="text-xs text-gray-400 text-center mt-2">{t("header.wechatTip")}</p>
                  </div>
                </>
              )}
            </div>
            <LanguageToggle />
            {/* Newsletter CTA button */}
            <button
              onClick={scrollToNewsletter}
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-xs bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium cursor-pointer"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              {t("header.newsletter")}
            </button>
          </div>
        </div>

        {/* Tab Navigation or Breadcrumb */}
        {showTabs && onTabChange ? (
          <div className="-mb-3 sm:-mb-4">
            <div className="flex items-center gap-1 border-b border-gray-100 pb-0">
              <button
                onClick={() => onTabChange("overview")}
                className={`px-3 sm:px-4 py-2 sm:py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                  tab === "overview"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                <svg className="w-4 h-4 inline -mt-0.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"/></svg>
                {t("tab.overview")}
              </button>
              <button
                onClick={() => onTabChange("explore")}
                className={`px-3 sm:px-4 py-2 sm:py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                  tab === "explore"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                <svg className="w-4 h-4 inline -mt-0.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/></svg>
                {t("tab.explore")}
              </button>
            </div>
            {/* Section quick navigation (overview tab only) */}
            {tab === "overview" && (
              <div className="flex items-center gap-1.5 py-2 overflow-x-auto scrollbar-hide">
                {[
                  { id: "trending", label: t("nav.trending") },
                  { id: "masters", label: t("nav.masters") },
                  { id: "recent", label: t("nav.recent") },
                  { id: "top-rated", label: t("nav.topRated") },
                  { id: "categories", label: t("nav.categories") },
                  { id: "workflows", label: t("nav.workflows") },
                  { id: "newsletter", label: t("nav.newsletter") },
                ].map((sec) => (
                  <button
                    key={sec.id}
                    onClick={() => {
                      const el = document.getElementById(sec.id);
                      if (el) {
                        el.scrollIntoView({ behavior: "smooth", block: "start" });
                        el.classList.add("ring-2", "ring-indigo-300", "rounded-xl");
                        setTimeout(() => el.classList.remove("ring-2", "ring-indigo-300", "rounded-xl"), 2000);
                      }
                    }}
                    className="px-2.5 py-1 text-xs text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors whitespace-nowrap shrink-0 cursor-pointer"
                  >
                    {sec.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : breadcrumb && breadcrumb.length > 0 ? (
          <div className="flex items-center gap-2 text-sm -mb-3 sm:-mb-4 pb-2 border-b border-gray-100">
            <Link to="/" className="text-gray-400 hover:text-blue-600 transition-colors">
              {t("tab.overview")}
            </Link>
            {breadcrumb.map((item, i) => (
              <span key={i} className="flex items-center gap-2">
                <svg className="w-3 h-3 text-gray-300 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                <span className="text-gray-700 font-medium truncate">{item.label}</span>
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </header>
  );
}
