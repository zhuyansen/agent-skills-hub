interface Props {
  score: number;
  size?: "sm" | "md" | "lg";
  showTier?: boolean;
}

// Tiers re-cut for the ×1.42 composite rescale (2026-07-03): the raw sum
// empirically topped out ~67, so the old S≥80 tier was unreachable dead code.
// On the new scale (ceiling ≈95): S = the handful of all-time best, A = the
// genuine top tier, B = solid, C = average.
function getScoreColor(score: number): string {
  if (score >= 90) return "bg-emerald-50 text-emerald-700 border-emerald-200";
  if (score >= 80) return "bg-blue-50 text-blue-700 border-blue-200";
  if (score >= 60) return "bg-amber-50 text-amber-700 border-amber-200";
  if (score >= 40) return "bg-orange-50 text-orange-700 border-orange-200";
  return "bg-gray-50 text-gray-600 border-gray-200";
}

function getTier(score: number): string {
  if (score >= 90) return "S";
  if (score >= 80) return "A";
  if (score >= 60) return "B";
  if (score >= 40) return "C";
  return "D";
}

function getTierColor(score: number): string {
  if (score >= 90) return "text-emerald-600";
  if (score >= 80) return "text-blue-600";
  if (score >= 60) return "text-amber-600";
  if (score >= 40) return "text-orange-600";
  return "text-gray-500";
}

export function ScoreBadge({ score, size = "md", showTier = false }: Props) {
  const color = getScoreColor(score);

  if (showTier) {
    const tier = getTier(score);
    // Compact: score number on top, tier letter below, all inside one unified element
    const w = size === "sm" ? "w-10" : size === "lg" ? "w-14" : "w-12";
    const h = size === "sm" ? "h-12" : size === "lg" ? "h-18" : "h-16";
    return (
      <div
        className={`${w} ${h} ${color} border rounded-xl flex flex-col items-center justify-center shrink-0`}
      >
        <span
          className={`${size === "sm" ? "text-sm" : size === "lg" ? "text-xl" : "text-lg"} font-bold leading-none`}
        >
          {score.toFixed(0)}
        </span>
        <span
          className={`${size === "sm" ? "text-[9px]" : size === "lg" ? "text-xs" : "text-[10px]"} font-bold opacity-60 leading-none mt-0.5`}
        >
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

/** Compact quality badge for card/table use. Shows the actual 0-100 quality
 *  score (not just a tier letter) — the plan calls for a visible number, and a
 *  precise "Q 92" reads as a stronger trust signal than "Q:A". */
export function QualityBadge({ score }: { score: number }) {
  if (!score || score <= 0) return null;
  const color = getScoreColor(score);
  return (
    <span
      className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[9px] font-bold rounded ${color}`}
      title={`Quality score: ${Math.round(score)}/100`}
    >
      <span className="opacity-60">Q</span>
      {Math.round(score)}
    </span>
  );
}

export { getTier, getTierColor, getScoreColor };
