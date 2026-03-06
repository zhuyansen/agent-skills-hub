export interface Skill {
  id: number;
  repo_full_name: string;
  repo_name: string;
  repo_url: string;
  description: string;
  homepage_url: string;
  author_name: string;
  author_avatar_url: string;
  author_followers: number;
  stars: number;
  forks: number;
  open_issues: number;
  total_issues: number;
  total_commits: number;
  language: string;
  category: string;
  topics: string; // JSON string
  license: string;
  score: number;
  star_momentum: number;
  project_type: string;
  last_commit_at: string | null;
  created_at: string | null;
  last_synced: string | null;

  // Quality scoring (4 dimensions)
  quality_completeness: number;
  quality_clarity: number;
  quality_specificity: number;
  quality_examples: number;
  quality_agent_readiness: number;
  quality_score: number;

  // Size / Focus
  size_category: string;
  repo_size_kb: number;
  readme_size: number;
  readme_structure_score: number;

  // Platforms
  platforms: string; // JSON string e.g. '["python","node"]'

  // Token budget
  estimated_tokens: number;
}

export interface SkillCompositionItem {
  skill_id: number;
  skill_name: string;
  skill_score: number;
  compatibility_score: number;
  reason: string;
}

export interface SkillDetail extends Skill {
  compatible_skills: SkillCompositionItem[];
}

export interface PaginatedSkills {
  items: Skill[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CategoryCount {
  name: string;
  count: number;
}

export interface Stats {
  total_skills: number;
  categories: CategoryCount[];
  avg_score: number;
  last_sync_at: string | null;
  last_sync_status: string | null;
}

export interface SkillsQueryParams {
  page: number;
  page_size: number;
  sort_by: "score" | "stars" | "last_commit_at" | "created_at";
  sort_order: "asc" | "desc";
  search?: string;
  category?: string;
  platform?: string;
  size_category?: string;
}

// Admin types
export interface MasterData {
  id: number;
  github: string;
  github_aliases: string;
  name: string;
  x_handle: string | null;
  bio: string | null;
  tags: string;
  x_followers: number;
  x_posts_count: number;
  x_verified_at: string | null;
  x_notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExtraRepoData {
  id: number;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface SearchQueryData {
  id: number;
  query: string;
  is_active: boolean;
  created_at: string;
}

export interface SyncLogData {
  id: number;
  started_at: string | null;
  finished_at: string | null;
  status: string;
  repos_found: number;
  repos_new: number;
  repos_updated: number;
  error_message: string | null;
}
