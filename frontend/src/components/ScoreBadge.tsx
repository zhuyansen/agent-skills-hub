interface Props {
  score: number;
  size?: "sm" | "md";
  showTier?: boolean;
}

function getScoreColor(score: number): string {
  if (score >= 80) return "bg-emerald-50 text-emerald-700 border-emerald-200";
  if (score >= 65) return "bg-blue-50 text-blue-700 border-blue-200";
  if (score >= 50) return "bg-amber-50 text-amber-700 border-amber-200";
  if (score >= 35) return "bg-orange-50 text-orange-700 border-orange-200";
  return "bg-gray-50 text-gray-600 border-gray-200";
}

function getTier(score: number): string {
  if (score >= 80) return "S";
  if (score >= 65) return "A";
  if (score >= 50) return "B";
  if (score >= 35) return "C";
  return "D";
}

function getTierColor(score: number): string {
  if (score >= 80) return "text-emerald-600";
  if (score >= 65) return "text-blue-600";
  if (score >= 50) return "text-amber-600";
  if (score >= 35) return "text-orange-600";
  return "text-gray-500";
}

export function ScoreBadge({ score, size = "md", showTier = false }: Props) {
  const color = getScoreColor(score);

  if (showTier) {
    const tier = getTier(score);
    // Compact: score number on top, tier letter below, all inside one unified element
    const w = size === "sm" ? "w-10" : "w-12";
    const h = size === "sm" ? "h-12" : "h-16";
    return (
      <div className={`${w} ${h} ${color} border rounded-xl flex flex-col items-center justify-center shrink-0`}>
        <span className={`${size === "sm" ? "text-sm" : "text-lg"} font-bold leading-none`}>
          {score.toFixed(0)}
        </span>
        <span className={`${size === "sm" ? "text-[9px]" : "text-[10px]"} font-bold opacity-60 leading-none mt-0.5`}>
          {tier}
        </span>
      </div>
    );
  }

  const sizeClass = size === "sm" ? "w-10 h-10 text-sm" : "w-12 h-12 text-base";
  return (
    <div
      className={`${sizeClass} ${color} border rounded-xl flex items-center justify-center font-bold shrink-0`}
    >
      {score.toFixed(0)}
    </div>
  );
}

export { getTier, getTierColor, getScoreColor };
