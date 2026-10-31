/**
 * Where an old /skill/ URL went: the current name of a repository GitHub renamed or transferred
 * (table skill_redirects, written by backend/renamed_repos.py). A visit that loads an old URL
 * gets the build's redirect page (scripts/generate-skill-redirects.mjs); this covers links to one
 * followed inside the app. Its own module because supabaseClient.ts is already past the
 * file-size limit.
 */
import { supabase } from "../lib/supabase";

/** The repository's current owner/repo, or null: no redirect, or none could be read. */
export async function fetchSkillRedirect(oldName: string): Promise<string | null> {
  if (!supabase) return null;
  const { data, error } = await supabase
    .from("skill_redirects")
    .select("new_full_name")
    .eq("old_full_name", oldName)
    .maybeSingle<{ new_full_name: string }>();
  if (error) return null;
  return data?.new_full_name ?? null;
}
