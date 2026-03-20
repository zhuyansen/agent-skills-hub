import { useNavigate } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";

interface WorkflowStep {
  name: string;
  slug: string;
  description_zh: string;
  description_en: string;
}

interface Scenario {
  id: string;
  icon: string;
  title_zh: string;
  title_en: string;
  description_zh: string;
  description_en: string;
  steps: WorkflowStep[];
}

const scenarios: Scenario[] = [
  {
    id: "social-media",
    icon: "share",
    title_zh: "自媒体内容创作",
    title_en: "Social Media Content",
    description_zh: "从内容创作到多平台发布的完整工作流",
    description_en: "End-to-end workflow from content creation to multi-platform publishing",
    steps: [
      {
        name: "Agent-Reach",
        slug: "Panniantong/Agent-Reach",
        description_zh: "阅读 X (Twitter) 内容",
        description_en: "Read X (Twitter) content",
      },
      {
        name: "baoyu-skills",
        slug: "JimLiu/baoyu-skills",
        description_zh: "封面图 + 微信公众号 + 小红书图文",
        description_en: "Cover images + WeChat + Xiaohongshu posts",
      },
      {
        name: "qiaomu-x-article-publisher",
        slug: "joeseesun/qiaomu-x-article-publisher",
        description_zh: "Markdown 发布 X 长文",
        description_en: "Publish long-form articles to X",
      },
    ],
  },
  {
    id: "learning",
    icon: "book",
    title_zh: "学习研究",
    title_en: "Learning & Research",
    description_zh: "高效获取和整理知识的学习工作流",
    description_en: "Efficient knowledge acquisition and organization workflow",
    steps: [
      {
        name: "yt-search-download",
        slug: "joeseesun/yt-search-download",
        description_zh: "YouTube 内容搜索与下载",
        description_en: "YouTube content search & download",
      },
      {
        name: "anything-to-notebooklm",
        slug: "joeseesun/anything-to-notebooklm",
        description_zh: "任意内容转换到 NotebookLM",
        description_en: "Convert any content to NotebookLM",
      },
      {
        name: "defuddle-skill",
        slug: "joeseesun/defuddle-skill",
        description_zh: "网页内容智能提取",
        description_en: "Smart web content extraction",
      },
    ],
  },
  {
    id: "dev-tools",
    icon: "wrench",
    title_zh: "开发效率",
    title_en: "Developer Productivity",
    description_zh: "提升开发效率的实用工具组合",
    description_en: "Practical tool combinations to boost development efficiency",
    steps: [
      {
        name: "knowledge-site-creator",
        slug: "joeseesun/knowledge-site-creator",
        description_zh: "知识站点一键生成",
        description_en: "One-click knowledge site generator",
      },
      {
        name: "qiaomu-design-advisor",
        slug: "joeseesun/qiaomu-design-advisor",
        description_zh: "UI/UX 设计顾问",
        description_en: "UI/UX design advisor",
      },
      {
        name: "skill-publisher",
        slug: "joeseesun/skill-publisher",
        description_zh: "Skill 发布与管理工具",
        description_en: "Skill publishing & management tool",
      },
    ],
  },
];

const iconPaths: Record<string, string> = {
  share:
    "M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z",
  book: "M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25",
  wrench:
    "M11.42 15.17l-5.384 5.384a1.522 1.522 0 01-2.153-2.153l5.384-5.384m2.153 2.153l5.384-5.384a1.522 1.522 0 00-2.153-2.153L9.267 12.95m2.153 2.22a3.015 3.015 0 004.276 0 3.015 3.015 0 000-4.276",
};

export function ScenarioWorkflows() {
  const { t, lang } = useI18n();
  const navigate = useNavigate();

  return (
    <section className="mb-10">
      <div className="mb-6">
        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
          {t("scenarios.title")}
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t("scenarios.subtitle")}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {scenarios.map((sc) => (
          <div
            key={sc.id}
            className="bg-white dark:bg-gray-800/80 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
                <svg
                  className="w-5 h-5 text-blue-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="1.5"
                    d={iconPaths[sc.icon] || iconPaths.wrench}
                  />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">
                  {lang === "zh" ? sc.title_zh : sc.title_en}
                </h3>
                <p className="text-xs text-gray-400 dark:text-gray-500 leading-tight">
                  {lang === "zh" ? sc.description_zh : sc.description_en}
                </p>
              </div>
            </div>

            {/* Call chain visualization */}
            <div className="relative">
              {sc.steps.map((step, idx) => (
                <div key={step.name} className="relative">
                  {/* Connector line between steps */}
                  {idx < sc.steps.length - 1 && (
                    <div className="absolute left-[9px] top-[32px] w-0.5 h-[calc(100%-8px)] bg-gradient-to-b from-blue-300 dark:from-blue-600 to-blue-100 dark:to-blue-800/30" />
                  )}
                  <button
                    onClick={() => navigate(`/skill/${step.slug}`)}
                    className="w-full flex items-start gap-3 p-2 rounded-lg hover:bg-blue-50 dark:hover:bg-gray-800 transition-colors group text-left relative z-10"
                  >
                    {/* Step node */}
                    <div className="mt-0.5 w-[18px] h-[18px] rounded-full border-2 border-blue-400 dark:border-blue-500 bg-white dark:bg-gray-900 flex items-center justify-center shrink-0">
                      <div className="w-2 h-2 rounded-full bg-blue-500 dark:bg-blue-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-200 group-hover:text-blue-600 transition-colors truncate">
                          {step.name}
                        </span>
                        {idx < sc.steps.length - 1 && (
                          <svg className="w-3 h-3 text-gray-300 dark:text-gray-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                          </svg>
                        )}
                      </div>
                      <span className="text-xs text-gray-400 dark:text-gray-500 block truncate">
                        {lang === "zh" ? step.description_zh : step.description_en}
                      </span>
                    </div>
                    <svg
                      className="w-3.5 h-3.5 text-gray-300 dark:text-gray-600 group-hover:text-blue-400 transition-colors shrink-0 mt-1"
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
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
