import { useI18n } from "../i18n/I18nContext";

const CATEGORY_CHIPS = [
  { key: "mcp-server", label: "MCP Server" },
  { key: "claude-skill", label: "Claude Skill" },
  { key: "agent-tool", label: "Agent Tool" },
  { key: "codex-skill", label: "Codex Skill" },
  { key: "ai-skill", label: "AI Skill" },
  { key: "llm-plugin", label: "LLM Plugin" },
];

interface Props {
  onSelect: (category: string) => void;
}

export function CategoryChips({ onSelect }: Props) {
  const { t } = useI18n();

  return (
    <section className="mb-8 mt-2">
      <div className="flex items-center gap-2.5 flex-wrap">
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
          {t("chips.quickFilter")}:
        </span>
        {CATEGORY_CHIPS.map((chip) => (
          <button
            key={chip.key}
            onClick={() => onSelect(chip.key)}
            className="px-3 py-1.5 text-xs font-medium rounded-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:border-indigo-400 hover:text-indigo-600 dark:hover:border-indigo-500 dark:hover:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-all cursor-pointer"
          >
            {chip.label}
          </button>
        ))}
      </div>
    </section>
  );
}
