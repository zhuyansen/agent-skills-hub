/**
 * The two counts the home page states, written into dist/index.html at build time: the catalog
 * total and how many entries carry a security grade, each rounded down to the thousand.
 *
 * Only marked places change: the three description tags, whose count is always the total, and
 * each <span data-count="total"> or <span data-count="graded"> in the page. Every other number
 * stays as written. Until 2026-11-02 the build rewrote every "X,000+" on the page to the total,
 * so "24,000+ graded so far" went live as "258,000+ graded so far", and the Dataset's 130,000+
 * (the size of the published snapshot) moved with the catalog.
 */

const ROUND_TO = 1000;

const COUNT = /\b\d{1,3}(?:,\d{3})+\+/g;

const DESCRIPTION_TAGS = [
  /(<meta name="description" content=")([^"]*)(")/,
  /(<meta property="og:description" content=")([^"]*)(")/,
  /(<meta name="twitter:description" content=")([^"]*)(")/,
];

const MARKED = /(<span data-count="(total|graded)">)[^<]*(<\/span>)/g;

/** `n` rounded down to the thousand, as the page writes it: 258901 → "258,000+". */
export function plusThousands(n) {
  return `${(Math.floor(n / ROUND_TO) * ROUND_TO).toLocaleString("en-US")}+`;
}

/** `html` with `total` and `graded` written into the places marked for them. */
export function stampHomeCounts(html, { total, graded }) {
  const text = { total: plusThousands(total), graded: plusThousands(graded) };
  const described = DESCRIPTION_TAGS.reduce(
    (out, tag) => out.replace(tag, (_, open, content, close) => open + content.replace(COUNT, text.total) + close),
    html,
  );
  return described.replace(MARKED, (_, open, kind, close) => open + text[kind] + close);
}
