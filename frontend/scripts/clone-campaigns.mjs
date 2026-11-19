/**
 * Clone campaigns: one real project's README copied under many throwaway accounts, every
 * copy with bought stars. The OpenSEO audit of 2026-11-18 found ~900 of them with live
 * /skill/ pages graded Safe (Simpleyyt/ai-manus' description under "ai--manus",
 * "manus--ai", "ai--manus2.0"…, the GitHub Copilot app's under "GitHub-Copilot-app", a
 * Gemini proxy scanner, a "Capri" desktop agent), each README a "GET" button to a .rar on
 * Dropbox. The backend deletes them on every sync (app/services/clone_campaigns.py, same
 * rule); this keeps a page from being built in the hours between a sync and its cleanup.
 *
 * The rule, checked against every same-description group in the catalog that day:
 *   - the same description (case and spacing ignored, at least MIN_DESC chars)
 *   - on at least MIN_OWNERS different accounts
 *   - and every copy has at least MIN_STARS stars. Forks and course copies of a real
 *     project share its description too, but sit at 0–1 stars (anthropics/claude-code's
 *     group: 156k, then 1, 0, 0…), so they never match.
 * The original is kept when it predates the rest of its group by ORIGINAL_LEAD_DAYS.
 */

export const MIN_DESC = 30;
export const MIN_OWNERS = 5;
export const MIN_STARS = 20;
export const ORIGINAL_LEAD_DAYS = 30;
const DAY_MS = 24 * 60 * 60 * 1000;

const normalize = (d) => (d || "").trim().replace(/\s+/g, " ").toLowerCase();
const ownerOf = (s) => (s.author_name || s.repo_full_name.split("/")[0]).toLowerCase();
const createdMs = (s) => (s.created_at ? Date.parse(s.created_at) : NaN);

function groupByDescription(skills) {
  const groups = new Map();
  for (const s of skills) {
    const d = normalize(s.description);
    if (d.length < MIN_DESC) continue;
    if (!groups.has(d)) groups.set(d, []);
    groups.get(d).push(s);
  }
  return groups;
}

function isCampaign(group) {
  return new Set(group.map(ownerOf)).size >= MIN_OWNERS && group.every((s) => (s.stars || 0) >= MIN_STARS);
}

/** The group's original: its oldest row, if made ORIGINAL_LEAD_DAYS before any other. */
function originalOf(group) {
  const dated = group.filter((s) => !Number.isNaN(createdMs(s))).sort((a, b) => createdMs(a) - createdMs(b));
  if (dated.length < 2) return null;
  return createdMs(dated[1]) - createdMs(dated[0]) >= ORIGINAL_LEAD_DAYS * DAY_MS ? dated[0] : null;
}

/** repo_full_names (lowercased) of every clone-campaign copy in `skills`. */
export function cloneCampaignRepos(skills) {
  const out = new Set();
  for (const group of groupByDescription(skills).values()) {
    if (!isCampaign(group)) continue;
    const original = originalOf(group);
    for (const s of group) if (s !== original) out.add(s.repo_full_name.toLowerCase());
  }
  return out;
}

/** `skills` without clone-campaign copies; logs how many it dropped. */
export function withoutCloneCampaigns(skills) {
  const drop = cloneCampaignRepos(skills);
  if (drop.size) console.log(`  ✓ dropped ${drop.size} clone-campaign copies (see clone-campaigns.mjs)`);
  return drop.size ? skills.filter((s) => !drop.has(s.repo_full_name.toLowerCase())) : skills;
}
