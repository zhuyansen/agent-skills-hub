import type {
  CategoryCount,
  ExtraRepoData,
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
  sbFetchLanguageStats,
  sbFetchMasters,
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

export async function fetchSkillDetail(id: number): Promise<SkillDetail> {
  if (USE_SUPABASE) return sbFetchSkillDetail(id);
  return request<SkillDetail>(`/api/skills/${id}`);
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

// ═══ Admin API ═══

function adminHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

export async function adminFetchMasters(token: string): Promise<MasterData[]> {
  return request<MasterData[]>("/api/admin/masters", { headers: adminHeaders(token) });
}

export async function adminCreateMaster(
  token: string,
  data: { github: string; name: string; github_aliases?: string[]; x_handle?: string; bio?: string; tags?: string[] }
): Promise<MasterData> {
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
  return request<MasterData>(`/api/admin/masters/${id}`, {
    method: "PUT",
    headers: adminHeaders(token),
    body: JSON.stringify(data),
  });
}

export async function adminDeleteMaster(token: string, id: number): Promise<void> {
  await request(`/api/admin/masters/${id}`, { method: "DELETE", headers: adminHeaders(token) });
}

export async function adminFetchExtraRepos(token: string): Promise<ExtraRepoData[]> {
  return request<ExtraRepoData[]>("/api/admin/extra-repos", { headers: adminHeaders(token) });
}

export async function adminCreateExtraRepo(token: string, full_name: string): Promise<ExtraRepoData> {
  return request<ExtraRepoData>("/api/admin/extra-repos", {
    method: "POST",
    headers: adminHeaders(token),
    body: JSON.stringify({ full_name }),
  });
}

export async function adminDeleteExtraRepo(token: string, id: number): Promise<void> {
  await request(`/api/admin/extra-repos/${id}`, { method: "DELETE", headers: adminHeaders(token) });
}

export async function adminFetchSearchQueries(token: string): Promise<SearchQueryData[]> {
  return request<SearchQueryData[]>("/api/admin/search-queries", { headers: adminHeaders(token) });
}

export async function adminCreateSearchQuery(token: string, query: string): Promise<SearchQueryData> {
  return request<SearchQueryData>("/api/admin/search-queries", {
    method: "POST",
    headers: adminHeaders(token),
    body: JSON.stringify({ query }),
  });
}

export async function adminDeleteSearchQuery(token: string, id: number): Promise<void> {
  await request(`/api/admin/search-queries/${id}`, { method: "DELETE", headers: adminHeaders(token) });
}

export async function adminFetchSyncLogs(token: string): Promise<SyncLogData[]> {
  return request<SyncLogData[]>("/api/admin/sync-logs", { headers: adminHeaders(token) });
}

export async function adminTriggerSync(token: string): Promise<{ message: string; sync_id: number }> {
  return request("/api/admin/sync", { method: "POST", headers: adminHeaders(token) });
}

export async function adminFetchSkills(
  token: string,
  page = 1,
  search?: string
): Promise<Skill[]> {
  const sp = new URLSearchParams({ page: String(page), page_size: "50" });
  if (search) sp.set("search", search);
  return request<Skill[]>(`/api/admin/skills?${sp}`, { headers: adminHeaders(token) });
}

export async function adminDeleteSkill(token: string, id: number): Promise<void> {
  await request(`/api/admin/skills/${id}`, { method: "DELETE", headers: adminHeaders(token) });
}
