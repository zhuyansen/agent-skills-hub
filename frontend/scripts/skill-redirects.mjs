/**
 * Old names of renamed or transferred GitHub repositories (table skill_redirects, written by
 * backend/renamed_repos.py). GitHub answers an old name with a redirect, the sync files the
 * repository under the name GitHub returns, and the row under the old name used to stay behind
 * with frozen numbers and an indexed page of its own: 277 of the 4,108 rows with 500+ stars on
 * 2026-10-31, whose old URLs held 5,961 impressions in 90 days. The backend now keeps one row
 * per repository. This module gives each old /skill/ URL a redirect page, so that search history
 * passes to the new URL instead of ending in a 404, and renames the repositories the curated
 * /best/ files name (scripts/rename-curated.mjs).
 */
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { SUPABASE_URL, SUPABASE_ANON_KEY, SITE, esc } from "./shared-utils.mjs";

const HEADERS = { apikey: SUPABASE_ANON_KEY, Authorization: `Bearer ${SUPABASE_ANON_KEY}` };
const PAGE = 1000;          // PostgREST's row limit per request
const RETRIES = 3;
const TIMEOUT_MS = 20000;
/** PostgREST's code for a table it does not know: skill_redirects before migration 041. */
const NO_TABLE = "PGRST205";
const HERE = dirname(fileURLToPath(import.meta.url));
/** The curated files that name repositories, all written as JSON.stringify(data, null, 1). */
export const CURATED_FILES = ["scenario-keywords.json", "scenario-kinds.json", "scenario-desc-zh.json",
  "scenario-desc-en.json"].map((f) => join(HERE, f));
const CURATED_INDENT = 1;

// ── data ──────────────────────────────────────────────────────────────────────────

/** One page of rows, or null when the table does not exist yet. */
async function getPage(offset) {
  const url = `${SUPABASE_URL}/rest/v1/skill_redirects?select=old_full_name,new_full_name`
    + `&order=old_full_name.asc&limit=${PAGE}&offset=${offset}`;
  const r = await fetch(url, { headers: HEADERS, signal: AbortSignal.timeout(TIMEOUT_MS) });
  if (r.ok) return r.json();
  const text = await r.text();
  if (text.includes(NO_TABLE)) return null;
  throw new Error(`HTTP ${r.status}: ${text.slice(0, 200)}`);
}

async function getPageWithRetry(offset) {
  for (let attempt = 1; ; attempt++) {
    try {
      return await getPage(offset);
    } catch (err) {
      if (attempt >= RETRIES) throw new Error(`skill_redirects: ${err.message}`);
      await new Promise((res) => setTimeout(res, 1000 * attempt));
    }
  }
}

/** Every redirect as [old, new] full names; [] while the table does not exist (migration 041). */
export async function fetchSkillRedirects() {
  const rows = [];
  for (let offset = 0; ; offset += PAGE) {
    const page = await getPageWithRetry(offset);
    if (page === null) {
      console.warn("  skill_redirects: no such table yet (migration 041), so no redirects");
      return [];
    }
    rows.push(...page.map((r) => [r.old_full_name, r.new_full_name]));
    if (page.length < PAGE) return rows;
  }
}

// ── redirect pages ────────────────────────────────────────────────────────────────

/** Redirects that need a page: the two names differ by more than case (GitHub serves any case of
 *  a name), and the old name has no page of its own (`hasPage`), which it has again when a new
 *  repository takes the old name. */
export function stubsToWrite(redirects, hasPage) {
  return redirects.filter(([from, to]) => from.toLowerCase() !== to.toLowerCase() && !hasPage(from));
}

/** The page at an old /skill/ URL: an instant meta refresh (Google reads it as a permanent
 *  redirect), a canonical pointing the same way, and a script for visitors. Unlike the other
 *  redirect pages (generate-static-pages.mjs) it has no robots noindex: the redirect takes the
 *  old URL out of the index by itself, and a noindex next to it could stop Google from passing
 *  the old URL's signals on to the new one. */
export function redirectStubHtml(newName) {
  const path = `/skill/${newName}/`;
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Redirecting… — AgentSkillsHub</title>
<link rel="canonical" href="${esc(SITE + path)}" />
<meta http-equiv="refresh" content="0; url=${esc(path)}" />
<script>location.replace(${JSON.stringify(path)});</script>
</head>
<body>Redirecting to <a href="${esc(path)}">${esc(newName)}</a>…</body>
</html>
`;
}

// ── curated files ─────────────────────────────────────────────────────────────────

/** Old name (lowercased) -> new name. */
export const renameMap = (redirects) => new Map(redirects.map(([from, to]) => [from.toLowerCase(), to]));

function renamed(s, renames, changes) {
  const to = renames.get(s.toLowerCase());
  if (!to || to === s) return s;
  changes.push([s, to]);
  return to;
}

/** A renamed entry is dropped when the list names its repository already. */
function renameList(list, renames, changes) {
  const present = new Set(list.filter((v) => typeof v === "string").map((v) => v.toLowerCase()));
  const out = [];
  for (const v of list) {
    const next = renameNames(v, renames, changes);
    if (next !== v && typeof next === "string") {
      if (present.has(next.toLowerCase())) continue;
      present.add(next.toLowerCase());
    }
    out.push(next);
  }
  return out;
}

/** A renamed key keeps its place; it is dropped when the object has an entry under the new name. */
function renameKeys(obj, renames, changes) {
  const out = {};
  for (const [key, v] of Object.entries(obj)) {
    const next = renamed(key, renames, changes);
    if (next !== key && Object.hasOwn(obj, next)) continue;
    out[next] = renameNames(v, renames, changes);
  }
  return out;
}

/** `value` with every string that equals an old name (in any case), as a value or a key, replaced
 *  by the new name; `changes` collects the [old, new] pairs. A sentence that mentions a name is
 *  left alone. */
export function renameNames(value, renames, changes = []) {
  if (typeof value === "string") return renamed(value, renames, changes);
  if (Array.isArray(value)) return renameList(value, renames, changes);
  if (value && typeof value === "object") return renameKeys(value, renames, changes);
  return value;
}

/** A curated file's text, formatted the way the files in the repository are. */
export const curatedJson = (data) => `${JSON.stringify(data, null, CURATED_INDENT)}\n`;
