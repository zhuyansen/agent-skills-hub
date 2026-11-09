/**
 * /agent-skills-directories/: where to find agent skills and MCP servers, the directories
 * compared from their own pages, ours included (2026-11-10).
 *
 * A copy of dist/index.html with the page's head and its whole text pre-rendered into #root
 * (prose-page-html.mjs), so crawlers that don't run JS read all of it. React then mounts
 * src/pages/DirectoriesPage.tsx in its place, from the same text (src/lib/directoriesContent.mjs)
 * with the same title and description (src/lib/directoriesMeta.mjs).
 *
 * Our catalog count is the one the home page states: the data-count markers that
 * generate-skill-pages.mjs stamps into dist/index.html (homeCounts). So this runs after that
 * step, and before generate-sitemap.mjs, which lists the page in sitemap-top.xml with the
 * Article's dateModified as lastmod. It reads only dist/ and needs no database: after a plain
 * `vite build` the markers still hold the numbers index.html was written with. Writes
 * dist/agent-skills-directories/index.html and nothing else.
 */
import { homeCounts } from "./agent-file-counts.mjs";
import { prosePageHtml, readShell, writeProsePage } from "./prose-page-html.mjs";
import { ABOUT_HALF, directoriesText } from "../src/lib/directoriesContent.mjs";
import {
  DIRECTORIES_META,
  DIRECTORIES_PATH,
  DIRECTORIES_PUBLISHED,
  DIRECTORIES_UPDATED,
  DIRECTORIES_URL,
  FACTS_READ_ON,
} from "../src/lib/directoriesMeta.mjs";
import { NOFOLLOW_REL } from "../src/lib/proseContent.mjs";

const PERCENT = 100;

/** "132,000+" → 132000. */
const countOf = (text) => Number(text.replace(/\D/g, ""));

/**
 * Our entry says about half of the catalog is graded. A build whose counts say otherwise still
 * ships (a sync must never stop a deploy), but says so in the log.
 */
function gradedShare(counts) {
  const share = countOf(counts.graded) / countOf(counts.total);
  const shown = `${Math.round(share * PERCENT)}%`;
  if (share < ABOUT_HALF.min || share > ABOUT_HALF.max) {
    console.warn(`  ⚠ ${DIRECTORIES_PATH} says about half of the catalog is graded, but this build counts ${shown} (${counts.graded} of ${counts.total}): reword the size fact in src/lib/directoryEntries.mjs.`);
  }
  return shown;
}

const shell = readShell();
const counts = homeCounts(shell);
const share = gradedShare(counts);
const html = prosePageHtml(shell, {
  ...DIRECTORIES_META.en,
  text: directoriesText(counts.total),
  url: DIRECTORIES_URL,
  published: DIRECTORIES_PUBLISHED,
  modified: DIRECTORIES_UPDATED,
  date: FACTS_READ_ON,
  rel: NOFOLLOW_REL,
});
writeProsePage(DIRECTORIES_PATH, html);
console.log(`    our catalog: ${counts.total} repos, ${share} graded`);
