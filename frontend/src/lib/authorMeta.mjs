/**
 * Title, meta description and indexing of an /author/<name>/ or /organization/<name>/ page, shared by
 * the static generator (scripts/generate-author-pages.mjs) and the React page
 * (src/pages/AuthorPage.tsx), which replaces the static markup once JS runs. Google renders
 * JS, so what it indexes is the React version; both must come from these functions.
 *
 * 2026-11-20 (OpenSEO audit, 10,000 pages): all 165 author pages it reached had a title over
 * 60 characters ("<name> — Top 7 AI Agent Skills (Security-Graded) · Agent Skills Hub", median
 * 70), so a results page cut every one of them. Search Console, 08-18 to 11-18: author pages
 * drew 19,177 impressions at positions 5-10 and 154 clicks (0.8%). The site name goes first
 * when the title is too long (a results page shows it above the title anyway), then the
 * security note. One skill reads "1 AI Agent Skill", not "Top 1 AI Agent Skills".
 */
import { TITLE_MAX_WIDTH, displayWidth } from "./skillMeta.mjs";

const SITE_NAME = "Agent Skills Hub";

/** "1 skill", "7 skills". */
export function countNoun(count, one, many) {
  return `${count.toLocaleString("en-US")} ${count === 1 ? one : many}`;
}

/**
 * The Author's name leads: people search the name (LobeHub's "Guizang – Top 3 AI Agent
 * Skills"). `total` is 0 while the React page is still loading.
 */
export function authorTitle(displayName, total, safeCount) {
  const what = total === 1 ? "1 AI Agent Skill" : total > 1 ? `Top ${total} AI Agent Skills` : "AI Agent Skills";
  const graded = safeCount ? " (Security-Graded)" : "";
  const candidates = [
    `${displayName} — ${what}${graded} · ${SITE_NAME}`,
    `${displayName} — ${what}${graded}`,
    `${displayName} — ${what}`,
    `${displayName} — AI Agent Skills`,
  ];
  return candidates.find((title) => displayWidth(title) <= TITLE_MAX_WIDTH) ?? candidates[candidates.length - 1];
}

/** An author page for this many Skills or fewer is noindex, unless someone wrote about the Author. */
export const THIN_AUTHOR_MAX_SKILLS = 2;

/**
 * Whether an author page asks to be indexed. 2026-11-21, the owner's call after the OpenSEO audit
 * of 2026-11-20: a page for one or two Skills says little their own /skill/ pages do not, and the
 * 279 such pages drew 3 clicks in Search Console from 08-18 to 11-18. A Master with a bio, or a
 * Verified Creator, keeps an indexed page: there a person wrote about them. The page stays live,
 * linked and shareable either way.
 */
export function authorIndexable(skillCount, master) {
  return skillCount > THIN_AUTHOR_MAX_SKILLS || Boolean(master?.bio || master?.is_verified);
}

/** `totalStars` is left out where the caller only has one page of the Author's Skills. */
export function authorDescription(displayName, total, safeCount, totalStars) {
  const skills = total === 1 ? "1 open-source skill or MCP server" : `${total} open-source skills & MCP servers`;
  const stars = typeof totalStars === "number" ? `, ${totalStars.toLocaleString("en-US")}+ GitHub stars` : "";
  const safe = safeCount ? `, ${safeCount} security-verified safe` : "";
  return `${displayName}'s AI agent skills: ${skills}${stars}${safe}. Quality-scored on AgentSkillsHub.`;
}
