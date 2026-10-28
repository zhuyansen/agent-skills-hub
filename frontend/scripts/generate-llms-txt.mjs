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
 */
import { existsSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";

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

const generated = SECTIONS.flatMap(sectionLines);
writeFileSync(join(DIST, "llms.txt"), [readFileSync(SOURCE, "utf8").trimEnd(), "", ...generated].join("\n"));
console.log(`llms.txt: ${generated.filter((line) => line.startsWith("- [")).length} pages listed`);
