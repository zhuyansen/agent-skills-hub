/**
 * Data for /skill/<owner>/<repo>/<slug>/: one SKILL.md inside a repository that holds several
 * skills (table sub_skills; scripts/sub-skills.mjs says which get pages). Its own module
 * because supabaseClient.ts is already past the file-size limit.
 */
import { supabase } from "../lib/supabase";
import { subSkillsJsonPath } from "../lib/subSkillMeta.mjs";

export interface SubSkill {
  repo_full_name: string;
  path: string;
  slug: string;
  name: string;
  description: string;
  body_excerpt: string;
  security_grade: string | null;
}

export interface SubSkillParent {
  repo_full_name: string;
  stars: number;
}

/** An entry of the repository's sub-skills.json (scripts/generate-sub-skill-pages.mjs).
 *  `page` is true when the build published a page for it. */
export interface SubSkillListItem {
  slug: string;
  name: string;
  path: string;
  grade: string | null;
  description: string;
  page: boolean;
}

const SUB_COLUMNS = "repo_full_name,path,slug,name,description,body_excerpt,security_grade";

export async function fetchSubSkill(repoFullName: string, slug: string): Promise<SubSkill | null> {
  if (!supabase) return null;
  const { data, error } = await supabase
    .from("sub_skills")
    .select(SUB_COLUMNS)
    .eq("repo_full_name", repoFullName)
    .eq("slug", slug)
    .maybeSingle<SubSkill>();
  if (error) throw new Error(error.message);
  return data;
}

export async function fetchSubSkillParent(repoFullName: string): Promise<SubSkillParent | null> {
  if (!supabase) return null;
  const { data, error } = await supabase
    .from("skills")
    .select("repo_full_name,stars")
    .eq("repo_full_name", repoFullName)
    .maybeSingle<SubSkillParent>();
  if (error) throw new Error(error.message);
  return data;
}

function isListItem(value: unknown): value is SubSkillListItem {
  if (typeof value !== "object" || value === null) return false;
  const item = value as Record<string, unknown>;
  return typeof item.slug === "string" && typeof item.name === "string" && typeof item.page === "boolean";
}

/** The repository's skill list. null: the build published none for it (a 404 on the site, the
 *  SPA's HTML in the dev server). undefined: the site could not be reached, so nobody knows. */
export async function fetchRepoSubSkillList(repoFullName: string): Promise<SubSkillListItem[] | null | undefined> {
  let r: Response;
  try {
    r = await fetch(subSkillsJsonPath(repoFullName));
  } catch {
    return undefined;
  }
  if (r.status === 404) return null;
  if (!r.ok) return undefined;
  const data: unknown = await r.json().catch(() => null);
  return Array.isArray(data) ? data.filter(isListItem) : null;
}
