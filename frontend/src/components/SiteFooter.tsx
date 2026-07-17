import { Link, useNavigate, useLocation } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";

export function SiteFooter() {
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const location = useLocation();

  const navigateToSection = (id: string) => {
    // Special routes — navigate directly instead of scrolling.
    // Blog and Daily are static HTML pages (not SPA routes), so hard-navigate.
    if (id === "blog") {
      window.location.href = "/blog/";
      return;
    }
    if (id === "daily") {
      window.location.href = "/daily/";
      return;
    }
    // If already on home overview page, just scroll
    const isHome = location.pathname === "/" || location.pathname === "";
    const isOverview =
      !new URLSearchParams(location.search).get("tab") ||
      new URLSearchParams(location.search).get("tab") === "overview";

    const scrollToEl = (el: HTMLElement) => {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      // Retry after lazy content renders & layout stabilizes
      setTimeout(() => {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
        el.classList.add("ring-2", "ring-indigo-300", "rounded-xl");
        setTimeout(
          () => el.classList.remove("ring-2", "ring-indigo-300", "rounded-xl"),
          2000,
        );
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
      <div className="max-w-[1440px] mx-auto px-4 py-10">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-8">
          {/* Brand column */}
          <div className="col-span-2 sm:col-span-1">
            <Link to="/" className="flex items-center gap-2 mb-3">
              <svg
                className="w-6 h-6"
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
              <span className="text-white font-bold text-sm">
                AgentSkillsHub
              </span>
            </Link>
            <p className="text-xs text-gray-500 leading-relaxed">
              {lang === "zh"
                ? "Claude Skills、MCP 服务器、Agent 工具的开源目录 —— 数据来自 GitHub，10 维质量评分，每 8 小时刷新。"
                : "The open directory of Claude Skills, MCP Servers, and Agent Tools — sourced from GitHub, scored on 10 signals, refreshed every 8 hours."}
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
                { id: "daily", zh: "每日新增", en: "Daily New" },
                { id: "blog", zh: "博客", en: "Blog" },
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
                { slug: "ppt-presentation", zh: "PPT 制作", en: "PPT Skills" },
                { slug: "web-scraping", zh: "网页抓取", en: "Web Scraping" },
                { slug: "mcp-database", zh: "MCP 数据库", en: "MCP Database" },
                { slug: "code-review", zh: "代码审查", en: "Code Review" },
                {
                  slug: "claude-code-skills",
                  zh: "Claude 技能",
                  en: "Claude Skills",
                },
                {
                  slug: "workflow-automation",
                  zh: "工作流自动化",
                  en: "Workflow Automation",
                },
                {
                  slug: "security-audit",
                  zh: "安全审计",
                  en: "Security Audit",
                },
                {
                  slug: "prompt-engineering",
                  zh: "提示工程",
                  en: "Prompt Engineering",
                },
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
                  <svg
                    className="w-3.5 h-3.5"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
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
                  <svg
                    className="w-3.5 h-3.5"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                  </svg>
                  X (Twitter)
                </a>
              </li>
              <li>
                <Link
                  to="/?tab=explore"
                  className="text-sm text-gray-400 hover:text-white transition-colors flex items-center gap-1.5"
                >
                  <svg
                    className="w-3.5 h-3.5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
                    />
                  </svg>
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
                  <svg
                    className="w-3.5 h-3.5"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M6.503 20.752c0 1.794-1.456 3.248-3.251 3.248-1.796 0-3.252-1.454-3.252-3.248 0-1.794 1.456-3.248 3.252-3.248 1.795 0 3.251 1.454 3.251 3.248zm-6.503-12.572v4.811c6.05.062 10.96 4.966 11.022 11.009h4.817c-.062-8.742-7.099-15.783-15.839-15.82zm0-8.18v4.819c12.376.051 22.41 10.087 22.461 22.419h4.539c-.062-14.896-12.149-27.005-27-27.238z" />
                  </svg>
                  RSS Feed
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Trust links bar */}
      <div className="border-t border-gray-800">
        <div className="max-w-[1440px] mx-auto px-4 py-3 flex flex-wrap items-center justify-center gap-4 text-xs text-gray-500">
          <a href="/about/" className="hover:text-white transition-colors">
            {lang === "zh" ? "关于我们" : "About"}
          </a>
          <span className="text-gray-700">·</span>
          <a
            href="/verified-creator/apply/"
            className="hover:text-emerald-400 transition-colors"
          >
            {lang === "zh" ? "Verified Creator" : "Verified Creator"}
          </a>
          <span className="text-gray-700">·</span>
          <a
            href="/enterprise/"
            className="hover:text-blue-400 transition-colors"
          >
            {lang === "zh" ? "企业版" : "For Business"}
          </a>
          <span className="text-gray-700">·</span>
          <a
            href="mailto:m17551076169@gmail.com"
            className="hover:text-white transition-colors"
          >
            {lang === "zh" ? "联系我们" : "Contact"}
          </a>
          <span className="text-gray-700">·</span>
          <a href="/privacy/" className="hover:text-white transition-colors">
            {lang === "zh" ? "隐私政策" : "Privacy Policy"}
          </a>
          <span className="text-gray-700">·</span>
          <a href="/terms/" className="hover:text-white transition-colors">
            {lang === "zh" ? "服务条款" : "Terms of Service"}
          </a>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-gray-800">
        <div className="max-w-[1440px] mx-auto px-4 py-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-gray-500">
          <span>
            &copy; {new Date().getFullYear()} AgentSkillsHub.{" "}
            {lang === "zh" ? "保留所有权利" : "All rights reserved"}.
          </span>
          <span className="flex items-center gap-3">
            {/* Directory-listing badges (reciprocal verification links). */}
            <a
              href="https://turbo0.com/item/agentskillshub"
              target="_blank"
              rel="noopener noreferrer"
            >
              <img
                src="https://img.turbo0.com/badge-listed-dark.svg"
                alt="Listed on Turbo0"
                className="h-7 w-auto"
                loading="lazy"
              />
            </a>
            <span className="text-gray-600">·</span>
            {/* The pulsing dot reads as interactive — Clarity's top homepage
                dead-click cluster was this footer bar. Give the click a
                destination: "auto-updated" → what's new today. */}
            <a
              href="/daily/"
              className="flex items-center gap-1.5 hover:text-white transition-colors"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              {t("footer.autoUpdated")}
            </a>
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
