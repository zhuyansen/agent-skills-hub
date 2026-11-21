/**
 * The <head> of an SPA shell (generate-static-pages.mjs): dist/index.html with the shell's own
 * title, description, canonical and share card.
 *
 * Until 2026-11-20 a shell replaced only the first three and kept the home page's og: and
 * twitter: tags. A link preview is built from those tags without running JavaScript, and the
 * React pages do not set them either, so /analyzer/, /enterprise/ and every
 * /analyzer?repo=… or /org-audit/?owner=… share link unfurled as the home page, pointing at
 * the home address.
 */
import { esc } from "./shared-utils.mjs";

const SITE = "https://agentskillshub.top";

/** Sets one <meta> tag's content. The value is written literally: a "$" in the copy stays a "$". */
function setMeta(html, selector, value) {
  const tag = new RegExp(`<meta ${selector} content="[^"]*"`);
  return html.replace(tag, () => `<meta ${selector} content="${value}"`);
}

/** The share card: the tags a link preview reads. Text is escaped for an attribute. */
function setShareCard(html, { title, description, url }) {
  const card = [
    ['property="og:title"', esc(title)],
    ['name="twitter:title"', esc(title)],
    ['property="og:description"', esc(description)],
    ['name="twitter:description"', esc(description)],
    ['property="og:url"', url],
  ];
  return card.reduce((out, [selector, value]) => setMeta(out, selector, value), html);
}

/** index.html offers /index.md as its Markdown twin. That file is the home page's, not a shell's. */
const HOME_MARKDOWN_LINK = /\s*<link rel="alternate" type="text\/markdown"[^>]*>/;

/**
 * index.html's markup with the head of one shell. `html` must already carry a canonical tag
 * (generate-static-pages.mjs injects a placeholder). A member page (`noindex`) says so in the raw
 * HTML, for crawlers that do not run the page's own Helmet tag.
 */
export function shellHead(html, { path, title, description, noindex = false }) {
  const url = `${SITE}/${path}/`;
  const head = html
    .replace(/<title>[^<]+<\/title>/, () => `<title>${title}</title>`)
    .replace(/<meta name="description" content="[^"]+"/, () => `<meta name="description" content="${description}"`)
    .replace(/<link rel="canonical" href="[^"]+"/, () => `<link rel="canonical" href="${url}"`)
    .replace(HOME_MARKDOWN_LINK, "");
  const withCard = setShareCard(head, { title, description, url });
  return noindex ? withCard.replace("</head>", '<meta name="robots" content="noindex" />\n</head>') : withCard;
}
