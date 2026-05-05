import { useI18n } from "../i18n/I18nContext";

const HOT_SCENARIOS = [
  { slug: "web-scraping", zh: "网页抓取", en: "Web Scraping" },
  { slug: "mcp-database", zh: "MCP 数据库", en: "MCP Database" },
  { slug: "mcp-browser", zh: "MCP 浏览器", en: "MCP Browser" },
  { slug: "code-review", zh: "代码审查", en: "Code Review" },
  { slug: "code-completion", zh: "代码补全", en: "Code Completion" },
  { slug: "workflow-automation", zh: "工作流自动化", en: "Workflow Automation" },
  { slug: "claude-code-skills", zh: "Claude Code 技能", en: "Claude Code Skills" },
  { slug: "security-audit", zh: "安全审计", en: "Security Audit" },
  { slug: "prompt-engineering", zh: "提示工程", en: "Prompt Engineering" },
  { slug: "semantic-search", zh: "语义搜索", en: "Semantic Search" },
  { slug: "ci-cd", zh: "CI/CD 部署", en: "CI/CD & DevOps" },
  { slug: "browser-automation", zh: "浏览器自动化", en: "Browser Automation" },
  { slug: "git-tools", zh: "Git 工具", en: "Git Tools" },
  { slug: "slack-integration", zh: "Slack 集成", en: "Slack Integration" },
  { slug: "content-writing", zh: "内容写作", en: "Content Writing" },
  { slug: "debugging", zh: "调试工具", en: "Debugging" },
];

export function ScenarioTagCloud() {
  const { lang } = useI18n();

  return (
    <section id="scenarios" className="scroll-mt-44 mb-10">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">🔥</span>
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
          {lang === "zh" ? "热门场景" : "Popular Scenarios"}
        </h2>
        <span className="text-xs text-gray-400 dark:text-gray-500">
          {lang === "zh" ? "— 按场景找到最佳工具" : "— Find the best tools by scenario"}
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        {HOT_SCENARIOS.map((s) => (
          <a
            key={s.slug}
            href={`/best/${s.slug}/`}
            className="px-3 py-1.5 text-sm rounded-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:border-blue-400 hover:text-blue-600 dark:hover:border-blue-500 dark:hover:text-blue-400 hover:shadow-sm transition-all"
          >
            {lang === "zh" ? s.zh : s.en}
          </a>
        ))}
        <a
          href="/best/"
          className="px-3 py-1.5 text-sm rounded-full border border-dashed border-gray-300 dark:border-gray-600 text-gray-400 dark:text-gray-500 hover:border-blue-400 hover:text-blue-500 transition-all"
        >
          {lang === "zh" ? `全部 71 个场景 →` : `All 71 scenarios →`}
        </a>
      </div>
    </section>
  );
}
