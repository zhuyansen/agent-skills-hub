interface Props {
  grade: string | null;
}

const CONFIG: Record<string, { label: string; cls: string }> = {
  safe: {
    label: "Safe",
    cls: "bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400 border-green-100 dark:border-green-800",
  },
  caution: {
    label: "Caution",
    cls: "bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-800",
  },
  unsafe: {
    label: "Unsafe",
    cls: "bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 border-red-100 dark:border-red-800",
  },
  reject: {
    label: "Reject",
    cls: "bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300 border-red-200 dark:border-red-700",
  },
};

export function SecurityBadge({ grade }: Props) {
  if (!grade || grade === "unknown") return null;
  const c = CONFIG[grade] ?? CONFIG.caution;
  return (
    <span className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[9px] font-bold rounded border ${c.cls}`}>
      <svg className="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 1a1 1 0 011 1v.586l5.707 2.853A1 1 0 0117 6.414V10a7 7 0 01-7 7 7 7 0 01-7-7V6.414a1 1 0 01.293-.975L9 2.586V2a1 1 0 011-1z" clipRule="evenodd" />
      </svg>
      {c.label}
    </span>
  );
}
