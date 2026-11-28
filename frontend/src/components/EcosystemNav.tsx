import { useI18n } from "../i18n/I18nContext";
import { useStats } from "../hooks/useStats";
import { ECOSYSTEM_LAYERS } from "../utils/ecosystem";
import type { TransKey } from "../i18n/translations";

interface Props {
  onSelectCategory: (category: string) => void;
  onSelectLayer: (layer: string) => void;
}

export function EcosystemNav({ onSelectCategory, onSelectLayer }: Props) {
  const { t } = useI18n();
  const { stats } = useStats();

  // Compute counts per layer from stats categories
  const layerCounts: Record<string, number> = {};
  for (const layer of ECOSYSTEM_LAYERS) {
    layerCounts[layer.id] = 0;
    for (const cat of layer.categories) {
      const found = stats?.categories.find((c) => c.name === cat);
      if (found) layerCounts[layer.id] += found.count;
    }
  }

  const LAYER_GLASS: Record<string, string> = {
    mcp: "bg-emerald-50/70 border-emerald-200/80 hover:border-emerald-400 dark:bg-[#0e221b]/85 dark:border-emerald-500/20 dark:hover:border-emerald-400/45",
    claude: "bg-indigo-50/70 border-indigo-200/80 hover:border-indigo-400 dark:bg-[#131934]/85 dark:border-indigo-500/20 dark:hover:border-indigo-400/45",
    agent: "bg-violet-50/70 border-violet-200/80 hover:border-violet-400 dark:bg-[#1d1530]/85 dark:border-violet-500/20 dark:hover:border-violet-400/45",
  };

  return (
    <section className="mb-10 mt-2">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        {ECOSYSTEM_LAYERS.map((layer) => (
          <div
            key={layer.id}
            onClick={() => onSelectLayer(layer.id)}
            className={`rounded-2xl border p-5 cursor-pointer group transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md ${
              LAYER_GLASS[layer.id] ||
              "bg-white dark:bg-white/[0.03] border-gray-200 dark:border-white/[0.08] hover:border-indigo-400"
            }`}
          >
            {/* Header */}
            <div className="flex items-center gap-2.5 mb-2">
              <span className="w-8 h-8 rounded-full bg-white/80 dark:bg-white/[0.08] flex items-center justify-center text-base shrink-0">
                {layer.icon}
              </span>
              <h3 className={`text-sm font-bold ${layer.colorClass}`}>
                {t(`ecosystem.${layer.id}` as TransKey)}
              </h3>
              <span className="ml-auto text-xs font-semibold text-gray-500 dark:text-white/60 tabular-nums">
                {layerCounts[layer.id]?.toLocaleString() || "..."}
              </span>
            </div>

            {/* Description */}
            <p className="text-xs text-gray-600 dark:text-white/60 mb-3.5 leading-relaxed">
              {t(`ecosystem.${layer.id}Desc` as TransKey)}
            </p>

            {/* Sub-chips */}
            <div className="flex flex-wrap gap-1.5">
              {layer.categories.map((cat) => {
                const count = stats?.categories.find(
                  (c) => c.name === cat,
                )?.count;
                return (
                  <button
                    key={cat}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectCategory(cat);
                    }}
                    className={`px-2.5 py-0.5 text-[11px] font-medium rounded-full border transition-all ${layer.borderClass} ${layer.bgClass} ${layer.colorClass} hover:opacity-80 cursor-pointer`}
                  >
                    {cat}
                    {count ? ` (${count.toLocaleString()})` : ""}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
