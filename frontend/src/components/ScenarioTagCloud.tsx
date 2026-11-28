import { useI18n } from "../i18n/I18nContext";

// Live (not retired) scenario pages, as /best/ lists them. Retired pages are noindex and
// left off /best/, so they are not counted (88 defined, 31 live on 2026-10-06).
const SCENARIO_COUNT = 35;

interface FeaturedScenario {
  slug: string;
  zh: string;
  en: string;
  zhSub: string;
  enSub: string;
  cardClass: string;
  iconBg: string;
  iconPath: string;
}

const FEATURED_SCENARIOS: FeaturedScenario[] = [
  {
    slug: "ppt-presentation",
    zh: "PPT 生成",
    en: "PPT & Slides",
    zhSub: "32 个实测对比",
    enSub: "32 hands-on tested",
    cardClass:
      "bg-blue-50/90 border-blue-200/80 hover:border-blue-400 dark:bg-[#111c33]/95 dark:border-blue-500/20 dark:hover:border-blue-400/50",
    iconBg: "bg-blue-500/20 text-blue-600 dark:bg-blue-400/25 dark:text-blue-300",
    iconPath: "M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z",
  },
  {
    slug: "claude-video-skills",
    zh: "Claude 做视频",
    en: "Claude Video",
    zhSub: "16 个工具实测",
    enSub: "16 tools tested",
    cardClass:
      "bg-violet-50/90 border-violet-200/80 hover:border-violet-400 dark:bg-[#1e1532]/95 dark:border-violet-500/20 dark:hover:border-violet-400/50",
    iconBg: "bg-violet-500/20 text-violet-600 dark:bg-violet-400/25 dark:text-violet-300",
    iconPath: "M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z",
  },
  {
    slug: "image-generation",
    zh: "AI 生图",
    en: "Image Gen",
    zhSub: "130 个模型实测",
    enSub: "130 tested",
    cardClass:
      "bg-amber-50/90 border-amber-200/80 hover:border-amber-400 dark:bg-[#261c10]/95 dark:border-amber-500/20 dark:hover:border-amber-400/50",
    iconBg: "bg-amber-500/20 text-amber-600 dark:bg-amber-400/25 dark:text-amber-300",
    iconPath: "M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z",
  },
  {
    slug: "ai-design",
    zh: "设计与前端",
    en: "AI & Design",
    zhSub: "UI / 设计系统",
    enSub: "UI & design systems",
    cardClass:
      "bg-emerald-50/90 border-emerald-200/80 hover:border-emerald-400 dark:bg-[#0e241b]/95 dark:border-emerald-500/20 dark:hover:border-emerald-400/50",
    iconBg: "bg-emerald-500/20 text-emerald-600 dark:bg-emerald-400/25 dark:text-emerald-300",
    iconPath: "M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01",
  },
  {
    slug: "mcp-database",
    zh: "数据库 MCP",
    en: "Database MCP",
    zhSub: "Postgres / SQL",
    enSub: "Postgres & SQL",
    cardClass:
      "bg-cyan-50/90 border-cyan-200/80 hover:border-cyan-400 dark:bg-[#0d2229]/95 dark:border-cyan-500/20 dark:hover:border-cyan-400/50",
    iconBg: "bg-cyan-500/20 text-cyan-600 dark:bg-cyan-400/25 dark:text-cyan-300",
    iconPath: "M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4",
  },
];

const FEATURED_SLUGS = new Set(FEATURED_SCENARIOS.map((s) => s.slug));

const MORE_SCENARIOS = [
  // Preserves every remaining live /best/* link from the original tag cloud.
  { slug: "animation-skills", zh: "动画 Skill", en: "Animation Skills" },
  { slug: "claude-code-hooks", zh: "Claude Code Hooks", en: "Claude Code Hooks" },
  { slug: "3d-mcp", zh: "3D 与游戏引擎", en: "Blender & 3D MCP" },
  { slug: "codex-skills", zh: "Codex Skills", en: "Codex Skills" },
  { slug: "skill-management-tools", zh: "Skill 管理", en: "Skill Managers" },
  { slug: "obsidian-second-brain", zh: "Obsidian × Claude", en: "Obsidian + Claude" },
  { slug: "anti-slop", zh: "去 AI 味", en: "Humanizer Skills" },
  { slug: "knowledge-base", zh: "LLM Wiki 知识库", en: "LLM Wiki" },
  { slug: "browser-automation", zh: "浏览器自动化", en: "Browser Automation" },
  { slug: "code-review", zh: "代码审查", en: "Code Review" },
  { slug: "telegram-bot", zh: "Telegram 机器人", en: "Telegram Bots" },
  { slug: "typesafe-jev", zh: "TypeSafe Jev", en: "TypeSafe Jev" },
  { slug: "claude-code-skills", zh: "Claude Code 技能", en: "Claude Code Skills" },
  { slug: "web-scraping", zh: "网页抓取", en: "Web Scraping" },
  { slug: "prompt-engineering", zh: "提示工程", en: "Prompt Engineering" },
].filter((s) => !FEATURED_SLUGS.has(s.slug));

export function ScenarioTagCloud() {
  const { lang } = useI18n();
  const isZh = lang === "zh";

  return (
    <section id="scenarios" className="scroll-mt-44 mb-10">
      <div className="flex items-center justify-between gap-2 mb-4">
        <div className="flex items-center gap-2">
          <h2 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white tracking-tight">
            {isZh ? "热门分类与场景" : "Top categories & scenarios"}
          </h2>
        </div>
        <a
          href={isZh ? "/best/zh/" : "/best/"}
          className="text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline shrink-0"
        >
          {isZh ? `全部 ${SCENARIO_COUNT} 个场景 →` : `All ${SCENARIO_COUNT} guides →`}
        </a>
      </div>

      {/* Top 5 mcp.so-style tinted-glass capsule cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-4">
        {FEATURED_SCENARIOS.map((s) => (
          <a
            key={s.slug}
            href={`/best/${s.slug}/`}
            className={`group flex items-center justify-between gap-3 rounded-2xl border px-4 py-4 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md no-underline ${s.cardClass}`}
          >
            <div className="min-w-0">
              <div className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                {isZh ? s.zh : s.en}
              </div>
              <div className="text-[11px] text-gray-500 dark:text-white/55 truncate mt-0.5">
                {isZh ? s.zhSub : s.enSub}
              </div>
            </div>
            <span
              className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 transition-transform duration-200 group-hover:scale-105 ${s.iconBg}`}
              aria-hidden="true"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d={s.iconPath} />
              </svg>
            </span>
          </a>
        ))}
      </div>

      {/* Remaining live scenarios as sleek dark-glass pills */}
      <div className="flex flex-wrap gap-2">
        {MORE_SCENARIOS.map((s) => (
          <a
            key={s.slug}
            href={`/best/${s.slug}/`}
            className="px-3 py-1.5 text-xs font-medium rounded-full border border-gray-200 dark:border-white/[0.08] bg-white dark:bg-white/[0.03] text-gray-700 dark:text-gray-300 hover:border-indigo-400 hover:text-indigo-600 dark:hover:border-indigo-400/50 dark:hover:text-indigo-300 dark:hover:bg-indigo-500/[0.08] transition-all no-underline"
          >
            {isZh ? s.zh : s.en}
          </a>
        ))}
        <a
          href="/best/"
          className="px-3 py-1.5 text-xs font-medium rounded-full border border-dashed border-gray-300 dark:border-white/15 text-gray-500 dark:text-gray-400 hover:border-indigo-400 hover:text-indigo-500 transition-all no-underline"
        >
          {isZh
            ? `全部 ${SCENARIO_COUNT} 个场景 →`
            : `All ${SCENARIO_COUNT} scenarios →`}
        </a>
      </div>
    </section>
  );
}
