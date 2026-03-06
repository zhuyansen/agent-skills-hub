interface Props {
  sizeCategory: string;
  sizeKb?: number;
}

const SIZE_CONFIG: Record<string, { label: string; color: string; bg: string; border: string }> = {
  micro: { label: "Micro", color: "text-emerald-700", bg: "bg-emerald-50", border: "border-emerald-200" },
  small: { label: "Small", color: "text-blue-700", bg: "bg-blue-50", border: "border-blue-200" },
  medium: { label: "Medium", color: "text-amber-700", bg: "bg-amber-50", border: "border-amber-200" },
  large: { label: "Large", color: "text-red-700", bg: "bg-red-50", border: "border-red-200" },
};

function formatSize(kb: number): string {
  if (kb >= 1024) return `${(kb / 1024).toFixed(1)} MB`;
  return `${kb} KB`;
}

export function SizeBadge({ sizeCategory, sizeKb }: Props) {
  const config = SIZE_CONFIG[sizeCategory];
  if (!config) return null;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full border ${config.bg} ${config.color} ${config.border}`}
      title={sizeKb ? formatSize(sizeKb) : undefined}
    >
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2 1 3 3 3h10c2 0 3-1 3-3V7c0-2-1-3-3-3H7C5 4 4 5 4 7z" />
      </svg>
      {config.label}
    </span>
  );
}
