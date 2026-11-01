import { useState } from "react";
import { Link } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";
import { useStats } from "../hooks/useStats";
import { timeAgo } from "../utils/time";

/** "···" overflow menu — collects the secondary header items (X / RSS / WeChat /
 *  last-updated) so the top bar stays clean. */
export function HeaderMoreMenu() {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [showWechat, setShowWechat] = useState(false);

  const close = () => {
    setOpen(false);
    setShowWechat(false);
  };

  const itemCls =
    "flex items-center gap-2.5 px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/60 rounded-lg transition-colors";

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-300 cursor-pointer"
        title={t("header.more")}
        aria-label="More links"
        aria-expanded={open}
      >
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <circle cx="5" cy="12" r="2" />
          <circle cx="12" cy="12" r="2" />
          <circle cx="19" cy="12" r="2" />
        </svg>
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={close} />
          <div className="absolute right-0 top-10 z-50 w-60 bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 p-1.5 animate-in fade-in slide-in-from-top-2">
            {/* Below lg the header's text links (Enterprise / Blue Book / Blog)
                are hidden to stop the top bar overflowing over the logo — they
                live here instead. lg:hidden avoids duplication on desktop. */}
            <div className="lg:hidden border-b border-gray-100 dark:border-gray-700 mb-1.5 pb-1.5">
              <a href="/enterprise/" className={itemCls}>
                🏢 Enterprise
              </a>
              <a href="/book/" className={itemCls}>
                📘 Blue Book
              </a>
              <a href="/blog/" className={itemCls}>
                ✍️ Blog
              </a>
            </div>
            {/* Below sm the header's favorites and GitHub icons are hidden too,
                so the logo keeps its room on phones; sm:hidden as above. */}
            <div className="sm:hidden border-b border-gray-100 dark:border-gray-700 mb-1.5 pb-1.5">
              <Link to="/favorites/" onClick={close} className={itemCls}>
                <svg
                  className="w-4 h-4 shrink-0 text-rose-500"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                </svg>
                {t("header.favorites")}
              </Link>
              <a
                href="https://github.com/ZhuYansen/agent-skills-hub"
                target="_blank"
                rel="noopener noreferrer"
                className={itemCls}
              >
                <svg
                  className="w-4 h-4 shrink-0"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                </svg>
                GitHub
              </a>
            </div>
            <a
              href="https://x.com/GoSailGlobal"
              target="_blank"
              rel="noopener noreferrer"
              className={itemCls}
            >
              <svg
                className="w-4 h-4 shrink-0"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
              X (Twitter)
            </a>
            <a
              href="/feed.xml"
              target="_blank"
              rel="noopener noreferrer"
              className={itemCls}
            >
              <svg
                className="w-4 h-4 shrink-0 text-orange-500"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M6.503 20.752c0 1.794-1.456 3.248-3.251 3.248-1.796 0-3.252-1.454-3.252-3.248 0-1.794 1.456-3.248 3.252-3.248 1.795 0 3.251 1.454 3.251 3.248zm-6.503-12.572v4.811c6.05.062 10.96 4.966 11.022 11.009h4.817c-.062-8.742-7.099-15.783-15.839-15.82zm0-8.18v4.819c12.376.051 22.41 10.087 22.461 22.419h4.539c-.062-14.896-12.149-27.005-27-27.238z" />
              </svg>
              {t("header.rss")}
            </a>
            <button
              onClick={() => setShowWechat(!showWechat)}
              className={`w-full text-left ${itemCls} cursor-pointer`}
            >
              <svg
                className="w-4 h-4 shrink-0 text-green-500"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 01.213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 00.167-.054l1.903-1.114a.864.864 0 01.717-.098 10.16 10.16 0 002.837.403c.276 0 .543-.027.811-.05a6.13 6.13 0 01-.247-1.722c0-3.647 3.39-6.605 7.57-6.605.63 0 1.246.066 1.84.178C17.99 4.504 13.773 2.188 8.691 2.188z" />
              </svg>
              {t("header.wechat")}
            </button>
            {showWechat && (
              <div className="px-3 pb-2 pt-1">
                <img
                  src="/wechat-qr.jpg"
                  alt="WeChat QR Code"
                  className="w-full rounded-lg border border-gray-100 dark:border-gray-700"
                />
                <p className="text-[11px] text-gray-400 text-center mt-1.5">
                  {t("header.wechatTip")}
                </p>
              </div>
            )}
            <div className="border-t border-gray-100 dark:border-gray-700 mt-1.5 pt-2 px-3 pb-1">
              <LastUpdated />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/** The open menu's "last updated" line. Its own component so the stats it
 *  reads are fetched when the menu opens, not on every page load — see
 *  BrowsePanel in BrowseMenu.tsx for why that matters. */
function LastUpdated() {
  const { t } = useI18n();
  const { stats } = useStats();
  return (
    <span className="flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-500">
      <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
      {t("header.lastUpdated")}{" "}
      {stats ? timeAgo(stats.last_sync_at) : "..."}
    </span>
  );
}
