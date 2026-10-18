/**
 * Title and meta description for a /skill/<owner>/<repo>/ page, shared by the
 * static generator (scripts/generate-skill-pages.mjs: what non-JS crawlers and AI
 * bots read) and the React page (src/pages/SkillDetailPage.tsx), which replaces
 * the static markup once JS runs. Google renders JS, so what it indexes is the
 * React version; both must come from these functions.
 *
 * 2026-10-18: Google's title-link guide (checked 2026-10-17) warns against long
 * boilerplate titles where only a small part changes. Every skill page read
 * "<owner/repo>: what it is, how to install & alternatives" (static) or
 * "<owner/repo> — security grade & quality score | Agent Skills Hub" (React).
 * The part that varies is now the repo's own one-line description, cleaned and
 * cut to what a results page shows.
 */

/** Rough results-page budget (~600px); a CJK character takes about two Latin widths. */
export const TITLE_MAX_WIDTH = 65;
/** The h1 is not cut by a results page; this only keeps it readable. */
export const HEADING_MAX_WIDTH = 110;
/** Used when the description gives nothing usable, and for deleted repos. */
export const TITLE_FALLBACK = "what it is & alternatives";
/** What a results page shows of a meta description (~155 characters). */
export const DESCRIPTION_LIMIT = 155;

/** A clause narrower than this reads as a fragment. */
const MIN_CLAUSE_WIDTH = 12;
/** Long repo names still get a short clause; the results page cuts the rest. */
const MIN_CLAUSE_BUDGET = 28;
/** A phrase break is only worth cutting at if it keeps this share of the budget. */
const PHRASE_KEEP_RATIO = 0.5;
/** How many dangling words to drop from the end at most ("... that lives in your"). */
const MAX_DANGLING_TRIMS = 3;
/** A cut that leaves "... tool that lives" drops the half relative clause. */
const HALF_CLAUSE = /\s+(?:that|which|who|where)(?:\s+\S+){0,2}$/iu;
const LOWERCASE_LEAD = /^[a-z][a-z-]*\b/;
const LEADING_ARTICLE = /^(?:a|an|the)\s/;
const PARENTHETICAL = /\s*[(（][^()（）]*[)）]/gu;
const UNCLOSED_PAREN = /\s*[(（][^)）]*$/u;
const SENTENCE_END = /[.!?。！？](?:\s|$)/u;
const WIDE_CHAR = /[ᄀ-ᅟ⺀-꓏가-힣豈-﫿︰-﹏＀-｠￠-￦]/u;
const LATIN_WORD_CHAR = /[A-Za-z0-9À-ɏ]/u;
const TRAILING = /[\s.,;:!?|\-–—。，；：、！？]+$/u;
const DANGLING =
  /\s+(?:and|or|for|with|to|of|the|a|an|in|on|at|as|by|via|from|into|using|your|its|their|that|which|who|is|are|&|\+)$/iu;
// No plain ", ": in English it mostly separates list items, and cutting there drops half a list.
const PHRASE_BREAKS = [" - ", " – ", " — ", "——", " | ", " (", ". ", "; ", ": ", "，", "；", "：", "。", "、", "！", "？", "｜"];

export function displayWidth(text) {
  let width = 0;
  for (const ch of text) width += WIDE_CHAR.test(ch) ? 2 : 1;
  return width;
}

function escapeRegExp(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** The description as plain text: no markup, links, quotes or emoji. */
function plainText(description) {
  return description
    .replace(/<[^>]+>/g, " ")
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/https?:\/\/\S+/g, " ")
    .replace(/:[a-z0-9_+-]+:/gi, " ")
    .replace(/[\p{Extended_Pictographic}\u{FE0F}\u{200D}]/gu, " ")
    .replace(/[`*"“”]/g, "")
    .replace(/【([^】]*)】/g, "$1，")
    .replace(/^(?:#+\s+|>\s*)/, "")
    .replace(/\s+/g, " ")
    .trim();
}

/** The description as plain text, without a leading repeat of the repo's own name. */
export function cleanDescription(description, repoName) {
  if (!description) return "";
  const plain = plainText(description);
  if (!repoName) return plain.replace(TRAILING, "");
  // "versus-incident" also matches "Versus Incident" and "Versus_Incident"
  const name = escapeRegExp(repoName).replace(/[-_\s]+/g, "[-_\\s]?");
  const tagline = new RegExp(`^${name}\\s*[:|\\-–—：｜]\\s*`, "iu");
  const sentence = new RegExp(`^${name}\\s+(?:is|are)\\s+(?:(?:an?|the)\\s+)?`, "iu");
  const withoutTagline = plain.replace(tagline, "");
  const out = withoutTagline !== plain ? withoutTagline : capitalizeLead(plain.replace(sentence, ""), plain);
  const lead = LEADING_ARTICLE.test(out) ? out.charAt(0).toUpperCase() + out.slice(1) : out;
  return lead.replace(TRAILING, "");
}

/** "Foo is a self-hosted agent" loses "Foo is a"; what is left starts a title, so capitalise it. */
function capitalizeLead(text, original) {
  if (text === original || !LOWERCASE_LEAD.test(text)) return text;
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function prefixWithin(text, budget) {
  let width = 0;
  let out = "";
  for (const ch of text) {
    width += WIDE_CHAR.test(ch) ? 2 : 1;
    if (width > budget) break;
    out += ch;
  }
  return out;
}

function cutPoint(head, nextChar, budget) {
  const atBreak = Math.max(...PHRASE_BREAKS.map((b) => head.lastIndexOf(b)));
  const keep = Math.max(MIN_CLAUSE_WIDTH, budget * PHRASE_KEEP_RATIO);
  if (atBreak > 0 && displayWidth(head.slice(0, atBreak)) >= keep) return atBreak;
  // Back up only when the cut would split a Latin word; CJK text can end at any character.
  const splitsWord = LATIN_WORD_CHAR.test(head.slice(-1)) && LATIN_WORD_CHAR.test(nextChar);
  const atSpace = head.lastIndexOf(" ");
  return splitsWord && atSpace > 0 ? atSpace : head.length;
}

function tidyEnd(text) {
  let out = text.replace(TRAILING, "");
  for (let i = 0; i < MAX_DANGLING_TRIMS && DANGLING.test(out); i++) out = out.replace(DANGLING, "").replace(TRAILING, "");
  const whole = out.replace(HALF_CLAUSE, "");
  return displayWidth(whole) >= MIN_CLAUSE_WIDTH ? whole.replace(TRAILING, "") : out;
}

/** Cut a clause to `budget` display width at a phrase break, else a word break. Asides in brackets go first. */
export function fitClause(clause, budget) {
  if (displayWidth(clause) <= budget) return clause;
  const lean = clause.replace(PARENTHETICAL, "");
  if (displayWidth(lean) <= budget) return lean;
  const head = prefixWithin(lean, budget);
  return tidyEnd(head.slice(0, cutPoint(head, lean.charAt(head.length), budget)).replace(UNCLOSED_PAREN, ""));
}

/** "<owner/repo>: <description clause>", or the fallback when the description gives nothing usable. */
export function skillTitle(repoFullName, repoName, description, fallback = TITLE_FALLBACK) {
  const budget = Math.max(TITLE_MAX_WIDTH - displayWidth(`${repoFullName}: `), MIN_CLAUSE_BUDGET);
  const clause = fitClause(cleanDescription(description, repoName), budget);
  return `${repoFullName}: ${displayWidth(clause) >= MIN_CLAUSE_WIDTH ? clause : fallback}`;
}

/** The h1 clause from the same description: all of it when it fits, else its first sentence. */
export function headingClause(repoName, description) {
  const clean = cleanDescription(description, repoName);
  const end = clean.search(SENTENCE_END);
  const first = end > 0 ? clean.slice(0, end) : clean;
  const clause = fitClause(displayWidth(clean) <= HEADING_MAX_WIDTH ? clean : first, HEADING_MAX_WIDTH);
  return displayWidth(clause) >= MIN_CLAUSE_WIDTH ? clause : "";
}

/** The first `n` UTF-16 units, one fewer if the cut would split an emoji (it left a "�" in snippets). */
function cutUnits(text, n) {
  const last = text.charCodeAt(n - 1);
  return last >= 0xd800 && last <= 0xdbff ? text.slice(0, n - 1) : text.slice(0, n);
}

/**
 * Meta description for a live repo: what it is, then the install command when the
 * README gave one, then the alternatives the page compares, cut at what a results
 * page shows. The React page never sees the README, so it reuses the description the
 * pre-rendered page shipped with (src/lib/prerenderedMeta.ts) and only builds one
 * here, without the install command, after a client-side navigation.
 */
export function skillDescription(repoName, description, installs = []) {
  const what = description ? `${repoName}: ${description.trim().replace(/\.$/, "")}.` : `${repoName}, an open-source agent tool.`;
  const parts = [installs[0] ? ` Install: ${installs[0]}.` : "", " Alternatives compared."];
  let out = what.length > DESCRIPTION_LIMIT ? `${cutUnits(what, DESCRIPTION_LIMIT - 1).trim()}…` : what;
  for (const part of parts) if (part && out.length + part.length <= DESCRIPTION_LIMIT) out += part;
  return out;
}
