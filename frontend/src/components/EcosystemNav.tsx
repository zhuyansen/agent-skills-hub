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

  return (
    <section className="mb-8 mt-2">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {ECOSYSTEM_LAYERS.map((layer) => (
          <div
            key={layer.id}
            onClick={() => onSelectLayer(layer.id)}
            className={`relative rounded-xl border bg-white dark:bg-gray-800/80 p-4 cursor-pointer transition-all duration-200 ${layer.hoverClass} border-gray-200 dark:border-gray-700 hover:shadow-md group`}
          >
            {/* Header */}
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">{layer.icon}</span>
              <h3 className={`text-sm font-semibold ${layer.colorClass}`}>
                {t(`ecosystem.${layer.id}` as TransKey)}
              </h3>
              <span className="ml-auto text-xs font-medium text-gray-400 dark:text-gray-500 tabular-nums">
                {layerCounts[layer.id]?.toLocaleString() || "..."}
              </span>
            </div>

            {/* Description */}
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-3 leading-relaxed">
              {t(`ecosystem.${layer.id}Desc` as TransKey)}
            </p>

            {/* Sub-chips */}
            <div className="flex flex-wrap gap-1.5">
              {layer.categories.map((cat) => {
                const count = stats?.categories.find((c) => c.name === cat)?.count;
                return (
                  <button
                    key={cat}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectCategory(cat);
                    }}
                    className={`px-2 py-0.5 text-[10px] font-medium rounded-full border transition-all ${layer.borderClass} ${layer.bgClass} ${layer.colorClass} hover:opacity-80 cursor-pointer`}
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
