import { useCompare } from "../hooks/useCompare";
import type { Skill } from "../types/skill";

interface Props {
  skill: Skill;
  size?: "sm" | "md";
}

export function CompareButton({ skill, size = "md" }: Props) {
  const { isInCompare, toggleCompare, items, maxCompare } = useCompare();
  const active = isInCompare(skill.id);
  const disabled = !active && items.length >= maxCompare;
  const sz = size === "sm" ? "w-7 h-7" : "w-9 h-9";
  const iconSz = size === "sm" ? "w-4 h-4" : "w-5 h-5";

  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        e.preventDefault();
        toggleCompare(skill);
      }}
      disabled={disabled}
      className={`${sz} flex items-center justify-center rounded-lg transition-colors cursor-pointer ${
        active
          ? "bg-blue-50 dark:bg-blue-900/30 text-blue-500 hover:bg-blue-100 dark:hover:bg-blue-900/50"
          : disabled
          ? "bg-gray-50 dark:bg-gray-800 text-gray-200 dark:text-gray-700 cursor-not-allowed"
          : "bg-gray-50 dark:bg-gray-800 text-gray-300 dark:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-blue-400"
      }`}
      aria-label={active ? "Remove from compare" : "Add to compare"}
      title={active ? "Remove from compare" : disabled ? "Max 3 skills" : "Add to compare"}
    >
      <svg className={iconSz} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={active ? 2.5 : 2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
      </svg>
    </button>
  );
}
