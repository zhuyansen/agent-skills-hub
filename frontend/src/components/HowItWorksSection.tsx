import { useI18n } from "../i18n/I18nContext";

const STEPS = [
  {
    num: "01",
    icon: "🔄",
    titleEn: "Auto-Collect",
    titleZh: "自动采集",
    descEn: "Every 8 hours, our crawler scans GitHub for new AI agent tools, MCP servers, and Claude skills across 25,000+ repositories.",
    descZh: "每 8 小时，爬虫自动扫描 GitHub 上 25,000+ 仓库中的新 AI Agent 工具、MCP 服务器和 Claude 技能。",
  },
  {
    num: "02",
    icon: "⚡",
    titleEn: "Quality Scoring",
    titleZh: "质量评分",
    descEn: "10 weighted signals — stars, maintenance, documentation, code quality — combined into a single 0-100 composite score.",
    descZh: "10 项加权指标——Star 数、维护活跃度、文档质量、代码质量——综合为 0-100 的质量评分。",
  },
  {
    num: "03",
    icon: "🎯",
    titleEn: "Smart Matching",
    titleZh: "智能匹配",
    descEn: "53 scenario pages match tools to your use case. Compare side-by-side, filter by category, language, or platform.",
    descZh: "53 个场景页面将工具匹配到你的使用场景。支持并排对比、按分类/语言/平台筛选。",
  },
];

export function HowItWorksSection() {
  const { lang } = useI18n();
  const isZh = lang === "zh";

  return (
    <section className="py-12 mb-8">
      <div className="text-center mb-10">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
          {isZh ? "我们如何运作" : "How It Works"}
        </h2>
        <p className="text-gray-500 dark:text-gray-400 max-w-2xl mx-auto">
          {isZh
            ? "全自动化流水线，从数据采集到质量评分，再到智能推荐。"
            : "A fully automated pipeline — from data collection to quality scoring to smart recommendations."}
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {STEPS.map((s, i) => (
          <div key={i} className="relative text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-50 dark:bg-blue-900/30 mb-4">
              <span className="text-2xl">{s.icon}</span>
            </div>
            <div className="absolute top-0 left-0 text-5xl font-black text-gray-100 dark:text-gray-800 -z-10 -translate-x-2 -translate-y-2 select-none">
              {s.num}
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              {isZh ? s.titleZh : s.titleEn}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
              {isZh ? s.descZh : s.descEn}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
