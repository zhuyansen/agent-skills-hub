/**
 * The A–Z directory: plain pages that link every indexable /skill/ and /audit/ page, so each
 * one is two clicks from the footer of any static page (Eli Schwartz, Product-Led SEO,
 * pp. 129–130, on HTML sitemaps). Category pages list only their first 100 repos, and the
 * sitemaps leave out most skill pages on purpose (generate-sitemap.mjs), so without this a page
 * that is neither popular nor new had no link from anywhere.
 *
 * Layout: /browse/ lists the letters of both sections with their counts; each letter has pages
 * of at most PAGE_SIZE links at /browse/<section>/<letter>/ and /browse/<section>/<letter>/<n>/.
 * Pure functions here; generate-browse-pages.mjs reads dist/ and writes the files.
 *
 * Test: node --test scripts/browse-pages.test.mjs
 */
import { SITE, analyticsTags, biAttrs, esc } from "./shared-utils.mjs";

export const BROWSE_PATH = "/browse/";
export const PAGE_SIZE = 500;

export const SECTIONS = {
  skills: {
    base: "/skill/",
    en: "Skill pages", zh: "技能页",
    introEn: "Every indexed skill and MCP server page on Agent Skills Hub, sorted by owner/repo.",
    introZh: "Agent Skills Hub 所有可被索引的技能和 MCP 服务器页面，按 owner/repo 排序。",
  },
  audits: {
    base: "/audit/",
    en: "Security audits", zh: "安全审计",
    introEn: "Every security audit page on Agent Skills Hub, sorted by owner/repo.",
    introZh: "Agent Skills Hub 所有安全审计页面，按 owner/repo 排序。",
  },
};

/** "a"…"z" by the first character of owner/repo, "0-9" for a digit, "other" for anything else. */
export function letterOf(name) {
  const ch = String(name || "").charAt(0).toLowerCase();
  if (ch >= "a" && ch <= "z") return ch;
  return ch >= "0" && ch <= "9" ? "0-9" : "other";
}

const LETTER_ORDER = ["0-9", ..."abcdefghijklmnopqrstuvwxyz", "other"];
const byName = (a, b) => a.toLowerCase().localeCompare(b.toLowerCase(), "en") || a.localeCompare(b);

/** Path of page `n` (1-based) of a letter. */
export function pagePath(section, letter, n) {
  return `${BROWSE_PATH}${section}/${letter}/${n > 1 ? `${n}/` : ""}`;
}

/**
 * Names (owner/repo, or owner/repo/sub) -> one entry per page to write:
 * { section, letter, n, of, start, path, names }; `start` is the number of its first link.
 */
export function paginate(section, names, size = PAGE_SIZE) {
  const groups = new Map();
  for (const name of [...names].sort(byName)) {
    const letter = letterOf(name);
    if (!groups.has(letter)) groups.set(letter, []);
    groups.get(letter).push(name);
  }
  const pages = [];
  for (const letter of LETTER_ORDER.filter((l) => groups.has(l))) {
    const list = groups.get(letter);
    const of = Math.ceil(list.length / size);
    for (let n = 1; n <= of; n++) {
      const start = (n - 1) * size;
      pages.push({ section, letter, n, of, start: start + 1, path: pagePath(section, letter, n), names: list.slice(start, start + size) });
    }
  }
  return pages;
}

/** letter -> link count, in display order. */
export function letterCounts(pages) {
  const counts = new Map();
  for (const p of pages) counts.set(p.letter, (counts.get(p.letter) || 0) + p.names.length);
  return counts;
}

const LANG_SCRIPT = `<script>(function(){try{var l=localStorage.getItem('lang')||(navigator.language&&navigator.language.toLowerCase().indexOf('zh')===0?'zh':'en');if(l==='zh'){document.documentElement.lang='zh-CN';document.querySelectorAll('[data-zh]').forEach(function(e){e.textContent=e.getAttribute('data-zh')})}}catch(e){}})();</script>`;

function shell({ title, description, path, prev, next, body }) {
  const url = `${SITE}${path}`;
  const rel = (name, p) => (p ? `\n  <link rel="${name}" href="${SITE}${p}" />` : "");
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${esc(title)}</title>
  <meta name="description" content="${esc(description)}" />
  <link rel="canonical" href="${esc(url)}" />${rel("prev", prev)}${rel("next", next)}
  <meta property="og:title" content="${esc(title)}" />
  <meta property="og:url" content="${esc(url)}" />
  <meta property="og:site_name" content="Agent Skills Hub" />
${analyticsTags()}
</head>
<body style="margin:0;font-family:system-ui,-apple-system,sans-serif;color:#1e293b;background:#fff">
  <div style="max-width:880px;margin:0 auto;padding:32px 20px">
${body}
  </div>
  ${LANG_SCRIPT}
</body>
</html>`;
}

const A = "color:#4f46e5;text-decoration:none";
const label = (en, zh) => `<span ${biAttrs(en, zh)}>${esc(en)}</span>`;

function lettersNav(pages, current = null) {
  const first = pages.filter((p) => p.n === 1);
  return first.map((p) => (p.letter === current
    ? `<strong style="padding:2px 6px">${p.letter.toUpperCase()}</strong>`
    : `<a href="${p.path}" style="${A};padding:2px 6px">${p.letter.toUpperCase()}</a>`)).join(" ");
}

const linkCount = (pages) => pages.reduce((sum, p) => sum + p.names.length, 0);

/** One section of the hub: its letters, each with the number of links under it. */
function hubSection(key, pages) {
  const s = SECTIONS[key];
  const rows = [...letterCounts(pages)].map(([letter, count]) =>
    `<li style="margin:3px 0"><a href="${pagePath(key, letter, 1)}" style="${A}">${letter.toUpperCase()}</a> <span style="color:#94a3b8">(${count.toLocaleString("en-US")})</span></li>`);
  return `    <section id="${key}" style="margin:28px 0">
      <h2 style="font-size:20px;margin:0 0 6px">${label(s.en, s.zh)} <span style="color:#94a3b8;font-weight:400">(${linkCount(pages).toLocaleString("en-US")})</span></h2>
      <p style="color:#64748b;margin:0 0 10px;font-size:14px" ${biAttrs(s.introEn, s.introZh)}>${esc(s.introEn)}</p>
      <ul style="columns:4 140px;padding-left:18px;margin:0;font-size:15px">
        ${rows.join("\n        ")}
      </ul>
    </section>`;
}

/** The /browse/ hub. `sections` = { skills: pages[], audits: pages[] }. */
export function hubHtml(sections) {
  const count = linkCount(sections.skills) + linkCount(sections.audits);
  const intro = ["Plain lists of every skill page and security audit we publish, so each one is a click away.", "我们发布的每个技能页和安全审计都列在这里，点一下就能到。"];
  return shell({
    title: "Browse All Skills & Security Audits A–Z | Agent Skills Hub",
    description: `Every indexed skill page and security audit on Agent Skills Hub, A–Z: ${count.toLocaleString("en-US")} pages in plain lists, ${PAGE_SIZE} per page.`,
    path: BROWSE_PATH,
    body: `    <nav style="font-size:13px;color:#64748b;margin-bottom:16px"><a href="/" style="${A}">${label("Home", "首页")}</a> &gt; ${label("Browse A–Z", "按字母浏览")}</nav>
    <h1 style="font-size:28px;margin:0 0 8px">${label("Browse every page A–Z", "按字母浏览全部页面")}</h1>
    <p style="color:#64748b;margin:0" ${biAttrs(...intro)}>${esc(intro[0])}</p>
${hubSection("skills", sections.skills)}
${hubSection("audits", sections.audits)}`,
  });
}

function pagerHtml(prev, next) {
  return [
    prev ? `<a href="${prev}" style="${A}" rel="prev">&larr; ${label("Previous", "上一页")}</a>` : "",
    next ? `<a href="${next}" style="${A}" rel="next">${label("Next", "下一页")} &rarr;</a>` : "",
  ].filter(Boolean).join(" &middot; ");
}

/** One listing page. `all` = every page of the section (for the letter bar and prev/next). */
export function listHtml(page, all) {
  const s = SECTIONS[page.section];
  const L = page.letter.toUpperCase();
  const idx = all.indexOf(page);
  const prev = idx > 0 ? all[idx - 1].path : null;
  const next = idx < all.length - 1 ? all[idx + 1].path : null;
  const part = page.of > 1 ? `, page ${page.n} of ${page.of}` : "";
  const partZh = page.of > 1 ? `，第 ${page.n}/${page.of} 页` : "";
  const items = page.names.map((name) => `<li><a href="${s.base}${esc(name)}/" style="${A}">${esc(name)}</a></li>`);
  return shell({
    title: `${s.en} ${L}${part} | Agent Skills Hub`,
    description: `${s.en} on Agent Skills Hub starting with ${L}${part}: ${page.names.length} links, A–Z.`,
    path: page.path,
    prev,
    next,
    body: `    <nav style="font-size:13px;color:#64748b;margin-bottom:16px"><a href="/" style="${A}">${label("Home", "首页")}</a> &gt; <a href="${BROWSE_PATH}#${page.section}" style="${A}">${label("Browse A–Z", "按字母浏览")}</a> &gt; ${label(s.en, s.zh)} &gt; ${L}</nav>
    <h1 style="font-size:26px;margin:0 0 8px"><span ${biAttrs(`${s.en}: ${L}${part}`, `${s.zh}：${L}${partZh}`)}>${esc(`${s.en}: ${L}${part}`)}</span></h1>
    <p style="font-size:14px;margin:0 0 16px">${lettersNav(all, page.letter)}</p>
    <ol start="${page.start}" style="columns:2 320px;padding-left:44px;line-height:1.8;font-size:14px;margin:0">
      ${items.join("\n      ")}
    </ol>
    <p style="margin:20px 0 0;font-size:14px">${pagerHtml(prev, next)}</p>`,
  });
}
