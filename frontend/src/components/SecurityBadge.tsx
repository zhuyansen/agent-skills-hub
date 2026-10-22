import { HowWeGradeLink } from "./HowWeGradeLink";
import { GRADES_ANCHOR } from "../lib/howWeGradeMeta.mjs";

interface Props {
  grade: string | null;
  /** "sm" = dense card row (default). "md" = detail page / collection header. */
  size?: "sm" | "md";
  /** Hide the Unaudited state (e.g. compact rows where null is preferred). */
  hideUnaudited?: boolean;
  /** Follow the badge with a small "How we grade" link to /how-we-grade/. Only where the
   *  badge is not inside a link or a clickable card (the skill page), or the clicks clash. */
  explain?: boolean;
}

interface Variant {
  label: string;
  dot: string; // filled status dot — the at-a-glance trust signal
  cls: string;
}

// The security grade is AgentSkillsHub's differentiator (the "Trust Layer" —
// LobeHub and every other directory show none of this). Every card carries a
// colour-coded status dot so trust is scannable down a grid, INCLUDING the
// honest "Unaudited" state — saying "we haven't audited this yet" is the point,
// not a gap to hide.
const CONFIG: Record<string, Variant> = {
  safe: {
    label: "Safe",
    dot: "bg-green-500",
    cls: "bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 border-green-200 dark:border-green-800",
  },
  caution: {
    label: "Caution",
    dot: "bg-amber-500",
    cls: "bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800",
  },
  unsafe: {
    label: "Unsafe",
    dot: "bg-red-500",
    cls: "bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border-red-200 dark:border-red-800",
  },
  reject: {
    label: "Reject",
    dot: "bg-red-600",
    cls: "bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300 border-red-300 dark:border-red-700",
  },
  unknown: {
    label: "Unaudited",
    dot: "bg-gray-300 dark:bg-gray-600",
    cls: "bg-gray-50 dark:bg-gray-800/60 text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-700",
  },
};

export function SecurityBadge({
  grade,
  size = "sm",
  hideUnaudited = false,
  explain = false,
}: Props) {
  const key = grade && CONFIG[grade] ? grade : "unknown";
  if (key === "unknown" && hideUnaudited) return null;
  const badge = <Badge gradeKey={key} size={size} />;
  if (!explain) return badge;
  return (
    <>
      {badge}
      <HowWeGradeLink
        anchor={GRADES_ANCHOR}
        className="self-center text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
      />
    </>
  );
}

function Badge({ gradeKey: key, size }: { gradeKey: string; size: "sm" | "md" }) {
  const c = CONFIG[key];
  const dims =
    size === "md"
      ? "gap-1.5 px-2.5 py-1 text-xs"
      : "gap-1 px-1.5 py-0.5 text-[9px]";
  const dotSize = size === "md" ? "w-2 h-2" : "w-1.5 h-1.5";
  return (
    <span
      className={`inline-flex items-center font-bold rounded border ${dims} ${c.cls}`}
      title={
        key === "unknown" ? "Not yet security-audited" : `Security: ${c.label}`
      }
    >
      <span className={`${dotSize} rounded-full ${c.dot}`} />
      {c.label}
    </span>
  );
}
