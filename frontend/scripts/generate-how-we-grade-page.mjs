/**
 * /how-we-grade/ — how security grades, quality scores and rankings are made (2026-10-22).
 *
 * Built like the Blue Book pages (generate-book-pages.mjs): a copy of dist/index.html with
 * this page's head and its whole text pre-rendered into #root, so crawlers that don't run JS
 * read all of it. React then mounts src/pages/HowWeGradePage.tsx in its place, rendered from
 * the same text (src/lib/howWeGradeContent.mjs) with the same title and description
 * (src/lib/howWeGradeMeta.mjs). The pre-rendered copy is English; the React page follows the
 * reader's language.
 *
 * Runs after generate-static-pages.mjs (which stamps the build date into dist/index.html) and
 * before generate-sitemap.mjs, which lists the page in sitemap-top.xml with the Article's
 * dateModified as lastmod. Writes dist/how-we-grade/index.html and nothing else.
 */
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { esc, replaceShellContent, SITE } from "./shared-utils.mjs";
import {
  HOW_WE_GRADE_META,
  HOW_WE_GRADE_PATH,
  HOW_WE_GRADE_PUBLISHED,
  HOW_WE_GRADE_UPDATED,
  HOW_WE_GRADE_URL,
} from "../src/lib/howWeGradeMeta.mjs";
import { CLASSES, HOW_WE_GRADE, inlineTokens, pick } from "../src/lib/howWeGradeContent.mjs";

const DIST = "dist";
const LANG = "en";

/* ── Body: the same markup src/components/HowWeGradeBlocks.tsx renders ──────── */

function tokenHtml(token) {
  const text = esc(token.text);
  if (token.kind === "strong") return `<strong>${text}</strong>`;
  if (token.kind === "em") return `<em>${text}</em>`;
  if (token.kind === "code") return `<code>${text}</code>`;
  if (token.kind === "br") return "<br>";
  if (token.kind !== "link") return text;
  const external = token.href.startsWith("/") ? "" : ' target="_blank" rel="noopener noreferrer"';
  return `<a href="${esc(token.href)}"${external}>${text}</a>`;
}

const inline = (text) => inlineTokens(pick(text, LANG)).map(tokenHtml).join("");
const plain = (text) => esc(pick(text, LANG));

const cellsHtml = (row, tag, attrs = "") => row.map((cell) => `<${tag}${attrs}>${inline(cell)}</${tag}>`).join("");

function tableHtml(table) {
  const width = table.minRem ? ` style="min-width:${table.minRem}rem"` : "";
  const rows = table.rows.map((row) => `<tr>${cellsHtml(row, "td")}</tr>`).join("\n");
  return `<div class="${CLASSES.tableWrap}" role="region" aria-label="${plain(table.label)}" tabindex="0">
<table${width}><thead><tr>${cellsHtml(table.head, "th", ' scope="col"')}</tr></thead>
<tbody>
${rows}
</tbody></table>
</div>`;
}

function blockHtml(block) {
  if (block.type === "p") return `<p>${inline(block.text)}</p>`;
  if (block.type === "h3") return `<h3>${inline(block.text)}</h3>`;
  if (block.type === "ul") return `<ul class="${CLASSES.list}">${block.items.map((item) => `<li>${inline(item)}</li>`).join("")}</ul>`;
  return tableHtml(block);
}

const blocksHtml = (blocks) => blocks.map(blockHtml).join("\n");

function sectionHtml(section) {
  return `<section id="${section.id}" class="${CLASSES.section}">
<h2>${plain(section.title)}</h2>
${blocksHtml(section.blocks)}
</section>`;
}

function headerHtml(page) {
  const { home, here } = page.crumbs;
  return `<nav class="${CLASSES.crumbs}" aria-label="Breadcrumb"><a href="/" class="${CLASSES.crumbLink}">${plain(home)}</a><span class="${CLASSES.crumbSep}">&gt;</span><span class="${CLASSES.crumbHere}">${plain(here)}</span></nav>
<header class="${CLASSES.header}"><h1 class="${CLASSES.h1}">${plain(page.h1)}</h1>
<p class="${CLASSES.updated}">${plain(page.updated)}<time datetime="${HOW_WE_GRADE_UPDATED}">${HOW_WE_GRADE_UPDATED}</time></p></header>`;
}

/** Not wrapped in a top-level <main>/<header>: index.html hides those under #root until React mounts. */
function bodyHtml(page) {
  return `<div class="${CLASSES.page}"><main class="${CLASSES.main}">
${headerHtml(page)}
<article class="${CLASSES.article}">
${blocksHtml(page.lead)}
${page.sections.map(sectionHtml).join("\n")}
</article>
</main></div>`;
}

/* ── Head: this page's title, description, canonical and Article JSON-LD ────── */

const HEAD_TAGS = [
  ["title", /(<title>)[^<]*(<\/title>)/],
  ["description", /(<meta name="description" content=")[^"]*(")/],
  ["title", /(<meta property="og:title" content=")[^"]*(")/],
  ["description", /(<meta property="og:description" content=")[^"]*(")/],
  ["type", /(<meta property="og:type" content=")[^"]*(")/],
  ["url", /(<meta property="og:url" content=")[^"]*(")/],
  ["title", /(<meta name="twitter:title" content=")[^"]*(")/],
  ["description", /(<meta name="twitter:description" content=")[^"]*(")/],
];

/** Puts this page's values into the tags index.html has. A tag gone from index.html fails the build. */
function setHeadTags(html, values) {
  return HEAD_TAGS.reduce((out, [key, pattern]) => {
    if (!pattern.test(out)) throw new Error(`dist/index.html has no tag matching ${pattern}`);
    return out.replace(pattern, (_, open, close) => `${open}${esc(values[key])}${close}`);
  }, html);
}

function articleLd(description) {
  return JSON.stringify({
    "@context": "https://schema.org",
    "@type": "Article",
    headline: pick(HOW_WE_GRADE.h1, LANG),
    description,
    url: HOW_WE_GRADE_URL,
    mainEntityOfPage: HOW_WE_GRADE_URL,
    datePublished: HOW_WE_GRADE_PUBLISHED,
    dateModified: HOW_WE_GRADE_UPDATED,
    inLanguage: LANG,
    author: { "@type": "Organization", name: "Agent Skills Hub", url: `${SITE}/` },
    publisher: { "@id": `${SITE}/#organization` },
  });
}

function headHtml(shell) {
  const { title, description } = HOW_WE_GRADE_META[LANG];
  const tags = setHeadTags(shell, { title, description, type: "article", url: HOW_WE_GRADE_URL });
  const extra = `<link rel="canonical" href="${HOW_WE_GRADE_URL}" />
    <script type="application/ld+json">${articleLd(description)}</script>
  </head>`;
  return tags.replace(/\s*<link rel="canonical"[^>]*>/g, "").replace("</head>", extra);
}

function main() {
  const shell = readFileSync(join(DIST, "index.html"), "utf-8");
  // Run on its own after `vite build`, the shell still carries generate-static-pages' placeholder.
  const stamped = shell.replaceAll("__BUILD_DATE__", new Date().toISOString().slice(0, 10));
  const html = replaceShellContent(headHtml(stamped), bodyHtml(HOW_WE_GRADE));
  const dir = join(DIST, HOW_WE_GRADE_PATH);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, "index.html"), html);
  console.log(`  ✓ ${HOW_WE_GRADE_PATH}index.html (pre-rendered, ${(html.length / 1024).toFixed(1)} KB)`);
}

main();
