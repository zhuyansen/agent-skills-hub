/**
 * The parts every long-form page of the site shares: /how-we-grade/ and
 * /agent-skills-directories/. Two renderers read a page's text through these: React
 * (src/components/ProsePage.tsx and HowWeGradeBlocks.tsx) and the static generators
 * (scripts/prose-page-html.mjs), so the page crawlers read and the page Google renders
 * say the same thing and look the same.
 *
 * Text is `[english, chinese]`, or one string when both languages read the same. Inline
 * markup: **bold**, *italic*, `code`, [label](href) and \n for a line break; see inlineTokens().
 */

export const SITE_ORIGIN = "https://agentskillshub.top";

/** rel of a link to another site. */
export const EXTERNAL_REL = "noopener noreferrer";
/** rel of a link to another site that the page does not vouch for, such as a directory it compares. */
export const NOFOLLOW_REL = "nofollow noopener noreferrer";

/** Tailwind classes shared by both renderers, so the pre-rendered page looks like the React one. */
export const CLASSES = {
  page: "min-h-screen bg-gray-50 dark:bg-gray-950",
  main: "max-w-3xl mx-auto px-4 py-8",
  crumbs: "text-sm text-gray-400 dark:text-gray-500 mb-4",
  crumbLink: "text-indigo-500 hover:text-indigo-600",
  crumbSep: "mx-2",
  crumbHere: "text-gray-600 dark:text-gray-300",
  header: "mb-8 pb-6 border-b border-gray-200 dark:border-gray-700",
  h1: "text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white tracking-tight",
  updated: "mt-3 text-sm text-gray-400 dark:text-gray-500",
  article: "book-prose break-words",
  section: "scroll-mt-24",
  list: "list-disc",
  tableWrap: "overflow-x-auto",
  /**
   * Added to the box of a table too wide for the 48rem column: on laptop and desktop screens it
   * spreads into the page's side margins (lg 960px, xl 992px wide) instead of scrolling.
   */
  tableWide: "lg:-mx-28 xl:-mx-32",
  /** A heading that links point at: scrolled to, it stays clear of the sticky site header. */
  anchor: "scroll-mt-24",
  /**
   * A boxed note, such as a disclosure: the card style the Enterprise and Submit pages use.
   * Its last paragraph or list keeps the 1rem bottom margin .book-prose gives it (unlayered
   * CSS, which no utility can override), so pb-1 makes the space below match the pt-5 above.
   */
  note: "bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 px-5 pt-5 pb-1 mb-8",
};

/** The text in `lang`: a pair is [english, chinese], a plain string reads the same in both. */
export function pick(text, lang) {
  if (typeof text === "string") return text;
  return lang === "zh" ? text[1] : text[0];
}

// **bold** | *italic* | `code` | [label](href) | line break — no nesting, which this text never needs.
const INLINE = /\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\)|\n/g;

function tokenOf(m) {
  if (m[1] !== undefined) return { kind: "strong", text: m[1] };
  if (m[2] !== undefined) return { kind: "em", text: m[2] };
  if (m[3] !== undefined) return { kind: "code", text: m[3] };
  if (m[4] !== undefined) return { kind: "link", text: m[4], href: m[5] };
  return { kind: "br", text: "" };
}

/** Splits one line of inline markup into plain-text and formatted tokens, in order. */
export function inlineTokens(text) {
  const tokens = [];
  let last = 0;
  for (const m of text.matchAll(INLINE)) {
    if (m.index > last) tokens.push({ kind: "text", text: text.slice(last, m.index) });
    tokens.push(tokenOf(m));
    last = m.index + m[0].length;
  }
  if (last < text.length) tokens.push({ kind: "text", text: text.slice(last) });
  return tokens;
}

/**
 * How a link opens. "route": a path of this app, followed by its router. "page": a place on
 * this page, or a full address on this site such as a static page or a file the router does
 * not know (/about/, /llms.txt), loaded in full. "external": another site, in a new tab.
 */
export function linkKind(href) {
  if (href.startsWith("/")) return "route";
  if (href.startsWith("#") || href.startsWith(`${SITE_ORIGIN}/`)) return "page";
  return "external";
}
