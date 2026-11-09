/**
 * /how-we-grade/ — how security grades, quality scores and rankings are made (2026-10-22).
 *
 * A copy of dist/index.html with this page's head and its whole text pre-rendered into #root
 * (scripts/prose-page-html.mjs), so crawlers that don't run JS read all of it. React then mounts
 * src/pages/HowWeGradePage.tsx in its place, rendered from the same text
 * (src/lib/howWeGradeContent.mjs) with the same title and description (src/lib/howWeGradeMeta.mjs).
 *
 * Runs after generate-static-pages.mjs (which stamps the build date into dist/index.html) and
 * before generate-sitemap.mjs, which lists the page in sitemap-top.xml with the Article's
 * dateModified as lastmod. Writes dist/how-we-grade/index.html and nothing else.
 */
import {
  HOW_WE_GRADE_META,
  HOW_WE_GRADE_PATH,
  HOW_WE_GRADE_PUBLISHED,
  HOW_WE_GRADE_UPDATED,
  HOW_WE_GRADE_URL,
} from "../src/lib/howWeGradeMeta.mjs";
import { HOW_WE_GRADE } from "../src/lib/howWeGradeContent.mjs";
import { prosePageHtml, readShell, writeProsePage } from "./prose-page-html.mjs";

const html = prosePageHtml(readShell(), {
  ...HOW_WE_GRADE_META.en,
  text: HOW_WE_GRADE,
  url: HOW_WE_GRADE_URL,
  published: HOW_WE_GRADE_PUBLISHED,
  modified: HOW_WE_GRADE_UPDATED,
  date: HOW_WE_GRADE_UPDATED,
});
writeProsePage(HOW_WE_GRADE_PATH, html);
