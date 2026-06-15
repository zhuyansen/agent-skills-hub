import { useState } from "react";
import { Link } from "react-router-dom";
import { useStats } from "../hooks/useStats";
import { useI18n } from "../i18n/I18nContext";

// Slug → display label. Mirrors CategoryPage; only these get a menu entry so a
// stray/empty category from the data never leaks into the nav.
const CATEGORY_LABELS: Record<string, { en: string; zh: string }> = {
  "mcp-server": { en: "MCP Server", zh: "MCP 服务器" },
  "agent-tool": { en: "Agent Tool", zh: "Agent 工具" },
  "claude-skill": { en: "Claude Skill", zh: "Claude Skill" },
  "codex-skill": { en: "OpenClaw / Codex", zh: "OpenClaw / Codex" },
  "ai-skill": { en: "AI Skill", zh: "AI Skill" },
  "llm-plugin": { en: "LLM Plugin", zh: "LLM 插件" },
};

export function BrowseMenu() {
  const { categories } = useStats();
  const { lang } = useI18n();
  const isZh = lang === "zh";
  const [open, setOpen] = useState(false);

  const items = categories
    .filter((c) => CATEGORY_LABELS[c.name])
    .sort((a, b) => b.count - a.count);

  return (
    <div
      className="relative hidden md:block"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-1 px-2.5 py-1 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg transition-colors font-medium cursor-pointer"
        aria-haspopup="true"
        aria-expanded={open}
      >
        {isZh ? "浏览" : "Browse"}
        <svg
          className={`w-3.5 h-3.5 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {open && (
        <div className="absolute left-0 top-full pt-2 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 p-2 w-72">
            <div className="px-2 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500">
              {isZh ? "按类型浏览" : "Browse by type"}
            </div>
            {items.length === 0 ? (
              <div className="px-2 py-3 text-sm text-gray-400">…</div>
            ) : (
              items.map((c) => (
                <Link
                  key={c.name}
                  to={`/category/${c.name}/`}
                  onClick={() => setOpen(false)}
                  className="flex items-center justify-between px-2 py-2 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/30 group transition-colors"
                >
                  <span className="text-sm text-gray-700 dark:text-gray-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                    {isZh
                      ? CATEGORY_LABELS[c.name].zh
                      : CATEGORY_LABELS[c.name].en}
                  </span>
                  <span className="text-xs font-medium text-gray-400 dark:text-gray-500 tabular-nums">
                    {c.count.toLocaleString()}
                  </span>
                </Link>
              ))
            )}
            <div className="border-t border-gray-100 dark:border-gray-700 mt-1 pt-1">
              <Link
                to="/"
                onClick={() => setOpen(false)}
                className="block px-2 py-2 text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 rounded-lg transition-colors"
              >
                {isZh ? "浏览全部 Skills →" : "Browse all skills →"}
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
