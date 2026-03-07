/**
 * Supabase direct client — replaces FastAPI endpoints when Supabase is available.
 * Uses PostgREST (via supabase-js) to query PostgreSQL views and tables.
 */
import { supabase } from "../lib/supabase";
import type {
  CategoryCount,
  PaginatedSkills,
  Skill,
  SkillDetail,
  SkillsQueryParams,
  Stats,
} from "../types/skill";
import type { Master } from "./client";

// Columns to SELECT for list queries (exclude readme_content to save bandwidth)
const SKILL_COLUMNS = [
  "id", "repo_full_name", "repo_name", "repo_url", "description", "homepage_url",
  "author_name", "author_avatar_url", "author_followers",
  "stars", "forks", "open_issues", "total_issues", "total_commits",
  "language", "category", "topics", "license",
  "score", "star_momentum", "project_type",
  "last_commit_at", "created_at", "last_synced",
  "quality_completeness", "quality_clarity", "quality_specificity", "quality_examples",
  "quality_agent_readiness", "quality_score",
  "size_category", "repo_size_kb", "readme_size", "readme_structure_score",
  "platforms", "estimated_tokens",
].join(",");

function ensureSupabase() {
  if (!supabase) throw new Error("Supabase not configured");
  return supabase;
}

export async function sbFetchSkills(params: SkillsQueryParams): Promise<PaginatedSkills> {
  const sb = ensureSupabase();
  let query = sb.from("skills").select(SKILL_COLUMNS, { count: "exact" });

  if (params.category) query = query.eq("category", params.category);
  if (params.size_category) query = query.eq("size_category", params.size_category);
  if (params.platform) query = query.ilike("platforms", `%"${params.platform}"%`);
  if (params.search) {
    const pat = `%${params.search}%`;
    query = query.or(`repo_name.ilike.${pat},description.ilike.${pat},author_name.ilike.${pat},topics.ilike.${pat}`);
  }

  const ascending = params.sort_order === "asc";
  query = query.order(params.sort_by, { ascending });

  const from = (params.page - 1) * params.page_size;
  const to = from + params.page_size - 1;
  query = query.range(from, to);

  const { data, count, error } = await query;
  if (error) throw new Error(error.message);

  const total = count ?? 0;
  return {
    items: (data ?? []) as Skill[],
    total,
    page: params.page,
    page_size: params.page_size,
    total_pages: Math.max(1, Math.ceil(total / params.page_size)),
  };
}

export async function sbFetchStats(): Promise<Stats> {
  const sb = ensureSupabase();
  const { data, error } = await sb.from("v_stats").select("*").single();
  if (error) throw new Error(error.message);

  // Also fetch categories
  const { data: cats, error: catErr } = await sb.from("v_categories").select("*");
  if (catErr) throw new Error(catErr.message);

  return {
    total_skills: data.total_skills,
    avg_score: data.avg_score,
    categories: (cats ?? []) as CategoryCount[],
    last_sync_at: data.last_sync_at,
    last_sync_status: data.last_sync_status,
  };
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
  return (data ?? []) as Skill[];
}

export async function sbFetchRising(_days = 7, limit = 10): Promise<Skill[]> {
  const sb = ensureSupabase();
  const { data, error } = await sb
    .from("v_rising")
    .select(SKILL_COLUMNS)
    .limit(limit);
  if (error) throw new Error(error.message);
  return (data ?? []) as Skill[];
}

export async function sbFetchTopRated(limit = 10): Promise<Skill[]> {
  const sb = ensureSupabase();
  const { data, error } = await sb
    .from("v_top_rated")
    .select(SKILL_COLUMNS)
    .limit(limit);
  if (error) throw new Error(error.message);
  return (data ?? []) as Skill[];
}

export async function sbFetchMostStarred(limit = 10): Promise<Skill[]> {
  const sb = ensureSupabase();
  const { data, error } = await sb
    .from("v_community_classics")
    .select(SKILL_COLUMNS)
    .limit(limit);
  if (error) throw new Error(error.message);
  return (data ?? []) as Skill[];
}

export async function sbFetchRecentlyUpdated(limit = 10): Promise<Skill[]> {
  const sb = ensureSupabase();
  const { data, error } = await sb
    .from("v_recently_updated")
    .select(SKILL_COLUMNS)
    .limit(limit);
  if (error) throw new Error(error.message);
  return (data ?? []) as Skill[];
}

export async function sbFetchSkillDetail(id: number): Promise<SkillDetail> {
  const sb = ensureSupabase();

  // Fetch skill
  const { data: skill, error } = await sb
    .from("skills")
    .select("*")
    .eq("id", id)
    .single();
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
      .select("id, repo_name, score")
      .in("id", ids);

    const othersMap = new Map((others ?? []).map((o) => [o.id, o]));
    for (const c of comps) {
      const other = othersMap.get(c.compatible_skill_id);
      if (other) {
        compatible_skills.push({
          skill_id: other.id,
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
    .select("*")
    .eq("repo_full_name", slug)
    .single();
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
      .select("id, repo_name, score")
      .in("id", ids);

    const othersMap = new Map((others ?? []).map((o) => [o.id, o]));
    for (const c of comps) {
      const other = othersMap.get(c.compatible_skill_id);
      if (other) {
        compatible_skills.push({
          skill_id: other.id,
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

export async function sbFetchLanguageStats(): Promise<{ language: string; count: number }[]> {
  const sb = ensureSupabase();
  const { data, error } = await sb.from("v_language_stats").select("*");
  if (error) throw new Error(error.message);
  return (data ?? []) as { language: string; count: number }[];
}

export async function sbFetchMasters(): Promise<Master[]> {
  const sb = ensureSupabase();
  const { data, error } = await sb.rpc("get_masters");
  if (error) throw new Error(error.message);

  // The function returns { masters: [...], emerging: [...] }
  const result = data as { masters: Master[]; emerging: Master[] };
  return [...(result.masters ?? []), ...(result.emerging ?? [])];
}

export async function sbFetchLastSyncAt(): Promise<string | null> {
  const sb = ensureSupabase();
  const { data, error } = await sb.rpc("get_last_sync_at");
  if (error) return null;
  return data as string | null;
}
