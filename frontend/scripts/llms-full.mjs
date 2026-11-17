/**
 * llms-full.txt: the full text of every page llms.txt lists, in one file for AI agents.
 * 哥飞's DR=0 SOP pairs an index (llms.txt) with a content file (llms-full.txt); since
 * 2026-11-16 the hub ships both. Pure functions here; generate-llms-txt.mjs reads dist/
 * and writes the file. Tested without files (node --test scripts/llms-full.test.mjs).
 *
 * Two page shapes exist: prose pages (prose-page-html.mjs) wrap their text in <main>,
 * scenario pages (generate-scenario-pages.mjs) have no <main> and carry site chrome in
 * <header id="site-header">, <nav> and <footer>. contentHtml strips the chrome and keeps
 * the page's own copy, so what an agent reads is what a non-JS crawler sees.
 */

const ENTITIES = {
  "&amp;": "&", "&quot;": '"', "&#x27;": "'", "&#39;": "'",
  "&lt;": "<", "&gt;": ">", "&nbsp;": " ",
};

const decode = (text) =>
  text.replace(/&(?:amp|quot|#x27|#39|lt|gt|nbsp);/g, (e) => ENTITIES[e] ?? e);

/** The page's own content: no scripts, styles, site header, navigation or footer. */
export function contentHtml(html) {
  let h = html
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<noscript[\s\S]*?<\/noscript>/gi, "")
    .replace(/<svg[\s\S]*?<\/svg>/gi, "")
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/<header[^>]*id=["']site-header["'][\s\S]*?<\/header>/gi, "")
    .replace(/<nav[\s\S]*?<\/nav>/gi, "")
    .replace(/<footer[\s\S]*?<\/footer>/gi, "");
  const main = h.match(/<main[^>]*>([\s\S]*?)<\/main>/i);
  if (main) return main[1];
  const body = h.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  return body ? body[1] : h;
}

/** HTML → plain markdown-ish text: headings kept, lists dashed, table rows pipe-joined. */
// Tags are matched quote-aware: about/ prose pages carry data-en/data-zh attributes whose
// values are raw HTML (<strong>, <a href='…'>) containing '>' — a naive <[^>]+> stops at
// that '>' and leaks the attribute into the text (32 such tags on /about/ alone).
const TAG = /<(\/?)([a-zA-Z][a-zA-Z0-9]*)((?:[^>"']|"[^"]*"|'[^']*')*)>/g;
const HEADING = { h1: "# ", h2: "## ", h3: "### ", h4: "#### ", h5: "#### ", h6: "#### " };
const BLOCK = new Set(["p", "div", "section", "article", "br", "ul", "ol", "table", "thead",
  "tbody", "aside", "header", "main", "figure", "figcaption", "blockquote", "pre", "hr"]);

export function htmlToText(html) {
  const h = contentHtml(html).replace(TAG, (_, slash, rawName) => {
    const name = rawName.toLowerCase();
    if (HEADING[name]) return slash ? "\n" : `\n${HEADING[name]}`;
    if (name === "li") return slash ? "" : "\n- ";
    if (name === "td" || name === "th") return slash ? " | " : "";
    if (name === "tr") return slash ? "\n" : "";
    if (BLOCK.has(name)) return "\n";
    return "";
  });
  const lines = decode(h).split("\n").map((line) =>
    line
      .replace(/[ \t]+/g, " ")
      .replace(/(\s*\|)+\s*$/, "")
      .replace(/^\s*\|(\s*\|)+/, "")
      .trim(),
  );
  const out = [];
  for (const line of lines) {
    if (!line) {
      if (out.length && out[out.length - 1] !== "") out.push("");
      continue;
    }
    out.push(line);
  }
  while (out.length && out[out.length - 1] === "") out.pop();
  return out.join("\n");
}

/** One file: a short header, then every page as "# title / URL: … / full text". */
export function buildLlmsFull(site, pages) {
  const header = [
    "# Agent Skills Hub — full text for AI agents",
    "",
    `> Companion to ${site}/llms.txt (the index). Every guide, comparison, category and key page below in full, as plain text read from the pre-rendered HTML a non-JS crawler sees. Security grades: Safe / Caution / Unsafe / Reject / Unaudited. Catalog data refreshed every 8 hours; cite the page URL, not this file.`,
    "",
  ].join("\n");
  const body = pages
    .filter((p) => p.text && p.text.trim())
    .map((p) => `# ${p.title}\n\nURL: ${site}${p.path}\n\n${p.text.trim()}\n\n---\n`)
    .join("\n");
  return `${header}\n${body}`;
}
