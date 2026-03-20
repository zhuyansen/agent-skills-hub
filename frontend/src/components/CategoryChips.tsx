import { useI18n } from "../i18n/I18nContext";

const CATEGORY_CHIPS = [
  { key: "mcp-server", label: "MCP Server", color: "bg-purple-100 text-purple-700 border-purple-200 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-800 hover:bg-purple-200 dark:hover:bg-purple-900/50" },
  { key: "claude-skill", label: "Claude Skill", color: "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800 hover:bg-blue-200 dark:hover:bg-blue-900/50" },
  { key: "agent-tool", label: "Agent Tool", color: "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800 hover:bg-emerald-200 dark:hover:bg-emerald-900/50" },
  { key: "codex-skill", label: "Codex Skill", color: "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800 hover:bg-amber-200 dark:hover:bg-amber-900/50" },
  { key: "ai-skill", label: "AI Skill", color: "bg-pink-100 text-pink-700 border-pink-200 dark:bg-pink-900/30 dark:text-pink-300 dark:border-pink-800 hover:bg-pink-200 dark:hover:bg-pink-900/50" },
  { key: "llm-plugin", label: "LLM Plugin", color: "bg-cyan-100 text-cyan-700 border-cyan-200 dark:bg-cyan-900/30 dark:text-cyan-300 dark:border-cyan-800 hover:bg-cyan-200 dark:hover:bg-cyan-900/50" },
];

interface Props {
  onSelect: (category: string) => void;
}

export function CategoryChips({ onSelect }: Props) {
  const { t } = useI18n();

  return (
    <section className="mb-8">
      <div className="flex items-center gap-3 flex-wrap">
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
          {t("chips.quickFilter")}:
        </span>
        {CATEGORY_CHIPS.map((chip) => (
          <button
            key={chip.key}
            onClick={() => onSelect(chip.key)}
            className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-all cursor-pointer ${chip.color}`}
          >
            {chip.label}
          </button>
        ))}
      </div>
    </section>
  );
}
