import { useI18n } from "../i18n/I18nContext";

const PAIN_POINTS = [
  {
    icon: "🔍",
    titleEn: "Fragmented Sources",
    titleZh: "信息分散",
    descEn: "AI tools are scattered across GitHub, npm, PyPI, and dozens of directories. Finding the right one takes hours.",
    descZh: "AI 工具分散在 GitHub、npm、PyPI 和数十个目录中，找到合适的要花好几个小时。",
  },
  {
    icon: "📊",
    titleEn: "No Quality Signals",
    titleZh: "缺乏质量信号",
    descEn: "Stars alone don't tell the whole story. No composite scoring, no maintenance checks, no community validation.",
    descZh: "Star 数不能说明一切。没有综合评分、没有维护检查、没有社区验证。",
  },
  {
    icon: "🧩",
    titleEn: "Hard to Compare",
    titleZh: "难以对比",
    descEn: "MCP servers, Claude skills, agent frameworks — different ecosystems, no unified way to discover and compare.",
    descZh: "MCP 服务器、Claude 技能、Agent 框架——不同生态系统，没有统一的发现和对比方式。",
  },
];

export function ProblemSection() {
  const { lang } = useI18n();
  const isZh = lang === "zh";

  return (
    <section className="py-12 mb-8">
      <div className="text-center mb-10">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
          {isZh ? "开发者面临的痛点" : "The Problem Developers Face"}
        </h2>
        <p className="text-gray-500 dark:text-gray-400 max-w-2xl mx-auto">
          {isZh
            ? "AI Agent 工具生态正在爆发式增长，但发现和评估这些工具仍然是个难题。"
            : "The AI agent tool ecosystem is exploding, but discovering and evaluating these tools remains a challenge."}
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {PAIN_POINTS.map((p, i) => (
          <div
            key={i}
            className="p-6 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 hover:shadow-lg transition-shadow"
          >
            <div className="text-3xl mb-4">{p.icon}</div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              {isZh ? p.titleZh : p.titleEn}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
              {isZh ? p.descZh : p.descEn}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
