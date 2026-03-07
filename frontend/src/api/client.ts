import type {
  CategoryCount,
  ExtraRepoData,
  LandingData,
  MasterData,
  PaginatedSkills,
  SearchQueryData,
  Skill,
  SkillDetail,
  SkillsQueryParams,
  Stats,
  SyncLogData,
} from "../types/skill";
import { supabase } from "../lib/supabase";
import {
  sbFetchSkills,
  sbFetchStats,
  sbFetchCategories,
  sbFetchTrending,
  sbFetchRising,
  sbFetchTopRated,
  sbFetchMostStarred,
  sbFetchRecentlyUpdated,
  sbFetchSkillDetail,
  sbFetchSkillBySlug,
  sbFetchLanguageStats,
  sbFetchLandingData,
  sbFetchMasters,
  sbSubmitSkill,
  sbSubscribe,
  sbVerifyEmail,
  sbSubmitMasterApplication,
  sbAdminAction,
} from "./supabaseClient";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

// Use Supabase when configured AND no local API base URL is set.
// When VITE_API_BASE_URL is set (local dev), use FastAPI backend.
// When deployed (no API base), use Supabase directly.
const USE_SUPABASE = !!supabase && !API_BASE;

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

// ═══ Public API (auto-switches between Supabase and FastAPI) ═══

export async function fetchSkills(params: SkillsQueryParams): Promise<PaginatedSkills> {
  if (USE_SUPABASE) return sbFetchSkills(params);
  const sp = new URLSearchParams();
  sp.set("page", String(params.page));
  sp.set("page_size", String(params.page_size));
  sp.set("sort_by", params.sort_by);
  sp.set("sort_order", params.sort_order);
  if (params.search) sp.set("search", params.search);
  if (params.category) sp.set("category", params.category);
  if (params.platform) sp.set("platform", params.platform);
  if (params.size_category) sp.set("size_category", params.size_category);
  return request<PaginatedSkills>(`/api/skills?${sp}`);
}

export async function fetchStats(): Promise<Stats> {
  if (USE_SUPABASE) return sbFetchStats();
  return request<Stats>("/api/stats");
}

export async function fetchCategories(): Promise<CategoryCount[]> {
  if (USE_SUPABASE) return sbFetchCategories();
  return request<CategoryCount[]>("/api/categories");
}

export async function fetchTrending(limit = 10): Promise<Skill[]> {
  if (USE_SUPABASE) return sbFetchTrending(limit);
  return request<Skill[]>(`/api/trending?limit=${limit}`);
}

export async function fetchRising(days = 7, limit = 10): Promise<Skill[]> {
  if (USE_SUPABASE) return sbFetchRising(days, limit);
  return request<Skill[]>(`/api/rising?days=${days}&limit=${limit}`);
}

export async function fetchTopRated(limit = 10): Promise<Skill[]> {
  if (USE_SUPABASE) return sbFetchTopRated(limit);
  return request<Skill[]>(`/api/top-rated?limit=${limit}`);
}

export async function fetchMostStarred(limit = 10): Promise<Skill[]> {
  if (USE_SUPABASE) return sbFetchMostStarred(limit);
  return request<Skill[]>(`/api/most-starred?limit=${limit}`);
}

export async function fetchRecentlyUpdated(limit = 10): Promise<Skill[]> {
  if (USE_SUPABASE) return sbFetchRecentlyUpdated(limit);
  return request<Skill[]>(`/api/recently-updated?limit=${limit}`);
}

export async function fetchQuickSearch(query: string, limit = 8): Promise<Skill[]> {
  if (!query.trim()) return [];
  if (USE_SUPABASE) {
    const sb = supabase!;
    const pat = `%${query}%`;
    const { data, error } = await sb
      .from("skills")
      .select("id,repo_full_name,repo_name,repo_url,description,author_name,author_avatar_url,stars,score,category,language,platforms,size_category,repo_size_kb,author_followers,forks,open_issues,total_issues,total_commits,topics,license,star_momentum,project_type,last_commit_at,created_at,last_synced,quality_completeness,quality_clarity,quality_specificity,quality_examples,quality_agent_readiness,quality_score,readme_size,readme_structure_score,estimated_tokens,homepage_url")
      .or(`repo_name.ilike.${pat},description.ilike.${pat},author_name.ilike.${pat},topics.ilike.${pat}`)
      .order("score", { ascending: false })
      .limit(limit);
    if (error) throw new Error(error.message);
    return (data ?? []) as Skill[];
  }
  return request<Skill[]>(`/api/skills?search=${encodeURIComponent(query)}&page_size=${limit}&sort_by=score&sort_order=desc`).then(
    (r: any) => r.items || r,
  );
}

export async function fetchSkillDetail(id: number): Promise<SkillDetail> {
  if (USE_SUPABASE) return sbFetchSkillDetail(id);
  return request<SkillDetail>(`/api/skills/${id}`);
}

export async function fetchSkillBySlug(slug: string): Promise<SkillDetail> {
  if (USE_SUPABASE) return sbFetchSkillBySlug(slug);
  return request<SkillDetail>(`/api/skills/by-slug/${encodeURIComponent(slug)}`);
}

export async function fetchLanguageStats(): Promise<{ language: string; count: number }[]> {
  if (USE_SUPABASE) return sbFetchLanguageStats();
  return request(`/api/language-stats?limit=10`);
}

export async function fetchPlatformStats(): Promise<{ platform: string; count: number }[]> {
  return request(`/api/platforms`);
}

export interface Master {
  github: string;
  name: string;
  x_handle: string | null;
  bio: string | null;
  tags: string[];
  avatar_url: string;
  repo_count: number;
  total_stars: number;
  x_followers: number;
  x_posts_count: number;
  x_verified_at: string | null;
  x_notes: string | null;
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
  discovered?: boolean;
}

export async function fetchMasters(): Promise<Master[]> {
  if (USE_SUPABASE) return sbFetchMasters();
  return request<Master[]>("/api/masters");
}

// ═══ Landing Page Bundle (single-request for all overview data) ═══

export async function fetchLandingData(): Promise<LandingData> {
  if (USE_SUPABASE) {
    // Single RPC call replaces 7+ individual requests
    return sbFetchLandingData();
  }
  return request<LandingData>("/api/landing");
}

// ═══ Community Submission ═══

export async function submitSkill(repoUrl: string): Promise<{ status: string; message: string; skill_id?: number }> {
  if (USE_SUPABASE) return sbSubmitSkill(repoUrl);
  return request("/api/submit-skill", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl }),
  });
}

export async function subscribe(email: string): Promise<{ status: string; message: string }> {
  if (USE_SUPABASE) return sbSubscribe(email);
  const res = await fetch(`${API_BASE}/api/subscribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Subscription failed");
  return { status: "success", message: data.message || "Subscribed!" };
}

export async function submitMasterApplication(
  github: string,
  name: string,
  bio: string,
  repoUrls: string[],
): Promise<{ status: string; message: string }> {
  if (USE_SUPABASE) return sbSubmitMasterApplication(github, name, bio, repoUrls);
  return request("/api/submit-master", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ github, name, bio, repo_urls: repoUrls }),
  });
}

// ═══ Email Verification ═══

export async function verifyEmail(token: string): Promise<{ status: string; message: string }> {
  if (USE_SUPABASE) return sbVerifyEmail(token);
  // FastAPI backend handles it via redirect, so this is for SPA verification
  return request(`/api/verify-email?token=${encodeURIComponent(token)}`);
}

// ═══ Admin API (auto-switches between Supabase RPC and FastAPI) ═══

function adminHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

export async function adminFetchMasters(token: string): Promise<MasterData[]> {
  if (USE_SUPABASE) return sbAdminAction<MasterData[]>(token, "fetch_masters");
  return request<MasterData[]>("/api/admin/masters", { headers: adminHeaders(token) });
}

export async function adminCreateMaster(
  token: string,
  data: { github: string; name: string; github_aliases?: string[]; x_handle?: string; bio?: string; tags?: string[] }
): Promise<MasterData> {
  if (USE_SUPABASE) {
    return sbAdminAction<MasterData>(token, "create_master", {
      github: data.github,
      name: data.name,
      github_aliases: JSON.stringify(data.github_aliases ?? []),
      x_handle: data.x_handle ?? null,
      bio: data.bio ?? null,
      tags: JSON.stringify(data.tags ?? []),
    });
  }
  return request<MasterData>("/api/admin/masters", {
    method: "POST",
    headers: adminHeaders(token),
    body: JSON.stringify(data),
  });
}

export async function adminUpdateMaster(
  token: string,
  id: number,
  data: Partial<{ name: string; github_aliases: string[]; x_handle: string; bio: string; tags: string[]; is_active: boolean; x_followers: number; x_posts_count: number; x_notes: string }>
): Promise<MasterData> {
  if (USE_SUPABASE) {
    const payload: Record<string, unknown> = { id };
    if (data.name !== undefined) payload.name = data.name;
    if (data.github_aliases !== undefined) payload.github_aliases = JSON.stringify(data.github_aliases);
    if (data.x_handle !== undefined) payload.x_handle = data.x_handle;
    if (data.bio !== undefined) payload.bio = data.bio;
    if (data.tags !== undefined) payload.tags = JSON.stringify(data.tags);
    if (data.is_active !== undefined) payload.is_active = data.is_active;
    if (data.x_followers !== undefined) payload.x_followers = data.x_followers;
    if (data.x_posts_count !== undefined) payload.x_posts_count = data.x_posts_count;
    if (data.x_notes !== undefined) payload.x_notes = data.x_notes;
    return sbAdminAction<MasterData>(token, "update_master", payload);
  }
  return request<MasterData>(`/api/admin/masters/${id}`, {
    method: "PUT",
    headers: adminHeaders(token),
    body: JSON.stringify(data),
  });
}

export async function adminDeleteMaster(token: string, id: number): Promise<void> {
  if (USE_SUPABASE) { await sbAdminAction(token, "delete_master", { id }); return; }
  await request(`/api/admin/masters/${id}`, { method: "DELETE", headers: adminHeaders(token) });
}

export async function adminFetchExtraRepos(token: string): Promise<ExtraRepoData[]> {
  if (USE_SUPABASE) return sbAdminAction<ExtraRepoData[]>(token, "fetch_extra_repos");
  return request<ExtraRepoData[]>("/api/admin/extra-repos", { headers: adminHeaders(token) });
}

export async function adminCreateExtraRepo(token: string, full_name: string): Promise<ExtraRepoData> {
  if (USE_SUPABASE) return sbAdminAction<ExtraRepoData>(token, "create_extra_repo", { full_name });
  return request<ExtraRepoData>("/api/admin/extra-repos", {
    method: "POST",
    headers: adminHeaders(token),
    body: JSON.stringify({ full_name }),
  });
}

export async function adminDeleteExtraRepo(token: string, id: number): Promise<void> {
  if (USE_SUPABASE) { await sbAdminAction(token, "delete_extra_repo", { id }); return; }
  await request(`/api/admin/extra-repos/${id}`, { method: "DELETE", headers: adminHeaders(token) });
}

export async function adminApproveExtraRepo(token: string, id: number): Promise<{ message: string }> {
  if (USE_SUPABASE) return sbAdminAction<{ message: string }>(token, "approve_extra_repo", { id });
  return request(`/api/admin/extra-repos/${id}/approve`, { method: "PUT", headers: adminHeaders(token) });
}

export async function adminRejectExtraRepo(token: string, id: number): Promise<{ message: string }> {
  if (USE_SUPABASE) return sbAdminAction<{ message: string }>(token, "reject_extra_repo", { id });
  return request(`/api/admin/extra-repos/${id}/reject`, { method: "PUT", headers: adminHeaders(token) });
}

export async function adminFetchSearchQueries(token: string): Promise<SearchQueryData[]> {
  if (USE_SUPABASE) return sbAdminAction<SearchQueryData[]>(token, "fetch_search_queries");
  return request<SearchQueryData[]>("/api/admin/search-queries", { headers: adminHeaders(token) });
}

export async function adminCreateSearchQuery(token: string, query: string): Promise<SearchQueryData> {
  if (USE_SUPABASE) return sbAdminAction<SearchQueryData>(token, "create_search_query", { query });
  return request<SearchQueryData>("/api/admin/search-queries", {
    method: "POST",
    headers: adminHeaders(token),
    body: JSON.stringify({ query }),
  });
}

export async function adminDeleteSearchQuery(token: string, id: number): Promise<void> {
  if (USE_SUPABASE) { await sbAdminAction(token, "delete_search_query", { id }); return; }
  await request(`/api/admin/search-queries/${id}`, { method: "DELETE", headers: adminHeaders(token) });
}

// ═══ Admin Subscribers ═══

export interface SubscriberData {
  id: number;
  email: string;
  subscribed_at: string | null;
  is_active: boolean;
  verified: boolean;
  verified_at: string | null;
}

export async function adminFetchSubscribers(token: string): Promise<SubscriberData[]> {
  if (USE_SUPABASE) return sbAdminAction<SubscriberData[]>(token, "fetch_subscribers");
  return request<SubscriberData[]>("/api/admin/subscribers", { headers: adminHeaders(token) });
}

export async function adminDeleteSubscriber(token: string, id: number): Promise<void> {
  if (USE_SUPABASE) { await sbAdminAction(token, "delete_subscriber", { id }); return; }
  await request(`/api/admin/subscribers/${id}`, { method: "DELETE", headers: adminHeaders(token) });
}

export async function adminFetchSyncLogs(token: string): Promise<SyncLogData[]> {
  if (USE_SUPABASE) return sbAdminAction<SyncLogData[]>(token, "fetch_sync_logs");
  return request<SyncLogData[]>("/api/admin/sync-logs", { headers: adminHeaders(token) });
}

export async function adminTriggerSync(token: string): Promise<{ message: string; sync_id: number }> {
  if (USE_SUPABASE) return sbAdminAction<{ message: string; sync_id: number }>(token, "trigger_sync");
  return request("/api/admin/sync", { method: "POST", headers: adminHeaders(token) });
}

export async function adminFetchSkills(
  token: string,
  page = 1,
  search?: string
): Promise<Skill[]> {
  if (USE_SUPABASE) return sbAdminAction<Skill[]>(token, "fetch_skills", { page, search: search ?? "" });
  const sp = new URLSearchParams({ page: String(page), page_size: "50" });
  if (search) sp.set("search", search);
  return request<Skill[]>(`/api/admin/skills?${sp}`, { headers: adminHeaders(token) });
}

export async function adminDeleteSkill(token: string, id: number): Promise<void> {
  if (USE_SUPABASE) { await sbAdminAction(token, "delete_skill", { id }); return; }
  await request(`/api/admin/skills/${id}`, { method: "DELETE", headers: adminHeaders(token) });
}

// ═══ Admin Master Applications ═══

export interface MasterApplicationData {
  id: number;
  github: string;
  name: string;
  bio: string | null;
  repo_urls: string;
  status: string;
  created_at: string;
}

export async function adminFetchMasterApplications(token: string): Promise<MasterApplicationData[]> {
  if (USE_SUPABASE) return sbAdminAction<MasterApplicationData[]>(token, "fetch_master_applications");
  return request<MasterApplicationData[]>("/api/admin/master-applications", { headers: adminHeaders(token) });
}

export async function adminApproveMasterApplication(token: string, id: number): Promise<{ message: string }> {
  if (USE_SUPABASE) return sbAdminAction<{ message: string }>(token, "approve_master_application", { id });
  return request(`/api/admin/master-applications/${id}/approve`, { method: "PUT", headers: adminHeaders(token) });
}

export async function adminRejectMasterApplication(token: string, id: number): Promise<{ message: string }> {
  if (USE_SUPABASE) return sbAdminAction<{ message: string }>(token, "reject_master_application", { id });
  return request(`/api/admin/master-applications/${id}/reject`, { method: "PUT", headers: adminHeaders(token) });
}
