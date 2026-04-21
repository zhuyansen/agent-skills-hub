import { Link } from "react-router-dom";

interface Props {
  /** Size variant */
  size?: "sm" | "md" | "lg";
  /** Show text label ("Verified Creator") alongside icon */
  showLabel?: boolean;
  /** Tier for tooltip */
  tier?: "founding" | "pro" | "basic";
}

const TIER_LABEL = {
  founding: "Founding Verified Creator",
  pro: "Verified Creator · Pro",
  basic: "Verified Creator",
};

/**
 * Green checkmark badge for Hub-verified skill authors.
 * Clicking navigates to /verified-creator/ program info page.
 */
export function VerifiedBadge({
  size = "md",
  showLabel = false,
  tier = "basic",
}: Props) {
  const iconSize = size === "sm" ? 14 : size === "lg" ? 20 : 16;
  const textClass =
    size === "sm" ? "text-xs" : size === "lg" ? "text-sm" : "text-xs";
  const label = TIER_LABEL[tier];

  return (
    <Link
      to="/verified-creator/"
      title={`${label} — Click to learn about the program`}
      className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 transition-colors"
      onClick={(e) => e.stopPropagation()}
    >
      <svg
        width={iconSize}
        height={iconSize}
        viewBox="0 0 24 24"
        fill="currentColor"
        aria-label={label}
      >
        <path d="M12 2L4 6v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V6l-8-4zm-1.4 14.6L6 12l1.4-1.4 3.2 3.2 6.2-6.2L18.2 9l-7.6 7.6z" />
      </svg>
      {showLabel && (
        <span className={`${textClass} font-medium whitespace-nowrap`}>
          Verified Creator
        </span>
      )}
    </Link>
  );
}
