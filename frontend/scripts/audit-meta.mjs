/**
 * Title and meta description of an /audit/<owner>/<repo>/ page, cut to what a results page
 * shows. Used by generate-audit-pages.mjs (the pages are static, there is no React version).
 *
 * Until 2026-11-20 every title read "Is <repo> Safe? Security Audit of <owner/repo> — Agent
 * Skills Hub": 674 of the 679 audit pages the OpenSEO audit reached were over 60 characters
 * (median 79), so the owner/repo and the site name were what a results page cut. These pages
 * are found by the repo's name ("xxxxxccc", "synthadoc", "is codexbar safe"): Search Console,
 * 08-18 to 11-18, 322 clicks on 14,438 impressions at position 6-7. The question and the name
 * stay; the site name goes (a results page shows it above the title).
 */
import { DESCRIPTION_LIMIT, TITLE_MAX_WIDTH, displayWidth, fitName } from "../src/lib/skillMeta.mjs";

/** Lowercased repo names that more than one of these repos has ("skills", "mcp"): a title
 *  without the owner would be the same on each of their pages. */
export function sharedRepoNames(skills) {
  const counts = new Map();
  for (const s of skills) {
    const name = s.repo_name.toLowerCase();
    counts.set(name, (counts.get(name) || 0) + 1);
  }
  return new Set([...counts].filter(([, n]) => n > 1).map(([name]) => name));
}

/** Falls back to a separator-capped owner/repo inside the question when nothing shorter fits. */
export function auditTitle(skill, sharedNames = new Set()) {
  const { repo_name: repo, repo_full_name: full } = skill;
  const ownName = sharedNames.has(repo.toLowerCase()) ? [] : [repo];
  const question = `Is ${full} Safe?`;
  const candidates = [
    `Is ${repo} Safe? Security Audit of ${full}`,
    `Is ${full} Safe? Security Audit`,
    ...ownName.map((name) => `Is ${name} Safe? Security Audit`),
    question,
    ...ownName.map((name) => `Is ${name} Safe?`),
  ];
  const fitted = candidates.find((title) => displayWidth(title) <= TITLE_MAX_WIDTH);
  return fitted ?? `Is ${fitName(full, TITLE_MAX_WIDTH - "Is  Safe?".length)} Safe?`;
}

/** A long owner/repo gives up words from the middle, never the result. */
export function auditDescription(skill, gradeLabel, flagCount) {
  const found = flagCount ? `${flagCount} flag${flagCount > 1 ? "s" : ""} found.` : "No dangerous patterns found.";
  const result = `${found} Quality score ${Math.round(skill.quality_score || 0)}/100.`;
  const subject = `${skill.repo_full_name} security audit: graded ${gradeLabel} by`;
  const suffix = `: graded ${gradeLabel} by AgentSkillsHub. ${result}`;
  const candidates = [
    `${subject} AgentSkillsHub's rule-based security scan. ${result}`,
    `${subject} AgentSkillsHub's rule-based scan. ${result}`,
    `${subject} AgentSkillsHub. ${result}`,
    `${skill.repo_full_name}${suffix}`,
  ];
  const fitted = candidates.find((text) => text.length <= DESCRIPTION_LIMIT);
  if (fitted) return fitted;
  const budget = DESCRIPTION_LIMIT - suffix.length;
  return budget >= 12 ? `${fitName(skill.repo_full_name, budget)}${suffix}` : candidates[candidates.length - 1];
}

/**
 * dist/sitemap-audit.xml: every audit page, most-starred first. No <lastmod>: a page changes when
 * its repo is rescanned, and a date that moves with every scan is the noise that teaches Google to
 * ignore our dates (generate-sitemap.mjs, 2026-10-14).
 */
export function auditSitemap(skills, site) {
  const urls = [...skills]
    .sort((a, b) => (b.stars || 0) - (a.stars || 0))
    .map((s) => `  <url>
    <loc>${xmlText(`${site}/audit/${s.repo_full_name}/`)}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.5</priority>
  </url>`);
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.join("\n")}
</urlset>`;
}

function xmlText(text) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
