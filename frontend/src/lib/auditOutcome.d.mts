export type GitHubFailureReason = "rate_limited" | "not_found" | "blocked" | "network" | "github_error";

export type StoredVerdict = "safe" | "caution" | "unsafe" | "reject";

export interface GitHubFailure {
  status: number;
  rateRemaining: string | null;
  retryAfter?: string | null;
}

export type FailedRead = { ok: false } & Partial<GitHubFailure>;

export interface GradedRow {
  security_grade?: string | null;
  /** 'live' | 'gone' | 'unknown' (migration 022). */
  repo_status?: string | null;
}

/** After a failed read: the catalog's verdict stands in, or there is nothing to show. */
export type FailedOutcome =
  | { kind: "index"; reason: GitHubFailureReason }
  | { kind: "error"; reason: GitHubFailureReason };

export type AuditOutcome = { kind: "live" } | FailedOutcome;

export function githubFailureReason(failure: GitHubFailure): GitHubFailureReason;
export function usableIndexedGrade(row: GradedRow | null | undefined): StoredVerdict | null;
export function parseStoredFlags(raw: unknown): string[];
export function auditOutcome(github: { ok: true }, row: GradedRow | null): { kind: "live" };
export function auditOutcome(github: FailedRead, row: GradedRow | null): FailedOutcome;
