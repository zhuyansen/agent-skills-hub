/**
 * Static pages for the skills inside multi-skill repositories (scripts/sub-skills.mjs says why
 * and which ones). Runs after generate-skill-pages.mjs, which writes the repository pages:
 *
 *   dist/skill/<owner>/<repo>/<slug>/index.html   one page per published sub-skill
 *   dist/skill/<owner>/<repo>/sub-skills.json     the repository's skill list, for the React page
 *   dist/skill/<owner>/<repo>/index.html          gets a "Skills in this repository" section
 *   dist/sub-skill-pages.json                     the published URLs, for generate-sitemap.mjs
 *
 * Run: node scripts/generate-sub-skill-pages.mjs  (after generate-skill-pages.mjs)
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "fs";
import { join } from "path";
import { extractAssetTags } from "./shared-utils.mjs";
import {
  fetchSubSkills, fetchParents, selectPublished, repoLists, parentSectionHtml, buildSubSkillHtml, SUB_SKILL_MANIFEST,
} from "./sub-skills.mjs";
import { subSkillUrl } from "../src/lib/subSkillMeta.mjs";

const DIST = "dist";
const PLACEHOLDER = "<!--sub-skills: generate-sub-skill-pages.mjs puts this repository's skill list here-->";
const MANIFEST = join(DIST, SUB_SKILL_MANIFEST);

function writePage(sub, parent, list, assetTags) {
  const [owner, repo] = sub.repo_full_name.split("/");
  const dir = join(DIST, "skill", owner, repo, sub.slug);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, "index.html"), buildSubSkillHtml(sub, parent, list, assetTags));
}

const BLOCK = /<!--sub-skills:start-->[\s\S]*?<!--sub-skills:end-->/;

/** The page with the list in place: after the placeholder, or over the list an earlier run on the
 *  same dist put there; null when neither is there. (Replacer functions, since a description
 *  may hold "$&" or "$'", which a replacement string would expand.) */
function withList(html, section) {
  const block = `<!--sub-skills:start-->${section}<!--sub-skills:end-->`;
  if (BLOCK.test(html)) return html.replace(BLOCK, () => block);
  return html.includes(PLACEHOLDER) ? html.replace(PLACEHOLDER, () => PLACEHOLDER + block) : null;
}

/** The list into the repository's static page; false when that page or its placeholder is missing. */
function fillParent(repoFullName, list) {
  const [owner, repo] = repoFullName.split("/");
  const dir = join(DIST, "skill", owner, repo);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, "sub-skills.json"), JSON.stringify(list));
  const file = join(dir, "index.html");
  if (!existsSync(file)) return false;
  const html = withList(readFileSync(file, "utf-8"), parentSectionHtml(repoFullName, list));
  if (html === null) return false;
  writeFileSync(file, html);
  return true;
}

function manifestEntry(sub, parent) {
  const lastmod = (parent.last_commit_at || new Date().toISOString()).slice(0, 10);
  return { loc: subSkillUrl(sub.repo_full_name, sub.slug), lastmod };
}

async function main() {
  const assetTags = extractAssetTags(readFileSync(join(DIST, "index.html"), "utf-8"));
  const subs = await fetchSubSkills();
  const parents = await fetchParents([...new Set(subs.map((s) => s.repo_full_name))]);
  const published = selectPublished(subs, parents);
  const lists = repoLists(subs, published);
  for (const sub of published) writePage(sub, parents.get(sub.repo_full_name), lists.get(sub.repo_full_name), assetTags);
  const filled = [...lists].filter(([repo, list]) => fillParent(repo, list)).length;
  writeFileSync(MANIFEST, JSON.stringify(published.map((s) => manifestEntry(s, parents.get(s.repo_full_name)))));
  console.log(`Sub-skill pages: ${published.length} from ${subs.length} skills in ${parents.size} repositories; `
    + `lists on ${filled} of ${lists.size} repository pages`);
}

main().catch((err) => {
  console.error("Failed to generate sub-skill pages:", err);
  process.exit(1);
});
