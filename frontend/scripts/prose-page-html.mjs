/**
 * The static copy of a long-form page (/how-we-grade/, /agent-skills-directories/), built like
 * the Blue Book pages (generate-book-pages.mjs): a copy of dist/index.html with the page's head
 * and its whole text pre-rendered into #root, so crawlers that don't run JS read all of it.
 * React then mounts the page in its place (src/components/ProsePage.tsx), rendered from the same
 * text with the same markup. The pre-rendered copy is English; the React page follows the
 * reader's language.
 *
 * Each page's generator passes its text (ProsePageText, src/lib/proseContent.d.mts), title,
 * description, address and dates; this module writes nothing else.
 */
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { esc, replaceShellContent, SITE } from "./shared-utils.mjs";
import { CLASSES, EXTERNAL_REL, inlineTokens, linkKind, pick } from "../src/lib/proseContent.mjs";

const DIST = "dist";
const LANG = "en";
const KILOBYTE = 1024;

/* ── Body: the same markup src/components/HowWeGradeBlocks.tsx renders ──────── */

function linkHtml(token, rel) {
  const external = linkKind(token.href) === "external" ? ` target="_blank" rel="${rel}"` : "";
  return `<a href="${esc(token.href)}"${external}>${esc(token.text)}</a>`;
}

function tokenHtml(token, rel) {
  if (token.kind === "link") return linkHtml(token, rel);
  const text = esc(token.text);
  if (token.kind === "strong") return `<strong>${text}</strong>`;
  if (token.kind === "em") return `<em>${text}</em>`;
  if (token.kind === "code") return `<code>${text}</code>`;
  if (token.kind === "br") return "<br>";
  return text;
}

const inline = (text, rel) => inlineTokens(pick(text, LANG)).map((token) => tokenHtml(token, rel)).join("");
const plain = (text) => esc(pick(text, LANG));

const cellsHtml = (row, tag, attrs, rel) => row.map((cell) => `<${tag}${attrs}>${inline(cell, rel)}</${tag}>`).join("");

function tableHtml(table, rel) {
  const width = table.minRem ? ` style="min-width:${table.minRem}rem"` : "";
  const box = table.wide ? `${CLASSES.tableWrap} ${CLASSES.tableWide}` : CLASSES.tableWrap;
  const rows = table.rows.map((row) => `<tr>${cellsHtml(row, "td", "", rel)}</tr>`).join("\n");
  return `<div class="${box}" role="region" aria-label="${plain(table.label)}" tabindex="0">
<table${width}><thead><tr>${cellsHtml(table.head, "th", ' scope="col"', rel)}</tr></thead>
<tbody>
${rows}
</tbody></table>
</div>`;
}

const listHtml = (items, rel) => `<ul class="${CLASSES.list}">${items.map((item) => `<li>${inline(item, rel)}</li>`).join("")}</ul>`;

function noteHtml(note, rel) {
  const title = plain(note.title);
  return `<aside class="${CLASSES.note}" aria-label="${title}"><p><strong>${title}</strong></p>${listHtml(note.items, rel)}</aside>`;
}

function h3Html(block, rel) {
  const anchor = block.id ? ` id="${esc(block.id)}" class="${CLASSES.anchor}"` : "";
  return `<h3${anchor}>${inline(block.text, rel)}</h3>`;
}

function blockHtml(block, rel) {
  if (block.type === "p") return `<p>${inline(block.text, rel)}</p>`;
  if (block.type === "h3") return h3Html(block, rel);
  if (block.type === "ul") return listHtml(block.items, rel);
  if (block.type === "note") return noteHtml(block, rel);
  return tableHtml(block, rel);
}

const blocksHtml = (blocks, rel) => blocks.map((block) => blockHtml(block, rel)).join("\n");

function sectionHtml(section, rel) {
  return `<section id="${section.id}" class="${CLASSES.section}">
<h2>${plain(section.title)}</h2>
${blocksHtml(section.blocks, rel)}
</section>`;
}

function headerHtml(text, date) {
  const { home, here } = text.crumbs;
  return `<nav class="${CLASSES.crumbs}" aria-label="Breadcrumb"><a href="/" class="${CLASSES.crumbLink}">${plain(home)}</a><span class="${CLASSES.crumbSep}">&gt;</span><span class="${CLASSES.crumbHere}">${plain(here)}</span></nav>
<header class="${CLASSES.header}"><h1 class="${CLASSES.h1}">${plain(text.h1)}</h1>
<p class="${CLASSES.updated}">${plain(text.updated)}<time datetime="${date}">${date}</time></p></header>`;
}

/** Not wrapped in a top-level <main>/<header>: index.html hides those under #root until React mounts. */
function bodyHtml({ text, date, rel = EXTERNAL_REL }) {
  return `<div class="${CLASSES.page}"><main class="${CLASSES.main}">
${headerHtml(text, date)}
<article class="${CLASSES.article}">
${blocksHtml(text.lead, rel)}
${text.sections.map((section) => sectionHtml(section, rel)).join("\n")}
</article>
</main></div>`;
}

/* ── Head: the page's title, description, canonical and Article JSON-LD ────── */

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

/** Puts the page's values into the tags index.html has. A tag gone from index.html fails the build. */
function setHeadTags(html, values) {
  return HEAD_TAGS.reduce((out, [key, pattern]) => {
    if (!pattern.test(out)) throw new Error(`dist/index.html has no tag matching ${pattern}`);
    return out.replace(pattern, (_, open, close) => `${open}${esc(values[key])}${close}`);
  }, html);
}

/** Article markup with its dates, like every long-form page; no FAQPage. */
function articleLd({ text, description, url, published, modified }) {
  return JSON.stringify({
    "@context": "https://schema.org",
    "@type": "Article",
    headline: pick(text.h1, LANG),
    description,
    url,
    mainEntityOfPage: url,
    datePublished: published,
    dateModified: modified,
    inLanguage: LANG,
    author: { "@type": "Organization", name: "Agent Skills Hub", url: `${SITE}/` },
    publisher: { "@id": `${SITE}/#organization` },
  });
}

function headHtml(shell, page) {
  const { title, description, url } = page;
  const tags = setHeadTags(shell, { title, description, type: "article", url });
  const extra = `<link rel="canonical" href="${url}" />
    <script type="application/ld+json">${articleLd(page)}</script>
  </head>`;
  return tags.replace(/\s*<link rel="canonical"[^>]*>/g, "").replace("</head>", extra);
}

/* ── The page ─────────────────────────────────────────────────────────────── */

/**
 * dist/index.html with its build date stamped. Run on its own after `vite build`, the shell
 * still carries generate-static-pages' placeholder.
 */
export function readShell() {
  const shell = readFileSync(join(DIST, "index.html"), "utf-8");
  return shell.replaceAll("__BUILD_DATE__", new Date().toISOString().slice(0, 10));
}

/**
 * The whole static page. `page`: { text, title, description, url, published, modified,
 * date (shown after the "updated" label), rel (of links to other sites, default EXTERNAL_REL) }.
 */
export function prosePageHtml(shell, page) {
  return replaceShellContent(headHtml(shell, page), bodyHtml(page));
}

/** Writes dist/<path>index.html. */
export function writeProsePage(path, html) {
  const dir = join(DIST, path);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, "index.html"), html);
  console.log(`  ✓ ${path}index.html (pre-rendered, ${(html.length / KILOBYTE).toFixed(1)} KB)`);
}
