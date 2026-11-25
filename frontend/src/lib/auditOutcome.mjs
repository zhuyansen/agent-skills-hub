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

// GitHub says the repo is gone or blocked: an old verdict would describe something no one can
// install, so these keep the error. For a security grade, showing an error beats a stale "Safe".
const NO_FALLBACK = new Set(["not_found", "blocked"]);

/**
 * Why the live read failed. `status` is the HTTP status, 0 when no response came back. A 403 is a
 * rate limit only when GitHub says so (quota 0, or Retry-After on a secondary limit); with quota
 * left it is "Repository access blocked", like a 451 takedown.
 */
export function githubFailureReason({ status, rateRemaining, retryAfter = null }) {
  if (status === 429 || (status === 403 && (rateRemaining === "0" || retryAfter != null))) return "rate_limited";
  if (status === 404) return "not_found";
  if (status === 403 || status === 451) return "blocked";
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
 * rateRemaining, retryAfter }) and the catalog row. No fallback for a repo GitHub calls gone or
 * blocked, nor for one the catalog's liveness check marked gone (repo_status, migration 022).
 */
export function auditOutcome(github, row) {
  if (github.ok) return { kind: "live" };
  const reason = githubFailureReason({
    status: github.status ?? 0,
    rateRemaining: github.rateRemaining ?? null,
    retryAfter: github.retryAfter ?? null,
  });
  const gone = row?.repo_status === "gone";
  if (!NO_FALLBACK.has(reason) && !gone && usableIndexedGrade(row)) return { kind: "index", reason };
  return { kind: "error", reason };
}
