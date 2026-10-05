import { useI18n } from "../i18n/I18nContext";

// Total curated scenarios — keep in sync with scripts/scenario-keywords.json.
const SCENARIO_COUNT = 88;

const HOT_SCENARIOS = [
  // Reviewed pages first (10-05): the list used to send half its links to retired, noindex pages.
  { slug: "claude-video-skills", zh: "Claude Code 做视频", en: "Claude Code Video Skills" },
  { slug: "ppt-presentation", zh: "PPT 制作", en: "PPT Skills" },
  { slug: "claude-code-hooks", zh: "Claude Code Hooks", en: "Claude Code Hooks" },
  { slug: "image-generation", zh: "AI 生图", en: "Image Generation" },
  { slug: "ai-design", zh: "设计与前端", en: "Design Skills" },
  { slug: "codex-skills", zh: "Codex Skills", en: "Codex Skills" },
  { slug: "skill-management-tools", zh: "Skill 管理", en: "Skill Managers" },
  { slug: "obsidian-second-brain", zh: "Obsidian × Claude", en: "Obsidian + Claude" },
  { slug: "anti-slop", zh: "去 AI 味", en: "Humanizer Skills" },
  { slug: "knowledge-base", zh: "LLM Wiki 知识库", en: "LLM Wiki" },
  { slug: "mcp-database", zh: "数据库 MCP", en: "Database MCP" },
  { slug: "browser-automation", zh: "浏览器自动化", en: "Browser Automation" },
  { slug: "code-review", zh: "代码审查", en: "Code Review" },
  { slug: "telegram-bot", zh: "Telegram 机器人", en: "Telegram Bots" },
  { slug: "typesafe-jev", zh: "TypeSafe Jev", en: "TypeSafe Jev" },
  { slug: "claude-code-skills", zh: "Claude Code 技能", en: "Claude Code Skills" },
  { slug: "web-scraping", zh: "网页抓取", en: "Web Scraping" },
  { slug: "prompt-engineering", zh: "提示工程", en: "Prompt Engineering" },
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
          {lang === "zh"
            ? "— 按场景找到最佳工具"
            : "— Find the best tools by scenario"}
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
          {/* Keep in sync with scenario-keywords.json count (currently 84) */}
          {lang === "zh"
            ? `全部 ${SCENARIO_COUNT} 个场景 →`
            : `All ${SCENARIO_COUNT} scenarios →`}
        </a>
      </div>
    </section>
  );
}
