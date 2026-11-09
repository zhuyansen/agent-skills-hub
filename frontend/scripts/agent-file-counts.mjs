/**
 * The catalog numbers in the two files written for AI agents, dist/llms.txt and dist/skill.md,
 * copied from the numbers this build has just stamped on the home page (home-counts.mjs), so an
 * agent reads the same figures a person sees. Until 2026-11-09 both files were hand-written and
 * months behind: llms.txt said 186,000+ skills and 24,000+ graded while the home page said
 * 267,000+ and 132,000+, and skill.md put the CLI's catalog at ~20K when it held 49,747.
 *
 * Only the sentences listed below change, and each must appear exactly once. A reworded sentence
 * stops the build instead of shipping a file with some numbers updated and others stale.
 */

const THOUSAND = 1000;

/** The home page markers this module reads; home-counts.mjs writes them. */
const REQUIRED = ["total", "graded", "graded-over-100", "graded-over-1000"];

const MARKER = /<span data-count="([^"]+)">([^<]*)<\/span>/g;

/** The text of each data-count marker on the built home page, e.g. { total: "267,000+", … }. */
export function homeCounts(html) {
  const counts = {};
  for (const [, key, text] of html.matchAll(MARKER)) counts[key] ??= text;
  const missing = REQUIRED.filter((key) => !counts[key]);
  if (missing.length) throw new Error(`home page has no data-count for ${missing.join(", ")}`);
  return counts;
}

/** "267,000+" → "267K+", the short form skill.md uses. */
export function kiloPlus(text) {
  return `${Math.floor(Number(text.replace(/\D/g, "")) / THOUSAND)}K+`;
}

/** "132,000+" → "132K", for "~132K" in skill.md. */
export function kilo(text) {
  return kiloPlus(text).slice(0, -1);
}

/** 49747 → "50K": the CLI catalog size, which skill.md gives as an approximation. */
export function aboutKilo(n) {
  return `${Math.round(n / THOUSAND)}K`;
}

/**
 * Each rule is a sentence with two capture groups around one number: the text before it and the
 * text after it. `value` is what the number becomes.
 */
export function llmsRules(counts) {
  return [
    { pattern: /(Directory of )[\d,]+\+( open-source)/, value: counts.total },
    { pattern: /(of which )[\d,]+\+( carry a rule-based security grade)/, value: counts.graded },
    { pattern: /(including )\d+%( of skills over 100 stars)/, value: counts["graded-over-100"] },
    { pattern: /(stars and )\d+%( over 1,000)/, value: counts["graded-over-1000"] },
  ];
}

/** `indexCount` is the number of skills in the CLI's search index (search-index-meta.json). */
export function skillMdRules(counts, indexCount) {
  return [
    { pattern: /( )\d+K\+( indexed skills)/, value: kiloPlus(counts.total) },
    { pattern: /(of which ~)\d+K( carry a \*\*security grade\*\*)/, value: kilo(counts.graded) },
    { pattern: /(\(including )\d+%( of skills over 100 stars\))/, value: counts["graded-over-100"] },
    { pattern: /(catalog of ~)\d+K( skills locally)/, value: aboutKilo(indexCount) },
    { pattern: /(holds the ~)\d+K( with stars ≥ )/, value: aboutKilo(indexCount) },
  ];
}

/** `text` with each rule's number replaced. Throws when a rule's sentence is missing or repeated. */
export function stampRules(text, rules, file) {
  return rules.reduce((out, { pattern, value }) => {
    const hits = out.match(new RegExp(pattern.source, "g"))?.length ?? 0;
    if (hits !== 1) throw new Error(`${file}: expected the sentence /${pattern.source}/ once, found it ${hits} times`);
    return out.replace(pattern, (_, before, after) => `${before}${value}${after}`);
  }, text);
}
