/**
 * Supabase direct client — replaces FastAPI endpoints when Supabase is available.
 * Uses PostgREST (via supabase-js) to query PostgreSQL views and tables.
 */
import { supabase } from "../lib/supabase";
import type {
  CategoryCount,
  LandingData,
  PaginatedSkills,
  Skill,
  SkillDetail,
  SkillsQueryParams,
  Stats,
} from "../types/skill";
import type { Master } from "./client";

// Columns to SELECT for list queries (exclude readme_content to save bandwidth)
const SKILL_COLUMNS = [
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

// Columns for one skill's detail view: the list set plus the two fields only
// the detail view reads (lib/gradeState.ts, AuditVerdictCard). Not select("*"):
// that also returns readme_content and readme_search_vector, which nothing in
// the frontend reads. With them a row was 36-40 KB on the wire (15-18 KB
// gzipped), without them ~1.5 KB (2026-10-16), on every skill page load, and
// crawlers make most of those loads.
const SKILL_DETAIL_COLUMNS = `${SKILL_COLUMNS},readme_fetched_at,security_flags`;

function ensureSupabase() {
  if (!supabase) throw new Error("Supabase not configured");
  return supabase;
}

/** Simple retry wrapper for flaky network calls */
async function withRetry<T>(
  fn: () => Promise<T>,
  retries = 1,
  delay = 1000,
): Promise<T> {
  try {
    return await fn();
  } catch (err) {
    if (retries <= 0) throw err;
    await new Promise((r) => setTimeout(r, delay));
    return withRetry(fn, retries - 1, delay);
  }
}

// How long a shared request's result is reused. Sync runs every 8 hours, so a
// minute of reuse never serves stale data; it only collapses duplicates.
const SHARED_REUSE_MS = 60_000;

/**
 * Collapse concurrent identical requests into one. A page mounts the same data
 * hook several times — Home alone mounts useStats three times — and each
 * instance used to fire its own request. Crawlers make that expensive: they run
 * our JS in a fresh profile every session, so every visit is a cold cache
 * (43K automated sessions in 28 days, measured 2026-09-17). A failed request is
 * dropped at once so the next caller retries instead of inheriting the error.
 */
function shareRequest<T>(fetcher: () => Promise<T>): () => Promise<T> {
  let entry: { startedAt: number; result: Promise<T> } | null = null;
  return () => {
    const now = Date.now();
    if (!entry || now - entry.startedAt >= SHARED_REUSE_MS) {
      const result = fetcher();
      entry = { startedAt: now, result };
      result.catch(() => {
        if (entry?.result === result) entry = null;
      });
    }
    return entry.result;
  };
}

export interface OrgAuditRow {
  repo_full_name: string;
  repo_name: string;
  security_grade: string | null;
  quality_score: number | null;
  stars: number;
  category: string | null;
}

const ORG_AUDIT_COLUMNS =
  "repo_full_name,repo_name,security_grade,quality_score,stars,category";
const ORG_AUDIT_LIMIT = 500;

// How a list reports its total (PostgREST's Prefer: count=...). "estimated"
// counts exactly up to db-max-rows (1,000) and gives the planner's estimate
// above that; "planned" always gives the estimate. Lists used "exact", which
// counted every match (up to all 250K rows) on each request and ran past
// anon's 3 s statement timeout: ~430 HTTP 500s a day (2026-10-27).
type CountMode = "estimated" | "planned";

function skillsQuery(columns: string, count?: CountMode) {
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
function matchAuthor(
  query: SkillsQuery,
  author: string,
  exact: boolean,
): SkillsQuery {
  return exact
    ? query.eq("author_name", author)
    : query.ilike("author_name", author);
}

/**
 * Batch security audit for one GitHub owner. Reads stored grades straight from
 * the index (see matchAuthor), with no GitHub API calls and no 60-req/hr rate
 * limit (the reason a live per-repo scan can't do "audit my whole org"). Every
 * grade returned here is also public on that skill's own page; the batch view
 * is a convenience, not privileged data — which is why the Pro gate is
 * honor-system, not a hard wall.
 */
export async function sbFetchOrgAudit(owner: string): Promise<OrgAuditRow[]> {
  const clean = owner.trim().replace(/^@/, "").replace(/\/.*$/, "");
  if (!clean) return [];
  return withRetry(async () => {
    const rows = await fetchOrgAuditRows(clean, true);
    return rows.length > 0 ? rows : fetchOrgAuditRows(clean, false);
  });
}

async function fetchOrgAuditRows(
  owner: string,
  exact: boolean,
): Promise<OrgAuditRow[]> {
  const query = matchAuthor(skillsQuery(ORG_AUDIT_COLUMNS), owner, exact);
  const { data, error } = await query
    .neq("repo_status", "gone")
    .order("stars", { ascending: false })
    .limit(ORG_AUDIT_LIMIT);
  if (error) throw error;
  return (data ?? []) as unknown as OrgAuditRow[];
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
  const pat = `%${search}%`;
  return query.or(
    `repo_name.ilike.${pat},description.ilike.${pat},author_name.ilike.${pat},topics.ilike.${pat}`,
  );
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

/** Fetch skills by a list of ids (for the favorites collection page). Order is
 *  not guaranteed by Postgres — callers re-order client-side if needed. */
export async function sbFetchSkillsByIds(ids: number[]): Promise<Skill[]> {
  if (!ids.length) return [];
  const sb = ensureSupabase();
  const { data, error } = await sb
    .from("skills")
    .select(SKILL_COLUMNS)
    .in("id", ids);
  if (error) throw new Error(error.message);
  return (data ?? []) as unknown as Skill[];
}

export async function sbFetchStats(): Promise<Stats> {
  // v_stats aggregates COUNT(*) + COUNT(DISTINCT category) + AVG over all 191K
  // rows of a table wide with readme_content, and now exceeds the statement
  // timeout (57014). The header calls this on every page, so a failing query
  // here retried per mounted component was ~4 dead queries a page view.
  // get_landing_data() serves the same five numbers from the cached row that
  // migration 014 added, and already folds categories into stats.
  return (await sbFetchLandingData()).stats;
}

export async function sbFetchCategories(): Promise<CategoryCount[]> {
  const sb = ensureSupabase();
  const { data, error } = await sb.from("v_categories").select("*");
  if (error) throw new Error(error.message);
  return (data ?? []) as CategoryCount[];
}

export async function sbFetchTrending(limit = 10): Promise<Skill[]> {
  const sb = ensureSupabase();
  const { data, error } = await sb
    .from("v_trending")
    .select(SKILL_COLUMNS)
    .limit(limit);
  if (error) throw new Error(error.message);
  return (data ?? []) as unknown as Skill[];
}

export async function sbFetchRising(_days = 7, limit = 10): Promise<Skill[]> {
  const sb = ensureSupabase();
  const { data, error } = await sb
    .from("v_rising")
    .select(SKILL_COLUMNS)
    .limit(limit);
  if (error) throw new Error(error.message);
  return (data ?? []) as unknown as Skill[];
}

export async function sbFetchTopRated(limit = 10): Promise<Skill[]> {
  const sb = ensureSupabase();

  // Try the v_top_rated view first (filters WHERE score > 0)
  const { data, error } = await sb
    .from("v_top_rated")
    .select(SKILL_COLUMNS)
    .limit(limit);

  if (!error && data && data.length > 0) {
    return data as unknown as Skill[];
  }

  // Fallback: query skills table directly using quality_score
  const { data: fallbackData, error: fallbackError } = await sb
    .from("skills")
    .select(SKILL_COLUMNS)
    .gt("quality_score", 0)
    .order("quality_score", { ascending: false })
    .limit(limit);

  if (fallbackError) throw new Error(fallbackError.message);

  // Map quality_score to score so the UI displays it correctly
  const skills = (fallbackData ?? []) as unknown as Skill[];
  return skills.map((s) => ({
    ...s,
    score: s.score && s.score > 0 ? s.score : (s.quality_score ?? 0),
  }));
}

export async function sbFetchMostStarred(limit = 10): Promise<Skill[]> {
  const sb = ensureSupabase();
  const { data, error } = await sb
    .from("v_community_classics")
    .select(SKILL_COLUMNS)
    .limit(limit);
  if (error) throw new Error(error.message);
  return (data ?? []) as unknown as Skill[];
}

export async function sbFetchRecentlyUpdated(limit = 10): Promise<Skill[]> {
  const sb = ensureSupabase();
  const { data, error } = await sb
    .from("v_recently_updated")
    .select(SKILL_COLUMNS)
    .limit(limit);
  if (error) throw new Error(error.message);
  return (data ?? []) as unknown as Skill[];
}

export async function sbFetchSkillDetail(id: number): Promise<SkillDetail> {
  const sb = ensureSupabase();

  // Fetch skill
  const { data: skill, error } = await sb
    .from("skills")
    .select(SKILL_DETAIL_COLUMNS)
    .eq("id", id)
    .single<Skill>();
  if (error) throw new Error(error.message);

  // Fetch compositions
  const { data: comps } = await sb
    .from("skill_compositions")
    .select("compatible_skill_id, compatibility_score, reason")
    .eq("skill_id", id)
    .order("compatibility_score", { ascending: false })
    .limit(5);

  const compatible_skills = [];
  if (comps && comps.length > 0) {
    const ids = comps.map((c) => c.compatible_skill_id);
    const { data: others } = await sb
      .from("skills")
      .select("id, repo_full_name, repo_name, score")
      .in("id", ids);

    const othersMap = new Map((others ?? []).map((o) => [o.id, o]));
    for (const c of comps) {
      const other = othersMap.get(c.compatible_skill_id);
      if (other) {
        compatible_skills.push({
          skill_id: other.id,
          repo_full_name: other.repo_full_name,
          skill_name: other.repo_name,
          skill_score: other.score ?? 0,
          compatibility_score: c.compatibility_score,
          reason: c.reason,
        });
      }
    }
  }

  return { ...skill, compatible_skills } as SkillDetail;
}

export async function sbFetchSkillBySlug(slug: string): Promise<SkillDetail> {
  const sb = ensureSupabase();

  // slug = "owner/repo" = repo_full_name
  const { data: skill, error } = await sb
    .from("skills")
    .select(SKILL_DETAIL_COLUMNS)
    .eq("repo_full_name", slug)
    .single<Skill>();
  if (error) throw new Error(error.message);

  // Fetch compositions
  const { data: comps } = await sb
    .from("skill_compositions")
    .select("compatible_skill_id, compatibility_score, reason")
    .eq("skill_id", skill.id)
    .order("compatibility_score", { ascending: false })
    .limit(5);

  const compatible_skills = [];
  if (comps && comps.length > 0) {
    const ids = comps.map((c) => c.compatible_skill_id);
    const { data: others } = await sb
      .from("skills")
      .select("id, repo_full_name, repo_name, score")
      .in("id", ids);

    const othersMap = new Map((others ?? []).map((o) => [o.id, o]));
    for (const c of comps) {
      const other = othersMap.get(c.compatible_skill_id);
      if (other) {
        compatible_skills.push({
          skill_id: other.id,
          repo_full_name: other.repo_full_name,
          skill_name: other.repo_name,
          skill_score: other.score ?? 0,
          compatibility_score: c.compatibility_score,
          reason: c.reason,
        });
      }
    }
  }

  return { ...skill, compatible_skills } as SkillDetail;
}

export async function sbFetchLanguageStats(): Promise<
  { language: string; count: number }[]
> {
  const sb = ensureSupabase();
  const { data, error } = await sb.from("v_language_stats").select("*");
  if (error) throw new Error(error.message);
  return (data ?? []) as { language: string; count: number }[];
}

// ═══ Landing page single-RPC optimization ═══

// Home mounts useLandingData, and useStats (five mounts) reads the same RPC, so a
// cold visit fetched this 74KB payload six times before it was shared.
export const sbFetchLandingData = shareRequest(fetchLandingData);

async function fetchLandingData(): Promise<LandingData> {
  return withRetry(async () => {
    const sb = ensureSupabase();
    const { data, error } = await sb.rpc("get_landing_data");
    if (error) throw new Error(error.message);

    interface RpcLandingData {
      stats?: {
        total_skills?: number;
        avg_score?: number;
        last_sync_at?: string | null;
        last_sync_status?: string | null;
      };
      categories?: CategoryCount[];
      trending?: Skill[];
      rising?: Skill[];
      top_rated?: Skill[];
      hall_of_fame?: Skill[];
      recently_updated?: Skill[];
      languages?: { language: string; count: number }[];
    }
    const d = data as RpcLandingData;
    return {
      stats: {
        total_skills: d.stats?.total_skills ?? 0,
        avg_score: d.stats?.avg_score ?? 0,
        categories: (d.categories ?? []) as CategoryCount[],
        last_sync_at: d.stats?.last_sync_at ?? null,
        last_sync_status: d.stats?.last_sync_status ?? null,
      },
      trending: (d.trending ?? []) as Skill[],
      rising: (d.rising ?? []) as Skill[],
      top_rated: (d.top_rated ?? []) as Skill[],
      hall_of_fame: (d.hall_of_fame ?? []) as Skill[],
      recently_updated: (d.recently_updated ?? []) as Skill[],
      languages: (d.languages ?? []) as { language: string; count: number }[],
      generated_at: new Date().toISOString(),
    };
  });
}

// ═══ New This Week (first_seen within 7 days) ═══

export async function sbFetchNewThisWeek(limit = 10): Promise<Skill[]> {
  const sb = ensureSupabase();
  const sevenDaysAgo = new Date(
    Date.now() - 7 * 24 * 60 * 60 * 1000,
  ).toISOString();
  const { data, error } = await sb
    .from("skills")
    .select(SKILL_COLUMNS)
    .gte("first_seen", sevenDaysAgo)
    .order("stars", { ascending: false })
    .limit(limit);
  if (error) throw new Error(error.message);
  return (data ?? []) as unknown as Skill[];
}

// ═══ Weekly Trending History ═══

export async function sbFetchTrendingWeeks(): Promise<
  import("../types/skill").TrendingWeek[]
> {
  const sb = ensureSupabase();
  const { data, error } = await sb.rpc("get_trending_weeks");
  if (error) throw new Error(error.message);
  return (data ?? []) as import("../types/skill").TrendingWeek[];
}

export async function sbFetchTrendingHistory(
  weekStart: string,
): Promise<import("../types/skill").WeeklyTrendingEntry[]> {
  const sb = ensureSupabase();
  const { data, error } = await sb.rpc("get_trending_history", {
    p_week_start: weekStart,
  });
  if (error) throw new Error(error.message);
  return (data ?? []) as import("../types/skill").WeeklyTrendingEntry[];
}

// ═══ Organization Builders (aggregated from skills table) ═══

export interface OrgBuilder {
  github: string;
  name: string;
  avatar_url: string;
  repo_count: number;
  total_stars: number;
  top_repos: {
    id: number;
    repo_name: string;
    repo_full_name: string;
    repo_url: string;
    description: string;
    stars: number;
    score: number;
    category: string;
  }[];
}

export async function sbFetchOrgBuilders(): Promise<OrgBuilder[]> {
  const sb = ensureSupabase();
  const { data, error } = await sb.rpc("get_org_builders");
  if (error) throw new Error(error.message);

  const orgs = (data ?? []) as Partial<OrgBuilder>[];
  return orgs.map((o) => ({
    github: o.github ?? "",
    name: o.name ?? "",
    avatar_url:
      o.avatar_url || `https://avatars.githubusercontent.com/${o.github}`,
    repo_count: o.repo_count ?? 0,
    total_stars: o.total_stars ?? 0,
    top_repos: (o.top_repos || []).slice(0, 5),
  }));
}

export async function sbFetchMasters(): Promise<Master[]> {
  const sb = ensureSupabase();
  const { data, error } = await sb.rpc("get_masters");
  if (error) throw new Error(error.message);

  // The RPC returns { masters: [...], emerging: [...] } with stats but missing
  // avatar_url, top_repos, repo_count — we need to enrich the data.
  interface RpcMaster {
    github: string;
    name: string;
    x_handle: string | null;
    bio: string | null;
    tags: string[];
    github_aliases: string[];
    x_followers: number;
    x_posts_count: number;
    x_notes: string | null;
    total_stars: number;
    skill_count: number;
    avg_score: number;
    is_verified: boolean;
  }

  const result = data as { masters: RpcMaster[]; emerging: RpcMaster[] };
  const allRpc = [...(result.masters ?? []), ...(result.emerging ?? [])];

  // Fallback to hardcoded data when the skill_masters table is empty
  if (allRpc.length === 0) {
    return getFallbackMasters();
  }

  // Collect all github usernames (+ aliases) to fetch their top repos
  const githubNames: string[] = [];
  for (const m of allRpc) {
    githubNames.push(m.github);
    if (m.github_aliases) {
      for (const alias of m.github_aliases) githubNames.push(alias);
    }
  }

  // Fetch top repos for all masters in one query
  const { data: repos } = await sb
    .from("skills")
    .select(
      "id,repo_name,repo_full_name,repo_url,description,stars,score,category,author_name",
    )
    .in("author_name", githubNames)
    .order("stars", { ascending: false })
    .limit(100);

  // Group repos by author
  const reposByAuthor = new Map<string, typeof repos>();
  for (const r of repos ?? []) {
    const key = r.author_name?.toLowerCase();
    if (!reposByAuthor.has(key)) reposByAuthor.set(key, []);
    reposByAuthor.get(key)!.push(r);
  }

  // Enrich masters
  const enriched: Master[] = allRpc.map((m) => {
    const authorKeys = [m.github, ...(m.github_aliases || [])];
    const topRepos: Master["top_repos"] = [];
    for (const key of authorKeys) {
      const reps = reposByAuthor.get(key.toLowerCase()) ?? [];
      for (const r of reps) {
        if (topRepos.length >= 5) break;
        topRepos.push({
          id: r.id,
          repo_name: r.repo_name,
          repo_full_name: r.repo_full_name,
          repo_url: r.repo_url,
          description: r.description || "",
          stars: r.stars,
          score: r.score ?? 0,
          category: r.category,
        });
      }
    }

    return {
      github: m.github,
      name: m.name,
      x_handle: m.x_handle,
      bio: m.bio,
      tags: Array.isArray(m.tags) ? m.tags : [],
      github_aliases: m.github_aliases ?? [],
      is_verified: !!m.is_verified,
      avatar_url: `https://avatars.githubusercontent.com/${m.github}`,
      repo_count: m.skill_count,
      total_stars: m.total_stars,
      x_followers: m.x_followers,
      x_posts_count: m.x_posts_count,
      x_verified_at: null,
      x_notes: m.x_notes,
      top_repos: topRepos,
      discovered: !m.is_verified,
    };
  });

  return enriched;
}

function getFallbackMasters(): Master[] {
  const hardcodedMasters: Master[] = [
    {
      github: "joeseesun",
      name: "Joe See Sun",
      x_handle: "joeseesun",
      bio: "Prolific skill builder, author of qiaomu design tools",
      tags: ["skill-builder", "design", "productivity"],
      avatar_url: "https://avatars.githubusercontent.com/u/joeseesun",
      repo_count: 8,
      total_stars: 2000,
      x_followers: 5000,
      x_posts_count: 200,
      x_verified_at: null,
      x_notes: null,
      top_repos: [
        {
          id: 1,
          repo_name: "qiaomu-design-advisor",
          repo_full_name: "joeseesun/qiaomu-design-advisor",
          repo_url: "https://github.com/joeseesun/qiaomu-design-advisor",
          description: "UI/UX design advisor",
          stars: 500,
          score: 56,
          category: "claude-skill",
        },
      ],
      discovered: false,
    },
    {
      github: "Panniantong",
      name: "Panniantong",
      x_handle: null,
      bio: "Agent-Reach creator",
      tags: ["agent-tool", "twitter"],
      avatar_url: "https://avatars.githubusercontent.com/u/Panniantong",
      repo_count: 3,
      total_stars: 800,
      x_followers: 0,
      x_posts_count: 0,
      x_verified_at: null,
      x_notes: null,
      top_repos: [
        {
          id: 2,
          repo_name: "Agent-Reach",
          repo_full_name: "Panniantong/Agent-Reach",
          repo_url: "https://github.com/Panniantong/Agent-Reach",
          description: "Read X content",
          stars: 400,
          score: 50,
          category: "agent-tool",
        },
      ],
      discovered: false,
    },
  ];

  const hardcodedEmerging: Master[] = [
    {
      github: "JimLiu",
      name: "JimLiu",
      x_handle: "dotey",
      bio: null,
      tags: ["content-creation"],
      avatar_url: "https://avatars.githubusercontent.com/u/JimLiu",
      repo_count: 2,
      total_stars: 600,
      x_followers: 0,
      x_posts_count: 0,
      x_verified_at: null,
      x_notes: null,
      top_repos: [
        {
          id: 3,
          repo_name: "baoyu-skills",
          repo_full_name: "JimLiu/baoyu-skills",
          repo_url: "https://github.com/JimLiu/baoyu-skills",
          description: "Content creation skills",
          stars: 300,
          score: 45,
          category: "claude-skill",
        },
      ],
      discovered: true,
    },
  ];

  return [...hardcodedMasters, ...hardcodedEmerging];
}

// Every useCachedQuery instance probes this before deciding whether to refetch,
// and a page mounts about six of them: six identical RPCs per page view.
export const sbFetchLastSyncAt = shareRequest(probeLastSyncAt);

async function probeLastSyncAt(): Promise<string | null> {
  const sb = ensureSupabase();
  const { data, error } = await sb.rpc("get_last_sync_at");
  if (error) return null;
  return data as string | null;
}

// Write operations moved to ./supabaseWrite.ts
export {
  sbSubmitSkill,
  sbSubscribe,
  sbVerifyEmail,
  sbSubmitMasterApplication,
  sbSubmitVerifiedCreatorApplication,
  sbSubmitWorkflow,
  sbAdminAction,
} from "./supabaseWrite";
export type { VerifiedCreatorApplicationPayload } from "./supabaseWrite";
