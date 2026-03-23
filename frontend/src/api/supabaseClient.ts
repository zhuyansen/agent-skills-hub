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
  "id", "repo_full_name", "repo_name", "repo_url", "description", "homepage_url",
  "author_name", "author_avatar_url", "author_followers",
  "stars", "forks", "open_issues", "total_issues", "total_commits",
  "language", "category", "topics", "license",
  "score", "star_momentum", "project_type",
  "last_commit_at", "created_at", "last_synced", "first_seen",
  "quality_completeness", "quality_clarity", "quality_specificity", "quality_examples",
  "quality_agent_readiness", "quality_score",
  "size_category", "repo_size_kb", "readme_size", "readme_structure_score",
  "platforms", "estimated_tokens",
  "security_grade",
  "is_official",
].join(",");

function ensureSupabase() {
  if (!supabase) throw new Error("Supabase not configured");
  return supabase;
}

/** Simple retry wrapper for flaky network calls */
async function withRetry<T>(fn: () => Promise<T>, retries = 1, delay = 1000): Promise<T> {
  try {
    return await fn();
  } catch (err) {
    if (retries <= 0) throw err;
    await new Promise((r) => setTimeout(r, delay));
    return withRetry(fn, retries - 1, delay);
  }
}

export async function sbFetchSkills(params: SkillsQueryParams): Promise<PaginatedSkills> {
  const sb = ensureSupabase();
  let query = sb.from("skills").select(SKILL_COLUMNS, { count: "exact" });

  if (params.category) {
    // Support comma-separated categories (for layer filtering)
    if (params.category.includes(",")) {
      query = query.in("category", params.category.split(","));
    } else {
      query = query.eq("category", params.category);
    }
  }
  if (params.size_category) query = query.eq("size_category", params.size_category);
  if (params.platform) query = query.ilike("platforms", `%"${params.platform}"%`);
  if (params.search) {
    const trimmed = params.search.trim();
    const words = trimmed.split(/\s+/).filter(Boolean);
    // Use Full Text Search for multi-word queries; ILIKE fallback for short/single-char queries
    if (words.length >= 2) {
      query = query.textSearch("search_vector", trimmed, { type: "websearch" });
    } else {
      const pat = `%${trimmed}%`;
      query = query.or(`repo_name.ilike.${pat},description.ilike.${pat},author_name.ilike.${pat},topics.ilike.${pat}`);
    }
  }

  // Quality tier filter (S/A/B/C/D checkboxes)
  if (params.quality_tiers) {
    const tiers = params.quality_tiers.split(",");
    const conditions: string[] = [];
    for (const tier of tiers) {
      switch (tier) {
        case "S": conditions.push("quality_score.gte.80"); break;
        case "A": conditions.push("and(quality_score.gte.65,quality_score.lt.80)"); break;
        case "B": conditions.push("and(quality_score.gte.50,quality_score.lt.65)"); break;
        case "C": conditions.push("and(quality_score.gte.35,quality_score.lt.50)"); break;
        case "D": conditions.push("quality_score.lt.35"); break;
      }
    }
    if (conditions.length > 0) {
      query = query.or(conditions.join(","));
    }
  }
  // Min stars filter
  if (params.min_stars) {
    query = query.gte("stars", params.min_stars);
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
    items: (data ?? []) as unknown as Skill[],
    total,
    page: params.page,
    page_size: params.page_size,
    total_pages: Math.max(1, Math.ceil(total / params.page_size)),
  };
}

export async function sbFetchStats(): Promise<Stats> {
  return withRetry(async () => {
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
  });
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
    score: s.score && s.score > 0 ? s.score : (s as any).quality_score ?? 0,
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

// ═══ Landing page single-RPC optimization ═══

export async function sbFetchLandingData(): Promise<LandingData> {
  return withRetry(async () => {
    const sb = ensureSupabase();
    const { data, error } = await sb.rpc("get_landing_data");
    if (error) throw new Error(error.message);

    const d = data as any;
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
  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
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

export async function sbFetchTrendingWeeks(): Promise<import("../types/skill").TrendingWeek[]> {
  const sb = ensureSupabase();
  const { data, error } = await sb.rpc("get_trending_weeks");
  if (error) throw new Error(error.message);
  return (data ?? []) as import("../types/skill").TrendingWeek[];
}

export async function sbFetchTrendingHistory(weekStart: string): Promise<import("../types/skill").WeeklyTrendingEntry[]> {
  const sb = ensureSupabase();
  const { data, error } = await sb.rpc("get_trending_history", { p_week_start: weekStart });
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

  const orgs = (data ?? []) as any[];
  return orgs.map((o) => ({
    github: o.github,
    name: o.name,
    avatar_url: o.avatar_url || `https://avatars.githubusercontent.com/${o.github}`,
    repo_count: o.repo_count,
    total_stars: o.total_stars,
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
    .select("id,repo_name,repo_full_name,repo_url,description,stars,score,category,author_name")
    .in("author_name", githubNames)
    .order("stars", { ascending: false })
    .limit(100);

  // Group repos by author
  const reposByAuthor = new Map<string, typeof repos>();
  for (const r of (repos ?? [])) {
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

export async function sbFetchLastSyncAt(): Promise<string | null> {
  const sb = ensureSupabase();
  const { data, error } = await sb.rpc("get_last_sync_at");
  if (error) return null;
  return data as string | null;
}

// ═══ Write operations (Supabase direct) ═══

export async function sbSubmitSkill(
  repoUrl: string,
): Promise<{ status: string; message: string; skill_id?: number }> {
  const sb = ensureSupabase();

  // Extract owner/repo from URL
  const match = repoUrl.match(/github\.com\/([^/]+\/[^/]+)/);
  if (!match) {
    return { status: "error", message: "Invalid GitHub URL" };
  }
  const fullName = match[1].replace(/\.git$/, "");

  // Check if already in skills table
  const { data: existing } = await sb
    .from("skills")
    .select("id")
    .eq("repo_full_name", fullName)
    .maybeSingle();

  if (existing) {
    return {
      status: "already_tracked",
      message: "This skill is already tracked!",
      skill_id: existing.id,
    };
  }

  // Check if already submitted in extra_repos (may fail if SELECT RLS is not set)
  try {
    const { data: submitted } = await sb
      .from("extra_repos")
      .select("id, status")
      .eq("full_name", fullName)
      .maybeSingle();

    if (submitted) {
      return {
        status: "already_submitted",
        message: `This repo has already been submitted (status: ${submitted.status || "pending"})`,
      };
    }
  } catch {
    // SELECT may be blocked by RLS — skip dedup check, INSERT will handle unique constraint
  }

  // Insert new submission
  const { error } = await sb.from("extra_repos").insert({
    full_name: fullName,
    is_active: false,
    status: "pending",
    submitted_by: "community",
  });

  if (error) {
    // Unique constraint violation = already submitted
    if (error.code === "23505") {
      return { status: "already_submitted", message: "This repo has already been submitted" };
    }
    return { status: "error", message: error.message };
  }

  return {
    status: "submitted",
    message: "Submitted successfully! It will be reviewed by our team.",
  };
}

// Generate a random verification token
function generateToken(): string {
  const chars = "abcdefghijklmnopqrstuvwxyz0123456789";
  let token = "";
  const arr = new Uint8Array(32);
  crypto.getRandomValues(arr);
  for (const byte of arr) {
    token += chars[byte % chars.length];
  }
  return token;
}

export async function sbSubscribe(
  email: string,
): Promise<{ status: string; message: string }> {
  const sb = ensureSupabase();

  // Check if already subscribed
  const { data: existing } = await sb
    .from("subscribers")
    .select("id, is_active, verified")
    .eq("email", email)
    .maybeSingle();

  if (existing) {
    if (existing.is_active && existing.verified) {
      return { status: "already", message: "You are already subscribed and verified!" };
    }
    // Re-subscribe: update with new token
    const token = generateToken();
    await sb
      .from("subscribers")
      .update({
        is_active: true,
        verified: false,
        verification_token: token,
      })
      .eq("id", existing.id);

    // Trigger verification email via RPC (if configured)
    try {
      await sb.rpc("send_verification_email", { p_email: email, p_token: token });
    } catch {
      // Silent fail — email may be sent by cron job or admin
    }

    return { status: "success", message: "Please check your email and click the verification link." };
  }

  // New subscriber
  const token = generateToken();
  const { error } = await sb.from("subscribers").insert({
    email,
    verification_token: token,
    verified: false,
  });

  if (error) {
    if (error.code === "23505") {
      return { status: "already", message: "You are already subscribed!" };
    }
    return { status: "error", message: error.message };
  }

  // Trigger verification email via RPC (if configured)
  try {
    await sb.rpc("send_verification_email", { p_email: email, p_token: token });
  } catch {
    // Silent fail — email will be sent by admin/backend
  }

  return { status: "success", message: "Please check your email and click the verification link." };
}

export async function sbVerifyEmail(
  token: string,
): Promise<{ status: string; message: string }> {
  const sb = ensureSupabase();

  const { data: subscriber, error: fetchErr } = await sb
    .from("subscribers")
    .select("id, verified")
    .eq("verification_token", token)
    .maybeSingle();

  if (fetchErr || !subscriber) {
    return { status: "error", message: "Invalid or expired verification token." };
  }

  if (subscriber.verified) {
    return { status: "already", message: "Email already verified!" };
  }

  const { error: updateErr } = await sb
    .from("subscribers")
    .update({
      verified: true,
      verified_at: new Date().toISOString(),
      verification_token: null,
    })
    .eq("id", subscriber.id);

  if (updateErr) {
    return { status: "error", message: updateErr.message };
  }

  return { status: "success", message: "Email verified successfully!" };
}

export async function sbSubmitMasterApplication(
  github: string,
  name: string,
  bio: string,
  repoUrls: string[],
): Promise<{ status: string; message: string }> {
  const sb = ensureSupabase();

  const { error } = await sb.from("master_applications").insert({
    github,
    name,
    bio,
    repo_urls: JSON.stringify(repoUrls),
    status: "pending",
  });

  if (error) {
    return { status: "error", message: error.message };
  }

  return {
    status: "submitted",
    message: "Application submitted! We will review it soon.",
  };
}

// ═══ Workflow Submission ═══

export async function sbSubmitWorkflow(
  name: string,
  description: string,
  steps: { name: string; slug: string; description: string }[],
): Promise<{ status: string; message: string }> {
  const sb = ensureSupabase();

  const { error } = await sb.from("submitted_workflows").insert({
    name,
    description,
    steps: JSON.stringify(steps),
    submitted_by: "community",
    status: "pending",
  });

  if (error) {
    return { status: "error", message: error.message };
  }

  return {
    status: "submitted",
    message: "Workflow submitted! It will be reviewed by our team.",
  };
}

// ═══ Admin RPC (single router for all admin operations) ═══

export async function sbAdminAction<T = unknown>(
  token: string,
  action: string,
  payload: Record<string, unknown> = {},
): Promise<T> {
  const sb = ensureSupabase();
  const { data, error } = await sb.rpc("admin_action", {
    admin_token: token,
    action,
    payload,
  });
  if (error) throw new Error(error.message);
  return data as T;
}
