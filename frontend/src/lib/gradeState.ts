/**
 * Why a row does or doesn't have a security grade — the same rule as
 * scripts/shared-utils.mjs `gradeState` and backend/app/services/readme_coverage.py.
 *
 *   graded       a rule verdict exists
 *   pending      README fetched, graded at the next sync (every 8 hours)
 *   no_readme    GitHub has no README, so it cannot be graded
 *   not_fetched  queued for the README backfill
 */
export type GradeState = "graded" | "pending" | "no_readme" | "not_fetched";

export function gradeState(s: {
  security_grade: string | null;
  readme_size?: number | null;
  readme_fetched_at?: string | null;
}): GradeState {
  if (s.security_grade && s.security_grade !== "unknown") return "graded";
  if ((s.readme_size ?? 0) > 0) return "pending";
  if (s.readme_fetched_at) return "no_readme";
  return "not_fetched";
}
