/**
 * Supabase list and search queries — the Explore list (sbFetchSkills), the
 * search box (sbQuickSearch) and the query helpers they share.
 * Extracted from supabaseClient.ts to keep file sizes under 800 lines. That
 * file re-exports both and imports SKILL_COLUMNS, skillsQuery and matchAuthor
 * from here; nothing here imports it back, so there is no import cycle.
 */
import { supabase } from "../lib/supabase";
import type { PaginatedSkills, Skill, SkillsQueryParams } from "../types/skill";

// Columns to SELECT for list queries (exclude readme_content to save bandwidth)
export const SKILL_COLUMNS = [
  "id",
  "repo_full_name",
  "repo_name",
  "repo_url",
  "repo_status",
  "description",
  "homepage_url",
  "author_name",
  "author_avatar_url",
  "author_followers",
  "stars",
  "forks",
  "open_issues",
  "total_issues",
  "total_commits",
  "language",
  "category",
  "topics",
  "license",
  "score",
  "star_momentum",
  "project_type",
  "last_commit_at",
  "created_at",
  "last_synced",
  "first_seen",
  "quality_completeness",
  "quality_clarity",
  "quality_specificity",
  "quality_examples",
  "quality_agent_readiness",
  "quality_score",
  "size_category",
  "repo_size_kb",
  "readme_size",
  "readme_structure_score",
  "platforms",
  "estimated_tokens",
  "security_grade",
  "is_official",
].join(",");

function ensureSupabase() {
  if (!supabase) throw new Error("Supabase not configured");
  return supabase;
}

// How a list reports its total (PostgREST's Prefer: count=...). "estimated"
// counts exactly up to db-max-rows (1,000) and gives the planner's estimate
// above that; "planned" always gives the estimate. Lists used "exact", which
// counted every match (up to all 250K rows) on each request and ran past
// anon's 3 s statement timeout: ~430 HTTP 500s a day (2026-10-27).
type CountMode = "estimated" | "planned";

export function skillsQuery(columns: string, count?: CountMode) {
  return ensureSupabase().from("skills").select(columns, { count });
}

type SkillsQuery = ReturnType<typeof skillsQuery>;

/**
 * Author logins are stored in GitHub's casing, which is what the site links
 * use, so an exact match is answered by the btree on author_name. The
 * case-insensitive match has no usable index (the trigram one was left invalid
 * by a failed build in June) and reads the whole table: callers fall back to
 * it only when the exact match finds nothing, e.g. for a hand-typed URL.
 */
export function matchAuthor(
  query: SkillsQuery,
  author: string,
  exact: boolean,
): SkillsQuery {
  return exact
    ? query.eq("author_name", author)
    : query.ilike("author_name", author);
}

// Han, kana and Hangul are written without spaces, so the full-text index
// can't find a word inside a sentence of them: those searches keep the
// substring match.
const UNSPACED_SCRIPT =
  /[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Hangul}]/u;
const WORD_PART = /[\p{L}\p{N}]+/gu;

/** "claude" → "claude:*", which also finds claudecode; "node.js" → "node:* & js:*". */
function prefixTsQuery(word: string): string {
  return (word.match(WORD_PART) ?? []).map((part) => `${part}:*`).join(" & ");
}

/**
 * Several words: full-text search on search_vector (GIN-indexed). One word:
 * the same index, matching whole words and word starts. A single word used to
 * be a substring match over four unindexed columns, which read the whole table
 * for a rare word (4.5 s for "godot") and timed out. Han/kana/Hangul words and
 * words with no letter or digit still get the substring match.
 */
function searchKind(search: string): "words" | "prefix" | "substring" {
  if (/\s/.test(search)) return "words";
  if (UNSPACED_SCRIPT.test(search) || !prefixTsQuery(search)) {
    return "substring";
  }
  return "prefix";
}

function substringSearch(query: SkillsQuery, search: string): SkillsQuery {
  const pat = `%${search}%`;
  return query.or(
    `repo_name.ilike.${pat},description.ilike.${pat},author_name.ilike.${pat},topics.ilike.${pat}`,
  );
}

function applySearch(query: SkillsQuery, search: string): SkillsQuery {
  const kind = searchKind(search);
  if (kind === "words") {
    return query.textSearch("search_vector", search, { type: "websearch" });
  }
  if (kind === "prefix") {
    return query.textSearch("search_vector", prefixTsQuery(search), {
      config: "english",
    });
  }
  return substringSearch(query, search);
}

const QUICK_SEARCH_COLUMNS =
  "id,repo_full_name,repo_name,repo_url,description,author_name,author_avatar_url,stars,score,category,language,platforms,size_category,repo_size_kb,author_followers,forks,open_issues,total_issues,total_commits,topics,license,star_momentum,project_type,last_commit_at,created_at,last_synced,quality_completeness,quality_clarity,quality_specificity,quality_examples,quality_agent_readiness,quality_score,readme_size,readme_structure_score,estimated_tokens,homepage_url";

/**
 * Search-as-you-type (header and hero search boxes): every word, the last one
 * half typed, as a word prefix on search_vector. This ran the substring match
 * on each keystroke, and a rare fragment ("amzo", "yamax") timed out: most of
 * the 500s left in the two hours after the list fix (2026-10-27).
 * Han/kana/Hangul input keeps the substring match.
 */
export async function sbQuickSearch(
  query: string,
  limit: number,
): Promise<Skill[]> {
  const search = query.trim();
  const words = UNSPACED_SCRIPT.test(search) ? "" : prefixTsQuery(search);
  const base = skillsQuery(QUICK_SEARCH_COLUMNS);
  const filtered = words
    ? base.textSearch("search_vector", words, { config: "english" })
    : substringSearch(base, search);
  const { data, error } = await filtered
    .order("score", { ascending: false })
    .limit(limit);
  if (error) throw new Error(error.message);
  return (data ?? []) as unknown as Skill[];
}

/** The substring search has no index: even a count capped at 1,000 can read
 *  the whole table for a rare word, so it gets the planner's estimate. */
function countMode(search: string): CountMode {
  return search && searchKind(search) === "substring"
    ? "planned"
    : "estimated";
}

// Quality tier filter (S/A/B/C/D checkboxes)
const QUALITY_TIER_FILTERS: Partial<Record<string, string>> = {
  S: "quality_score.gte.80",
  A: "and(quality_score.gte.65,quality_score.lt.80)",
  B: "and(quality_score.gte.50,quality_score.lt.65)",
  C: "and(quality_score.gte.35,quality_score.lt.50)",
  D: "quality_score.lt.35",
};

function applyQualityTiers(query: SkillsQuery, tiers: string): SkillsQuery {
  const conditions = tiers
    .split(",")
    .map((tier) => QUALITY_TIER_FILTERS[tier])
    .filter((condition): condition is string => condition !== undefined);
  return conditions.length > 0 ? query.or(conditions.join(",")) : query;
}

function applyFilters(
  query: SkillsQuery,
  params: SkillsQueryParams,
): SkillsQuery {
  let q = query;
  if (params.category) {
    // Support comma-separated categories (for layer filtering)
    const categories = params.category.split(",");
    q =
      categories.length > 1
        ? q.in("category", categories)
        : q.eq("category", params.category);
  }
  if (params.size_category) q = q.eq("size_category", params.size_category);
  if (params.platform) q = q.ilike("platforms", `%"${params.platform}"%`);
  if (params.min_stars) q = q.gte("stars", params.min_stars);
  return params.quality_tiers ? applyQualityTiers(q, params.quality_tiers) : q;
}

function toPage(
  items: Skill[],
  count: number | null,
  params: SkillsQueryParams,
): PaginatedSkills {
  const seen = (params.page - 1) * params.page_size + items.length;
  // An estimated total can be off either way; a page that isn't full settles it.
  const total =
    items.length < params.page_size ? seen : Math.max(count ?? 0, seen);
  return {
    items,
    total,
    page: params.page,
    page_size: params.page_size,
    total_pages: Math.max(1, Math.ceil(total / params.page_size)),
  };
}

async function fetchSkillsPage(
  params: SkillsQueryParams,
  exactAuthor: boolean,
): Promise<PaginatedSkills> {
  const search = params.search?.trim() ?? "";
  let query = applyFilters(
    skillsQuery(SKILL_COLUMNS, countMode(search)),
    params,
  );
  if (params.author) query = matchAuthor(query, params.author, exactAuthor);
  if (search) query = applySearch(query, search);
  const from = (params.page - 1) * params.page_size;
  const { data, count, error } = await query
    .order(params.sort_by, { ascending: params.sort_order === "asc" })
    .range(from, from + params.page_size - 1);
  if (error) throw new Error(error.message);
  return toPage((data ?? []) as unknown as Skill[], count, params);
}

export async function sbFetchSkills(
  params: SkillsQueryParams,
): Promise<PaginatedSkills> {
  const page = await fetchSkillsPage(params, true);
  // An /author/ URL typed in other casing finds nothing exactly (see matchAuthor).
  if (params.author && page.total === 0) return fetchSkillsPage(params, false);
  return page;
}
