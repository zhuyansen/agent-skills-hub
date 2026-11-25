/**
 * What /analyzer/ shows after a scan (pages/AnalyzerPage.tsx). A scan makes two reads at once:
 * the catalog row (Supabase) and the live GitHub read (repo + README, unauthenticated: 60 calls
 * per IP per hour, two per scan, so a shared carrier IP runs out fast).
 *
 *   live   GitHub answered: the README is graded now, as before
 *   index  GitHub failed but the catalog holds a verdict: show that grade and say it is stored
 *   error  GitHub failed and there is no verdict to show
 *
 * Why: PostHog, 2026-11-18..25. Of 67 sessions that clicked "Scan Now", 48 got no result, 43 of
 * them on the repo prefilled from a skill page, which the catalog had already graded. Any failed
 * GitHub read ended the scan with an error.
 *
 * Test: node --test scripts/audit-outcome.test.mjs
 */

const VERDICTS = new Set(["safe", "caution", "unsafe", "reject"]);

/** Why the live read failed. `status` is the HTTP status, 0 when no response came back. */
export function githubFailureReason({ status, rateRemaining }) {
  if (status === 429 || (status === 403 && rateRemaining === "0")) return "rate_limited";
  if (status === 404) return "not_found";
  if (status === 0) return "network";
  return "github_error";
}

/** The catalog's grade when it is a real verdict ("unknown" means it had no README to grade). */
export function usableIndexedGrade(row) {
  const grade = row?.security_grade;
  return VERDICTS.has(grade) ? grade : null;
}

/** security_flags is JSON text in the catalog; accept an array too, read anything else as none. */
export function parseStoredFlags(raw) {
  let flags = raw;
  if (typeof raw === "string") {
    try {
      flags = JSON.parse(raw || "[]");
    } catch {
      return [];
    }
  }
  return Array.isArray(flags) ? flags.filter((f) => typeof f === "string") : [];
}

/**
 * live, index or error, from the settled GitHub read ({ ok } or { ok: false, status,
 * rateRemaining }) and the catalog row. A repo GitHub calls gone (404) keeps the error: its old
 * grade would describe something that no longer exists.
 */
export function auditOutcome(github, row) {
  if (github.ok) return { kind: "live" };
  const reason = githubFailureReason({ status: github.status ?? 0, rateRemaining: github.rateRemaining ?? null });
  if (reason !== "not_found" && usableIndexedGrade(row)) return { kind: "index", reason };
  return { kind: "error", reason };
}
