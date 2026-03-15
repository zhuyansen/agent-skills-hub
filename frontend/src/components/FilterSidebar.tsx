import { useI18n } from "../i18n/I18nContext";
import type { CategoryCount, SkillsQueryParams } from "../types/skill";
import { getScoreColor } from "./ScoreBadge";

interface Props {
  params: SkillsQueryParams;
  onUpdate: (update: Partial<SkillsQueryParams>) => void;
  categories: CategoryCount[];
}

const TIERS = ["S", "A", "B", "C", "D"] as const;
const TIER_SCORES = [80, 65, 50, 35, 0]; // minimum score for each tier
const STAR_PRESETS = [
  { label: "100+", value: 100 },
  { label: "500+", value: 500 },
  { label: "1k+", value: 1000 },
  { label: "5k+", value: 5000 },
];

export function FilterSidebar({ params, onUpdate, categories }: Props) {
  const { t } = useI18n();

  const selectedTiers = params.quality_tiers ? params.quality_tiers.split(",") : [];

  const toggleTier = (tier: string) => {
    const current = new Set(selectedTiers);
    if (current.has(tier)) {
      current.delete(tier);
    } else {
      current.add(tier);
    }
    const value = current.size > 0 ? Array.from(current).join(",") : undefined;
    onUpdate({ quality_tiers: value });
  };

  const setMinStars = (value: number | undefined) => {
    onUpdate({ min_stars: params.min_stars === value ? undefined : value });
  };

  return (
    <aside className="w-56 shrink-0 space-y-5">
      {/* Quality Grade */}
      <div>
        <h4 className="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2 tracking-wide">
          {t("filter.qualityGrade")}
        </h4>
        <div className="space-y-1">
          {TIERS.map((tier, i) => (
            <label
              key={tier}
              className="flex items-center gap-2 py-1 px-2 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
            >
              <input
                type="checkbox"
                checked={selectedTiers.includes(tier)}
                onChange={() => toggleTier(tier)}
                className="w-3.5 h-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
              <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded ${getScoreColor(TIER_SCORES[i])}`}>
                {tier}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {tier === "S" ? "≥80" : tier === "A" ? "65-79" : tier === "B" ? "50-64" : tier === "C" ? "35-49" : "<35"}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Stars Range */}
      <div>
        <h4 className="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2 tracking-wide">
          {t("filter.starsRange")}
        </h4>
        <div className="flex flex-wrap gap-1">
          {STAR_PRESETS.map(({ label, value }) => (
            <button
              key={value}
              onClick={() => setMinStars(value)}
              className={`px-2.5 py-1 text-xs rounded-full border transition-colors cursor-pointer ${
                params.min_stars === value
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:border-blue-300"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Category */}
      <div>
        <h4 className="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2 tracking-wide">
          {t("table.category")}
        </h4>
        <div className="space-y-0.5 max-h-48 overflow-y-auto">
          <button
            onClick={() => onUpdate({ category: undefined })}
            className={`w-full text-left px-2 py-1 text-xs rounded transition-colors cursor-pointer ${
              !params.category ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 font-medium" : "text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
            }`}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat.name}
              onClick={() => onUpdate({ category: params.category === cat.name ? undefined : cat.name })}
              className={`w-full text-left px-2 py-1 text-xs rounded transition-colors cursor-pointer flex items-center justify-between ${
                params.category === cat.name ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 font-medium" : "text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
              }`}
            >
              <span className="truncate">{cat.name}</span>
              <span className="text-gray-400 dark:text-gray-500 text-[10px] shrink-0">{cat.count}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Size */}
      <div>
        <h4 className="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2 tracking-wide">
          {t("explore.size").replace(":", "")}
        </h4>
        <div className="flex flex-wrap gap-1">
          {["micro", "small", "medium", "large"].map((s) => (
            <button
              key={s}
              onClick={() => onUpdate({ size_category: params.size_category === s ? undefined : s })}
              className={`px-2.5 py-1 text-xs rounded-full border transition-colors cursor-pointer ${
                params.size_category === s
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:border-blue-300"
              }`}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Platform */}
      <div>
        <h4 className="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2 tracking-wide">
          {t("explore.platform").replace(":", "")}
        </h4>
        <div className="flex flex-wrap gap-1">
          {["python", "node", "go", "docker", "claude", "mcp"].map((p) => (
            <button
              key={p}
              onClick={() => onUpdate({ platform: params.platform === p ? undefined : p })}
              className={`px-2.5 py-1 text-xs rounded-full border transition-colors cursor-pointer ${
                params.platform === p
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:border-blue-300"
              }`}
            >
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
