import { Link } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";
import { useStats } from "../hooks/useStats";

interface Collection {
  key: string;
  to: string;
  emoji: string;
  zh: string;
  en: string;
  zhDesc: string;
  enDesc: string;
  /** category name to pull a live count from stats.categories (optional) */
  catCount?: string;
  cardClass: string;
  badgeClass: string;
}

const COLLECTIONS: Collection[] = [
  {
    key: "safe-mcp",
    to: "/category/mcp-server/",
    emoji: "🛡️",
    zh: "MCP 服务器",
    en: "MCP Servers",
    zhDesc: "已安全评级",
    enDesc: "Security-graded",
    catCount: "mcp-server",
    cardClass:
      "bg-emerald-50/80 border-emerald-200/80 hover:border-emerald-400 dark:bg-[#0e241b]/95 dark:border-emerald-500/20 dark:hover:border-emerald-400/50",
    badgeClass: "bg-emerald-500/15 dark:bg-emerald-400/20",
  },
  {
    key: "claude-skills",
    to: "/category/claude-skill/",
    emoji: "⚡",
    zh: "Claude Skills",
    en: "Claude Skills",
    zhDesc: "Claude Code 必备",
    enDesc: "Built for Claude Code",
    catCount: "claude-skill",
    cardClass:
      "bg-indigo-50/80 border-indigo-200/80 hover:border-indigo-400 dark:bg-[#131936]/95 dark:border-indigo-500/20 dark:hover:border-indigo-400/50",
    badgeClass: "bg-indigo-500/15 dark:bg-indigo-400/20",
  },
  {
    key: "top-quality",
    to: "/#top-rated",
    emoji: "🏆",
    zh: "质量标杆",
    en: "Top Quality",
    zhDesc: "质量分最高",
    enDesc: "Highest-scored",
    cardClass:
      "bg-amber-50/80 border-amber-200/80 hover:border-amber-400 dark:bg-[#261c10]/95 dark:border-amber-500/20 dark:hover:border-amber-400/50",
    badgeClass: "bg-amber-500/15 dark:bg-amber-400/20",
  },
  {
    key: "trending",
    to: "/#trending",
    emoji: "🔥",
    zh: "本周飙升",
    en: "Trending",
    zhDesc: "增速最快",
    enDesc: "Fastest-rising",
    cardClass:
      "bg-rose-50/80 border-rose-200/80 hover:border-rose-400 dark:bg-[#28141c]/95 dark:border-rose-500/20 dark:hover:border-rose-400/50",
    badgeClass: "bg-rose-500/15 dark:bg-rose-400/20",
  },
  {
    key: "enterprise",
    to: "/enterprise/",
    emoji: "🏢",
    zh: "企业级",
    en: "Enterprise",
    zhDesc: "部署前审计 + 合规",
    enDesc: "Pre-deploy audit",
    cardClass:
      "bg-violet-50/80 border-violet-200/80 hover:border-violet-400 dark:bg-[#1f1532]/95 dark:border-violet-500/20 dark:hover:border-violet-400/50",
    badgeClass: "bg-violet-500/15 dark:bg-violet-400/20",
  },
];

export function CuratedCollections() {
  const { lang } = useI18n();
  const { categories } = useStats();
  const isZh = lang === "zh";

  const countFor = (cat?: string) =>
    cat ? categories.find((c) => c.name === cat)?.count : undefined;

  return (
    <section className="mb-10">
      <div className="flex items-center gap-2 mb-3.5">
        <h2 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white tracking-tight">
          {isZh ? "精选合集" : "Curated collections"}
        </h2>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {COLLECTIONS.map((c) => {
          const count = countFor(c.catCount);
          return (
            <Link
              key={c.key}
              to={c.to}
              className={`group flex items-center justify-between gap-2.5 px-4 py-4 rounded-2xl border transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md no-underline ${c.cardClass}`}
            >
              <div className="min-w-0">
                <span className="block text-sm font-semibold text-gray-900 dark:text-white truncate">
                  {isZh ? c.zh : c.en}
                </span>
                <span className="block text-[11px] text-gray-500 dark:text-white/55 truncate mt-0.5">
                  {isZh ? c.zhDesc : c.enDesc}
                  {typeof count === "number" && (
                    <span className="text-gray-400 dark:text-white/40">
                      {" · "}
                      {count.toLocaleString()}
                    </span>
                  )}
                </span>
              </div>
              <span
                className={`w-9 h-9 rounded-full flex items-center justify-center text-base shrink-0 transition-transform duration-200 group-hover:scale-105 ${c.badgeClass}`}
                aria-hidden="true"
              >
                {c.emoji}
              </span>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
