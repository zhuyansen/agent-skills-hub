/**
 * One /analyzer/ scan: the catalog row and the live GitHub read, fetched together, turned into
 * what the page shows. lib/auditOutcome.mjs decides which read wins and is unit-tested.
 *
 * The live read is unauthenticated (60 GitHub calls per IP per hour, two per scan). When it
 * fails and the catalog already graded the repo, the scan now shows that stored verdict instead
 * of an error: 43 of the 48 sessions whose scan failed 2026-11-18..25 were on such a repo.
 */
import { supabase } from "./supabase";
import {
  fetchGitHubRepo,
  GitHubReadError,
  scanReadme,
  storedScanResult,
  type ScanResult,
} from "../utils/securityScanner";
import { auditOutcome, parseStoredFlags, usableIndexedGrade } from "./auditOutcome.mjs";

export interface FullResult {
  repo: {
    full_name: string;
    stars: number;
    description: string;
    license: string | null;
    repo_url: string;
    category: string | null;
  };
  indexed: boolean;
  /** "index": the live GitHub read failed, so `scan` is the catalog's stored verdict. */
  source: "live" | "index";
  scan: ScanResult;
  quality: {
    score: number;
    completeness: number;
    clarity: number;
    specificity: number;
    examples: number;
    agent_readiness: number;
  } | null;
}

/** A scan that ended with nothing to show. `reason` is what analytics records. */
export class AuditFailure extends Error {
  reason: string;
  indexed: boolean;

  constructor(message: string, reason: string, indexed: boolean) {
    super(message);
    this.name = "AuditFailure";
    this.reason = reason;
    this.indexed = indexed;
  }
}

const INDEX_COLUMNS = [
  "category", "quality_score", "quality_completeness", "quality_clarity", "quality_specificity",
  "quality_examples", "quality_agent_readiness", "security_grade", "security_flags",
  "stars", "description", "license", "repo_url", "author_name", "repo_status",
].join(",");

interface IndexRow {
  category: string | null;
  quality_score: number | null;
  quality_completeness: number | null;
  quality_clarity: number | null;
  quality_specificity: number | null;
  quality_examples: number | null;
  quality_agent_readiness: number | null;
  security_grade: string | null;
  security_flags: unknown;
  stars: number | null;
  description: string | null;
  license: string | null;
  repo_url: string | null;
  author_name: string | null;
  /** 'live' | 'gone' | 'unknown' (migration 022); a gone repo never gets the stored verdict. */
  repo_status: string | null;
}

type GitHubRepo = Awaited<ReturnType<typeof fetchGitHubRepo>>;
type GitHubRead =
  | { ok: true; repo: GitHubRepo }
  | { ok: false; status: number; rateRemaining: string | null; retryAfter: string | null; message: string };

async function readIndex(fullName: string): Promise<IndexRow | null> {
  if (!supabase) return null;
  try {
    const { data } = await supabase
      .from("skills")
      .select(INDEX_COLUMNS)
      .eq("repo_full_name", fullName)
      .maybeSingle();
    return (data as IndexRow | null) ?? null;
  } catch {
    return null; // the catalog only adds to a scan; the live read still runs without it
  }
}

async function readGitHub(fullName: string): Promise<GitHubRead> {
  try {
    return { ok: true, repo: await fetchGitHubRepo(fullName) };
  } catch (err) {
    const failed = err instanceof GitHubReadError ? err : null;
    return {
      ok: false,
      status: failed?.status ?? 0, // fetch() rejects without a status when the network fails
      rateRemaining: failed?.rateRemaining ?? null,
      retryAfter: failed?.retryAfter ?? null,
      message: err instanceof Error ? err.message : "Analysis failed",
    };
  }
}

function qualityOf(row: IndexRow): FullResult["quality"] {
  return {
    score: row.quality_score || 0,
    completeness: row.quality_completeness || 0,
    clarity: row.quality_clarity || 0,
    specificity: row.quality_specificity || 0,
    examples: row.quality_examples || 0,
    agent_readiness: row.quality_agent_readiness || 0,
  };
}

/** The catalog's verdict as a ScanResult, or null when it holds none worth showing. */
function storedScan(row: IndexRow | null, author: string, stars: number, license: string | null): ScanResult | null {
  const grade = usableIndexedGrade(row);
  if (!row || !grade) return null;
  return storedScanResult(grade, parseStoredFlags(row.security_flags), author, stars, license);
}

function liveResult(fullName: string, gh: GitHubRepo, row: IndexRow | null): FullResult {
  const scan = scanReadme(gh.readme, gh.author, gh.stars, gh.license, {
    repoFullName: fullName,
    homepage: gh.homepage,
  });
  // No README came back (none, or its call hit the rate limit): the catalog's verdict stands in.
  const stored = gh.readme ? null : storedScan(row, gh.author, gh.stars, gh.license);
  return {
    repo: {
      full_name: fullName,
      stars: gh.stars,
      description: gh.description,
      license: gh.license,
      repo_url: gh.repoUrl,
      category: row?.category ?? null,
    },
    indexed: row !== null,
    source: "live",
    scan: stored ?? scan,
    quality: row ? qualityOf(row) : null,
  };
}

function indexResult(fullName: string, row: IndexRow): FullResult | null {
  const stars = row.stars ?? 0;
  const license = row.license || null;
  const scan = storedScan(row, row.author_name || fullName.split("/")[0], stars, license);
  if (!scan) return null;
  return {
    repo: {
      full_name: fullName,
      stars,
      description: row.description ?? "",
      license,
      repo_url: row.repo_url || `https://github.com/${fullName}`,
      category: row.category,
    },
    indexed: true,
    source: "index",
    scan,
    quality: qualityOf(row),
  };
}

/** Scan `owner/repo`. Throws AuditFailure when there is nothing to show. */
export async function runAudit(fullName: string): Promise<{ result: FullResult; liveError?: string }> {
  const [row, github] = await Promise.all([readIndex(fullName), readGitHub(fullName)]);
  if (github.ok) return { result: liveResult(fullName, github.repo, row) };
  const outcome = auditOutcome(github, row);
  const stored = outcome.kind === "index" && row ? indexResult(fullName, row) : null;
  if (stored) return { result: stored, liveError: outcome.reason };
  throw new AuditFailure(github.message, outcome.reason, row !== null);
}
