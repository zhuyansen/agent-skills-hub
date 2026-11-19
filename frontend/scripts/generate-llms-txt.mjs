#!/usr/bin/env node
/**
 * dist/llms.txt for AI agents (2026-10-28): the hand-written public/llms.txt plus every
 * scenario guide, comparison, category and blog post, read from the sitemaps this build
 * has just written and from each page's own <title> and description.
 *
 * Before, the file named only the section indexes. Ten of the eleven /compare/ pages and
 * 23 Chinese scenario twins had no Google impression in 90 days, and agents reading this
 * file had no way to reach them. Runs after generate-sitemap.mjs; reads only dist/, so it
 * needs no database.
 *
 * Since 2026-11-09 it also gives llms.txt and dist/skill.md the catalog numbers the home page
 * states, read from the markers generate-skill-pages.mjs stamped into dist/index.html, and the
 * CLI index size from dist/search-index-meta.json (see agent-file-counts.mjs). The same numbers go
 * into the marked places of dist/about/index.html, which generate-static-pages.mjs writes before
 * the catalog is counted: until 2026-11-09 /about/ stated a count months older than the home page's.
 */
import { existsSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";
import { homeCounts, llmsRules, skillMdRules, stampRules } from "./agent-file-counts.mjs";
import { stampHomeCounts } from "./home-counts.mjs";
import { buildLlmsFull, htmlToText } from "./llms-full.mjs";
import { buildHomeMarkdown, stampHomeCanonical } from "./home-markdown.mjs";

const SITE = "https://agentskillshub.top";
const DIST = "dist";
const SOURCE = join("public", "llms.txt");
const DESCRIPTION_CHARS = 160;
// Section indexes (every page under them is listed) and the catch-all category.
const SKIPPED = new Set(["/compare/", "/blog/", "/blog/zh/", "/category/uncategorized/"]);

const SECTIONS = [
  { title: "Scenario guides", sitemap: "sitemap-scenarios.xml", keep: (path) => !path.endsWith("/zh/") },
  { title: "Head-to-head comparisons", sitemap: "sitemap-comparisons.xml", keep: () => true },
  { title: "Categories", sitemap: "sitemap-categories.xml", keep: () => true },
  { title: "Blog", sitemap: "sitemap-blog.xml", keep: () => true },
  { title: "中文指南 (scenario guides in Chinese)", sitemap: "sitemap-scenarios.xml", keep: (path) => path.endsWith("/zh/") },
];

const ENTITIES = { "&amp;": "&", "&quot;": '"', "&#x27;": "'", "&#39;": "'", "&lt;": "<", "&gt;": ">" };
/** Attribute or element text as one plain line. */
const decode = (text) => text.replace(/&(?:amp|quot|#x27|#39|lt|gt);/g, (e) => ENTITIES[e]).replace(/\s+/g, " ").trim();

/** At most DESCRIPTION_CHARS, cut at a space when there is one (Chinese has none). */
function clip(text) {
  if (text.length <= DESCRIPTION_CHARS) return text;
  const cut = text.lastIndexOf(" ", DESCRIPTION_CHARS);
  return `${text.slice(0, cut > 0 ? cut : DESCRIPTION_CHARS).replace(/[\s,;:]+$/, "")}…`;
}

/** The page's title (without the site name) and description, or null when it was not built. */
function pageInfo(path) {
  const file = join(DIST, ...path.split("/").filter(Boolean), "index.html");
  if (!existsSync(file)) return null;
  const html = readFileSync(file, "utf8");
  const title = html.match(/<title>([^<]*)<\/title>/)?.[1];
  if (!title) return null;
  const description = html.match(/<meta name="description" content="([^"]*)"/)?.[1] || "";
  const name = decode(title).replace(/ \| Agent Skills Hub$/, "").replace(/[[\]]/g, "\\$&"); // brackets would end the link text
  return { title: name, description: decode(description) };
}

function sectionLines({ title, sitemap, keep }) {
  const file = join(DIST, sitemap);
  if (!existsSync(file)) return [];
  const paths = [...readFileSync(file, "utf8").matchAll(/<loc>([^<]+)<\/loc>/g)]
    .map((m) => m[1].replace(SITE, ""))
    .filter((path) => !SKIPPED.has(path) && keep(path));
  const lines = paths.flatMap((path) => {
    const info = pageInfo(path);
    return info ? [`- [${info.title}](${SITE}${path})${info.description ? `: ${clip(info.description)}` : ""}`] : [];
  });
  return lines.length ? [`## ${title}`, "", ...lines, ""] : [];
}

const counts = homeCounts(readFileSync(join(DIST, "index.html"), "utf8"));
const indexCount = JSON.parse(readFileSync(join(DIST, "search-index-meta.json"), "utf8")).count;

const generated = SECTIONS.flatMap(sectionLines);
const header = stampRules(readFileSync(SOURCE, "utf8").trimEnd(), llmsRules(counts), "llms.txt");
writeFileSync(join(DIST, "llms.txt"), [header, "", ...generated].join("\n"));
console.log(`llms.txt: ${generated.filter((line) => line.startsWith("- [")).length} pages listed`);

// llms-full.txt (2026-11-16): the same pages in full text, the SOP pair to the index.
// Key prose pages first, then every section page llms.txt lists (EN + zh scenarios).
const KEY_PATHS = ["/about/", "/how-we-grade/", "/ai-info/", "/agent-skills-directories/", "/enterprise/", "/best/", "/book/"];
const fullPaths = [...new Set([
  ...KEY_PATHS,
  ...SECTIONS.flatMap(({ sitemap, keep }) => {
    const file = join(DIST, sitemap);
    if (!existsSync(file)) return [];
    return [...readFileSync(file, "utf8").matchAll(/<loc>([^<]+)<\/loc>/g)]
      .map((m) => m[1].replace(SITE, ""))
      .filter((path) => !SKIPPED.has(path) && keep(path));
  }),
])];
const fullPages = fullPaths.flatMap((path) => {
  const file = join(DIST, ...path.split("/").filter(Boolean), "index.html");
  if (!existsSync(file)) return [];
  const html = readFileSync(file, "utf8");
  const rawTitle = html.match(/<title>([^<]*)<\/title>/)?.[1];
  const text = htmlToText(html);
  if (!rawTitle || !text.trim()) return [];
  return [{ path, title: decode(rawTitle).replace(/ \| Agent Skills Hub$/, ""), text }];
});
const full = buildLlmsFull(SITE, fullPages);
writeFileSync(join(DIST, "llms-full.txt"), full);
console.log(`llms-full.txt: ${fullPages.length} pages, ${(full.length / 1024).toFixed(0)} KB`);

const SKILL_MD = join(DIST, "skill.md");
writeFileSync(SKILL_MD, stampRules(readFileSync(SKILL_MD, "utf8"), skillMdRules(counts, indexCount), "skill.md"));
console.log(`llms.txt and skill.md: ${counts.total} skills, ${counts.graded} graded, CLI index ${indexCount}`);

const ABOUT = join(DIST, "about", "index.html");
writeFileSync(ABOUT, stampHomeCounts(readFileSync(ABOUT, "utf8"), counts));
console.log(`/about/: ${counts.total} skills`);

const AI_INFO = join(DIST, "ai-info", "index.html");
if (existsSync(AI_INFO)) {
  writeFileSync(AI_INFO, stampHomeCounts(readFileSync(AI_INFO, "utf8"), counts));
  console.log(`/ai-info/: ${counts.total} skills, ${counts.graded} graded`);
}

const HOME_INDEX = join(DIST, "index.html");
writeFileSync(HOME_INDEX, stampHomeCanonical(readFileSync(HOME_INDEX, "utf8"), SITE));
const homeMd = buildHomeMarkdown({
  site: SITE,
  counts,
  indexCount,
  generatedDate: new Date().toISOString().slice(0, 10),
});
writeFileSync(join(DIST, "index.md"), homeMd);
console.log(`index.html canonical stamped; index.md written (${(homeMd.length / 1024).toFixed(1)} KB)`);
