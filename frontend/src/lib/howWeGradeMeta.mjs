/**
 * Where /how-we-grade/ lives, its title and meta description, and the label of the
 * links that point at it. Shared by the static generator
 * (scripts/generate-how-we-grade-page.mjs: what non-JS crawlers and AI bots read), the
 * React page (src/pages/HowWeGradePage.tsx: what Google indexes, since it renders JS)
 * and the sitemap, so the two versions of the page can never disagree.
 *
 * Kept apart from the page text (howWeGradeContent.mjs): the footer and the security
 * badge import this file, and they ship on every page.
 */

export const HOW_WE_GRADE_PATH = "/how-we-grade/";
export const HOW_WE_GRADE_URL = `https://agentskillshub.top${HOW_WE_GRADE_PATH}`;
/** Anchor of the section that explains each grade; the badge links there. */
export const GRADES_ANCHOR = "the-grades";

/** First published. */
export const HOW_WE_GRADE_PUBLISHED = "2026-10-22";
/**
 * The day the text was last checked against the scanner and scorers. Shown on the page
 * and used as the Article dateModified, which the sitemap reads as lastmod: bump it
 * whenever the text changes, never on a rebuild.
 */
export const HOW_WE_GRADE_UPDATED = "2026-10-22";

export const HOW_WE_GRADE_META = {
  en: {
    title: "How we grade skills: security grades and quality scores | Agent Skills Hub",
    description:
      "The 42 rules behind every Agent Skills Hub security grade, what Safe, Caution, Unsafe, Reject and Unaudited mean, the five source tiers and known limits.",
  },
  zh: {
    title: "我们怎么给 skill 评级：安全评级与质量分 | Agent Skills Hub",
    description:
      "Agent Skills Hub 每个安全评级背后的 42 条规则，Safe、Caution、Unsafe、Reject、Unaudited 各是什么意思，五档来源分级，以及已知局限。",
  },
};

/** Text of the small links to the page (footer, security badge, analyzer). */
export const HOW_WE_GRADE_LINK = { en: "How we grade", zh: "评级方法" };
