export interface EcosystemLayer {
  id: string;
  categories: string[];
  icon: string; // emoji
  colorClass: string; // tailwind color scheme
  hoverClass: string;
  bgClass: string;
  borderClass: string;
}

export const ECOSYSTEM_LAYERS: EcosystemLayer[] = [
  {
    id: "skills",
    categories: ["claude-skill", "codex-skill", "ai-skill"],
    icon: "✨",
    colorClass: "text-violet-600 dark:text-violet-400",
    hoverClass: "hover:border-violet-300 dark:hover:border-violet-600",
    bgClass: "bg-violet-50 dark:bg-violet-900/20",
    borderClass: "border-violet-100 dark:border-violet-800",
  },
  {
    id: "mcp-servers",
    categories: ["mcp-server"],
    icon: "🔌",
    colorClass: "text-blue-600 dark:text-blue-400",
    hoverClass: "hover:border-blue-300 dark:hover:border-blue-600",
    bgClass: "bg-blue-50 dark:bg-blue-900/20",
    borderClass: "border-blue-100 dark:border-blue-800",
  },
  {
    id: "frameworks",
    categories: ["agent-tool", "llm-plugin"],
    icon: "⚙️",
    colorClass: "text-emerald-600 dark:text-emerald-400",
    hoverClass: "hover:border-emerald-300 dark:hover:border-emerald-600",
    bgClass: "bg-emerald-50 dark:bg-emerald-900/20",
    borderClass: "border-emerald-100 dark:border-emerald-800",
  },
];

export function getLayerForCategory(category: string): string | null {
  for (const layer of ECOSYSTEM_LAYERS) {
    if (layer.categories.includes(category)) return layer.id;
  }
  return null;
}

export function getCategoriesForLayer(layerId: string): string[] {
  const layer = ECOSYSTEM_LAYERS.find((l) => l.id === layerId);
  return layer ? layer.categories : [];
}
