/**
 * The numbers the home page states, counted at build time and written into dist/index.html: the
 * catalog total and the graded rows, rounded down to the thousand, and the graded share of the
 * skills above each star tier, rounded down to a whole percent. The hero also gets the exact
 * count of every row and of each category, as JSON in a slot of its own (catalogCounts).
 *
 * Only marked places change: the three description tags, whose count is always the total, and
 * each <span data-count="…">, which takes the text for its marker. Every other number stays as
 * written. Until 2026-11-02 the build rewrote every "X,000+" on the page to the total, so
 * "24,000+ graded so far" went live as "258,000+ graded so far", and the Dataset's 130,000+
 * (the size of the published snapshot) moved with the catalog.
 */
import { gradeState } from "./shared-utils.mjs";

const ROUND_TO = 1000;
const PERCENT = 100;

/** Each tier is stated as data-count="graded-over-<stars>": the share of skills above it with a grade. */
const STAR_TIERS = [100, 1000];

const COUNT = /\b\d{1,3}(?:,\d{3})+\+/g;

const DESCRIPTION_TAGS = [
  /(<meta name="description" content=")([^"]*)(")/,
  /(<meta property="og:description" content=")([^"]*)(")/,
  /(<meta name="twitter:description" content=")([^"]*)(")/,
];

const MARKED = /<span data-count="([^"]*)">[^<]*<\/span>/g;

/** Where index.html holds the exact counts the hero paints before the stats arrive (src/lib/catalogCounts.ts). */
const CATALOG_SLOT = /(<script id="catalog-counts" type="application\/json">)[^<]*(<\/script>)/;

const isGraded = (s) => gradeState(s) === "graded";

/** `n` rounded down to the thousand, as the page writes it: 258901 → "258,000+". */
export function plusThousands(n) {
  return `${(Math.floor(n / ROUND_TO) * ROUND_TO).toLocaleString("en-US")}+`;
}

/** `part` of `whole` as a whole percent, rounded down: 10584 of 10665 → "99%". */
export function percentDown(part, whole) {
  return `${whole ? Math.floor((part * PERCENT) / whole) : 0}%`;
}

/** The text for each data-count marker, counted from every catalog row. */
export function homeCountTexts(skills) {
  const texts = { total: plusThousands(skills.length), graded: plusThousands(skills.filter(isGraded).length) };
  for (const stars of STAR_TIERS) {
    const tier = skills.filter((s) => s.stars > stars);
    texts[`graded-over-${stars}`] = percentDown(tier.filter(isGraded).length, tier.length);
  }
  return texts;
}

/** `html` with each marked place set to its text in `texts`; the description tags take the total. */
export function stampHomeCounts(html, texts) {
  const described = DESCRIPTION_TAGS.reduce(
    (out, tag) => out.replace(tag, (_, open, content, close) => open + content.replace(COUNT, texts.total) + close),
    html,
  );
  return described.replace(MARKED, (_, key) => {
    if (!Object.hasOwn(texts, key)) throw new Error(`index.html marks data-count="${key}", which the build does not count`);
    return `<span data-count="${key}">${texts[key]}</span>`;
  });
}

/**
 * The catalog's exact counts, every row and the rows in each category: the numbers the hero shows
 * once the stats arrive (v_stats and v_categories count the same rows). With them in the page the
 * first paint has as many digits as the live numbers, whichever count gains one next.
 */
export function catalogCounts(skills) {
  const categories = {};
  for (const { category } of skills) {
    if (category) categories[category] = (categories[category] ?? 0) + 1;
  }
  return { total: skills.length, categories };
}

/** `html` with `counts` in its catalog-counts slot, which it must have. */
export function stampCatalogCounts(html, counts) {
  if (!CATALOG_SLOT.test(html)) throw new Error('index.html has no <script id="catalog-counts"> to hold the counts');
  // "<" escaped, so no value can close the script element early.
  const json = JSON.stringify(counts).replace(/</g, "\\u003c");
  return html.replace(CATALOG_SLOT, (_, open, close) => open + json + close);
}
