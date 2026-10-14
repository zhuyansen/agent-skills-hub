/**
 * Chinese twins of the /best/ pages at /best/<slug>/zh/ (2026-10-14, owner's option A).
 *
 * The scenario pages already carry both languages in data-en / data-zh attributes,
 * swapped by script, so Google only ever read the English text: Chinese queries were
 * 0.3% of our impressions over 90 days. The twin is the same page with the Chinese
 * text written into the HTML, lang="zh-CN", its own canonical, and hreflang on both
 * versions. Skill pages get no twin: Google already knows only a third of our URLs.
 */
import { esc } from "./shared-utils.mjs";

const SITE = "https://agentskillshub.top";

export const zhPathOf = (enPath) => `${enPath}zh/`;

/** hreflang links for a page that has a Chinese twin; goes into both heads. */
export function hreflangTags(enPath) {
  const en = `${SITE}${enPath}`;
  const zh = `${SITE}${zhPathOf(enPath)}`;
  return `<link rel="alternate" hreflang="en" href="${en}" />
  <link rel="alternate" hreflang="zh" href="${zh}" />
  <link rel="alternate" hreflang="x-default" href="${en}" />`;
}

/** Adds the hreflang links to a page's head. */
export const withHreflang = (html, enPath) => html.replace("</head>", `  ${hreflangTags(enPath)}\n</head>`);

// Every element carrying data-zh gets its Chinese text written in, the same swap the
// page script does at runtime (textContent, so nested markup is flattened there too).
const OPEN_BILINGUAL = /<(\w+)\b[^>]*\bdata-zh="([^"]*)"[^>]*>/g;

/** Index just past the close tag matching an element opened before `from`. */
function closeOf(html, tag, from) {
  const re = new RegExp(`<(/?)${tag}\\b[^>]*>`, "gi");
  re.lastIndex = from;
  let depth = 1;
  for (let m = re.exec(html); m; m = re.exec(html)) {
    depth += m[1] ? -1 : m[0].endsWith("/>") ? 0 : 1;
    if (depth === 0) return { start: m.index, end: re.lastIndex };
  }
  return null;
}

function writeChinese(html) {
  let out = "";
  let pos = 0;
  OPEN_BILINGUAL.lastIndex = 0;
  for (let m = OPEN_BILINGUAL.exec(html); m; m = OPEN_BILINGUAL.exec(html)) {
    if (m.index < pos) continue; // inside an element already rewritten
    const openEnd = m.index + m[0].length;
    const close = closeOf(html, m[1], openEnd);
    if (!close) continue;
    out += html.slice(pos, openEnd) + m[2];
    pos = close.start;
    OPEN_BILINGUAL.lastIndex = close.start;
  }
  return out + html.slice(pos);
}

/** Points links to other pages that have a twin at the twin. */
function linkTwins(html, twinPaths) {
  return html.replace(/href="(\/best\/(?:[^"/]+\/)?)"/g, (m, path) => (twinPaths.has(path) ? `href="${zhPathOf(path)}"` : m));
}

function setHead(html, { zhPath, title, description }) {
  const url = `${SITE}${zhPath}`;
  return html
    .replace(/<html lang="[^"]*">/, '<html lang="zh-CN">')
    .replace(/<title>[^<]*<\/title>/, `<title>${esc(title)}</title>`)
    .replace(/(<meta name="description" content=")[^"]*(")/, `$1${esc(description)}$2`)
    .replace(/(<meta property="og:title" content=")[^"]*(")/, `$1${esc(title)}$2`)
    .replace(/(<meta property="og:description" content=")[^"]*(")/, `$1${esc(description)}$2`)
    .replace(/(<meta property="og:url" content=")[^"]*(")/, `$1${url}$2`)
    .replace(/(<link rel="canonical" href=")[^"]*(")/, `$1${url}$2`);
}

/** The H1's Chinese text, used as the Chinese <title>. */
function zhHeading(html) {
  const m = html.match(/<h1\b[^>]*\bdata-zh="([^"]*)"/);
  return m ? m[1].replace(/&amp;/g, "&").replace(/&quot;/g, '"') : null;
}

/**
 * The Chinese twin of a built English page (whose head already has the hreflang links).
 * `title` falls back to the H1's Chinese text; `twinPaths` are the English paths that
 * have a twin, so links between twins stay in Chinese.
 */
export function zhTwin(enHtml, { enPath, title, description, twinPaths }) {
  const zhTitle = title || zhHeading(enHtml) || "";
  const head = setHead(enHtml, { zhPath: zhPathOf(enPath), title: zhTitle, description });
  return linkTwins(writeChinese(head), twinPaths);
}
