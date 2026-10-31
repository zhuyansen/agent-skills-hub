/**
 * Title, description, links and install line for a sub-skill page
 * (/skill/<owner>/<repo>/<slug>/: one SKILL.md inside a repository that holds several
 * skills). Shared by scripts/generate-sub-skill-pages.mjs and src/pages/SubSkillPage.tsx
 * for the same reason skillMeta.mjs is: Google indexes the React render, so the static
 * page and the React page must say the same thing.
 */
import { skillTitle, DESCRIPTION_LIMIT } from "./skillMeta.mjs";

const SITE = "https://agentskillshub.top";

/** "unslop by mnapoli: Detect and remove AI-sounding writing patterns…", the repo pages' form. */
export function subSkillTitle(repoFullName, name, description) {
  const owner = repoFullName.split("/")[0];
  const safeName = name.replace(/\//g, "-");
  return skillTitle(`${owner}/${safeName}`, safeName, description);
}

/** At most `n` characters, counted by code point so an emoji is never cut in half. */
function cutChars(text, n) {
  const chars = Array.from(text);
  return chars.length > n ? `${chars.slice(0, n - 1).join("").trim()}…` : text;
}

/** What the skill does, then which repository it ships in, cut at what a results page shows. */
export function subSkillDescription(repoFullName, name, description) {
  const what = `${name}: ${String(description || "").trim().replace(/\.$/, "")}.`;
  const where = ` A skill in ${repoFullName}.`;
  const head = cutChars(what, DESCRIPTION_LIMIT);
  return head.length + where.length <= DESCRIPTION_LIMIT ? head + where : head;
}

export function subSkillPath(repoFullName, slug) {
  return `/skill/${repoFullName}/${slug}/`;
}

export function subSkillUrl(repoFullName, slug) {
  return `${SITE}${subSkillPath(repoFullName, slug)}`;
}

/** The per-repository list the generator writes next to the repository page. */
export function subSkillsJsonPath(repoFullName) {
  return `/skill/${repoFullName}/sub-skills.json`;
}

export function skillMdUrl(repoFullName, path) {
  return `https://github.com/${repoFullName}/blob/HEAD/${path ? `${path}/` : ""}SKILL.md`;
}

export function githubFolderUrl(repoFullName, path) {
  return path ? `https://github.com/${repoFullName}/tree/HEAD/${path}` : `https://github.com/${repoFullName}`;
}

/** The skills CLI's own form for installing one skill of a repository
 *  (vercel-labs/skills README: npx skills add <repo> --skill <name> -a claude-code). */
export function subSkillInstall(repoFullName, name) {
  const arg = /^[\w.-]+$/.test(name) ? name : `"${name.replace(/"/g, '\\"')}"`;
  return `npx skills add ${repoFullName} --skill ${arg} -a claude-code`;
}
