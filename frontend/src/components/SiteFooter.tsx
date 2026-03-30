import { Link, useNavigate, useLocation } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";

export function SiteFooter() {
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const location = useLocation();

  const navigateToSection = (id: string) => {
    // If already on home overview page, just scroll
    const isHome = location.pathname === "/" || location.pathname === "";
    const isOverview = !new URLSearchParams(location.search).get("tab") || new URLSearchParams(location.search).get("tab") === "overview";

    const scrollToEl = (el: HTMLElement) => {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      // Retry after lazy content renders & layout stabilizes
      setTimeout(() => {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
        el.classList.add("ring-2", "ring-indigo-300", "rounded-xl");
        setTimeout(() => el.classList.remove("ring-2", "ring-indigo-300", "rounded-xl"), 2000);
      }, 400);
    };

    if (isHome && isOverview) {
      const el = document.getElementById(id);
      if (el) {
        scrollToEl(el);
        return;
      }
    }

    // Otherwise navigate to home overview, then scroll after render
    navigate("/");
    setTimeout(() => {
      const el = document.getElementById(id);
      if (el) scrollToEl(el);
    }, 300);
  };

  return (
    <footer className="bg-gray-900 dark:bg-gray-950 text-gray-300 mt-12">
      {/* Main footer content */}
      <div className="max-w-7xl mx-auto px-4 py-10">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-8">
          {/* Brand column */}
          <div className="col-span-2 sm:col-span-1">
            <Link to="/" className="flex items-center gap-2 mb-3">
              <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="10" rx="2" strokeWidth="1.5"/><circle cx="9" cy="16" r="1.5" fill="currentColor"/><circle cx="15" cy="16" r="1.5" fill="currentColor"/><path d="M12 2v4M8 7h8a2 2 0 012 2v2H6V9a2 2 0 012-2z" strokeWidth="1.5" strokeLinecap="round"/></svg>
              <span className="text-white font-bold text-sm">Agent Skills Hub</span>
            </Link>
            <p className="text-xs text-gray-500 leading-relaxed">
              {lang === "zh"
                ? "发现和比较开源 Agent Skills、工具和 MCP 服务器。数据来自 GitHub，每8小时自动更新。"
                : "Discover and compare open-source Agent Skills, tools and MCP servers. Data sourced from GitHub, auto-updated every 8 hours."}
            </p>
          </div>

          {/* Navigation column — section links */}
          <div>
            <h4 className="text-white text-xs font-semibold uppercase tracking-wider mb-3">
              {lang === "zh" ? "导航" : "Navigation"}
            </h4>
            <ul className="space-y-2">
              {[
                { id: "trending", zh: "热门趋势", en: "Trending" },
                { id: "masters", zh: "技能大师", en: "Masters" },
                { id: "top-rated", zh: "高分项目", en: "Top Rated" },
                { id: "categories", zh: "分类浏览", en: "Categories" },
                { id: "workflows", zh: "工作流", en: "Workflows" },
                { id: "newsletter", zh: "订阅周报", en: "Newsletter" },
                { id: "submit-skill", zh: "提交技能", en: "Submit Skill" },
              ].map((sec) => (
                <li key={sec.id}>
                  <button
                    onClick={() => navigateToSection(sec.id)}
                    className="text-sm text-gray-400 hover:text-white transition-colors cursor-pointer"
                  >
                    {lang === "zh" ? sec.zh : sec.en}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Best Tools column */}
          <div>
            <h4 className="text-white text-xs font-semibold uppercase tracking-wider mb-3">
              {lang === "zh" ? "最佳工具" : "Best Tools"}
            </h4>
            <ul className="space-y-2">
              {[
                { slug: "web-scraping", zh: "网页抓取", en: "Web Scraping" },
                { slug: "mcp-database", zh: "MCP 数据库", en: "MCP Database" },
                { slug: "code-review", zh: "代码审查", en: "Code Review" },
                { slug: "claude-code-skills", zh: "Claude 技能", en: "Claude Skills" },
                { slug: "workflow-automation", zh: "工作流自动化", en: "Workflow Automation" },
                { slug: "security-audit", zh: "安全审计", en: "Security Audit" },
                { slug: "prompt-engineering", zh: "提示工程", en: "Prompt Engineering" },
              ].map((s) => (
                <li key={s.slug}>
                  <a
                    href={`/best/${s.slug}/`}
                    className="text-sm text-gray-400 hover:text-white transition-colors"
                  >
                    {lang === "zh" ? s.zh : s.en}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Community column */}
          <div>
            <h4 className="text-white text-xs font-semibold uppercase tracking-wider mb-3">
              {lang === "zh" ? "社区" : "Community"}
            </h4>
            <ul className="space-y-2">
              <li>
                <a
                  href="https://github.com/ZhuYansen/agent-skills-hub"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-400 hover:text-white transition-colors flex items-center gap-1.5"
                >
                  <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                  </svg>
                  GitHub
                </a>
              </li>
              <li>
                <a
                  href="https://x.com/GoSailGlobal"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-400 hover:text-white transition-colors flex items-center gap-1.5"
                >
                  <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                  </svg>
                  X (Twitter)
                </a>
              </li>
              <li>
                <Link to="/?tab=explore" className="text-sm text-gray-400 hover:text-white transition-colors flex items-center gap-1.5">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/></svg>
                  {t("tab.explore")}
                </Link>
              </li>
              <li>
                <a
                  href="/feed.xml"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-400 hover:text-orange-400 transition-colors flex items-center gap-1.5"
                >
                  <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M6.503 20.752c0 1.794-1.456 3.248-3.251 3.248-1.796 0-3.252-1.454-3.252-3.248 0-1.794 1.456-3.248 3.252-3.248 1.795 0 3.251 1.454 3.251 3.248zm-6.503-12.572v4.811c6.05.062 10.96 4.966 11.022 11.009h4.817c-.062-8.742-7.099-15.783-15.839-15.82zm0-8.18v4.819c12.376.051 22.41 10.087 22.461 22.419h4.539c-.062-14.896-12.149-27.005-27-27.238z"/>
                  </svg>
                  RSS Feed
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-gray-800">
        <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-gray-500">
          <span>
            &copy; {new Date().getFullYear()} Agent Skills Hub. {lang === "zh" ? "保留所有权利" : "All rights reserved"}.
          </span>
          <span className="flex items-center gap-3">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              {t("footer.autoUpdated")}
            </span>
            <span className="text-gray-600">·</span>
            <span>
              by{" "}
              <a
                href="https://x.com/GoSailGlobal"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 transition-colors"
              >
                Jason Zhu
              </a>
            </span>
          </span>
        </div>
      </div>
    </footer>
  );
}
