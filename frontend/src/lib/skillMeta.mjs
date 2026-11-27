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
 *
 * 2026-10-31: the title leads with the repo's own name, "<repo> by <owner>: ...".
 * From 10-02 to 10-29 skill pages averaged position 6-9 with a 1.27% click-through
 * rate (253 clicks on 19,968 impressions), and queries written as owner/repo were 5%
 * of their impressions: people search the name, and "owner/repo:" read like a path.
 */
import { brandedName } from "./repoBrand.mjs";
import { RULE_COUNT } from "./howWeGradeMeta.mjs";

/** What a results page shows before cutting (~580px, about 60 Latin characters); a CJK
 *  character takes about two Latin widths. 68 until 2026-11-19, when the OpenSEO audit found
 *  989 skill titles at 61-70 that Google would cut mid-word. */
export const TITLE_MAX_WIDTH = 60;
/** The h1 is not cut by a results page; this only keeps it readable. */
export const HEADING_MAX_WIDTH = 110;
/** Used when the description gives nothing usable, and for deleted repos. */
export const TITLE_FALLBACK = "what it is & alternatives";
/** What a results page shows of a meta description (~155 characters). */
export const DESCRIPTION_LIMIT = 155;

/** A clause narrower than this reads as a fragment. */
const MIN_CLAUSE_WIDTH = 12;
/** Long repo names still get a short clause; the results page cuts the rest. */
const MIN_CLAUSE_BUDGET = 16;
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
const WORD_JOINER = /[-/'’]/;
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

/** True when cutting between `head` and `tail` would split a Latin word or compound ("AI-looking", "CI/CD", "don't"). */
function splitsLatinWord(head, tail) {
  const last = head.slice(-1);
  const next = tail.charAt(0);
  const afterNext = tail.charAt(1);
  return (
    (LATIN_WORD_CHAR.test(last) && LATIN_WORD_CHAR.test(next)) ||
    (WORD_JOINER.test(last) && LATIN_WORD_CHAR.test(next)) ||
    (LATIN_WORD_CHAR.test(last) && WORD_JOINER.test(next) && LATIN_WORD_CHAR.test(afterNext))
  );
}

function cutPoint(head, tail, budget) {
  const atBreak = Math.max(...PHRASE_BREAKS.map((b) => head.lastIndexOf(b)));
  const keep = Math.max(MIN_CLAUSE_WIDTH, budget * PHRASE_KEEP_RATIO);
  if (atBreak > 0 && displayWidth(head.slice(0, atBreak)) >= keep) return atBreak;
  // Back up only when the cut would split a Latin word or compound; CJK text can end at any character.
  const atSpace = head.lastIndexOf(" ");
  return splitsLatinWord(head, tail) && atSpace > 0 ? atSpace : head.length;
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
  return tidyEnd(head.slice(0, cutPoint(head, lean.slice(head.length), budget)).replace(UNCLOSED_PAREN, ""));
}

/** "theclaymethod/unslop" -> "unslop by theclaymethod": the name people search for comes first. */
// 2026-11-18 (OpenSEO audit, 1,000 skill titles over 60): 94% ran 61–68, inside the budget
// above; the 6% beyond it were long repo names, where " by <owner>" pushed the minimum clause
// past the results page ("datamodel-code-generator by datamodel-code-generator: …", 81).
// The owner goes when it repeats the repo name or leaves the clause no room.
// A repo named only for its kind ("skills", "mcp") leads with its brand instead: "Remotion
// Skills", not "skills by remotion-dev" (see repoBrand.mjs).
function titleHead(repoFullName) {
  const branded = brandedName(repoFullName);
  if (branded) return branded;
  const [owner, repo] = repoFullName.split("/");
  if (!repo) return repoFullName;
  const full = `${repo} by ${owner}`;
  const crowded = displayWidth(`${full}: `) + MIN_CLAUSE_BUDGET > TITLE_MAX_WIDTH;
  return owner.toLowerCase() === repo.toLowerCase() || crowded ? repo : full;
}

/** Below this display width (~70 Latin chars), OpenSEO flags a meta description as too short.
 *  Measured by display width so CJK descriptions (50-65 chars ≈ 100-130 width) are left alone. */
export const DESCRIPTION_MIN_WIDTH = 70;
const VALID_GRADES = new Set(["safe", "caution", "unsafe", "reject"]);

/** Fit an identifier (repo name or owner/repo) to `budget` display width, preferring a separator break. */
export function fitName(name, budget) {
  if (displayWidth(name) <= budget) return name;
  const head = prefixWithin(name, Math.max(budget - 1, 1));
  const sep = Math.max(head.lastIndexOf("-"), head.lastIndexOf("_"), head.lastIndexOf(" "), head.lastIndexOf("/"));
  const cut = sep > 0 && displayWidth(head.slice(0, sep)) >= budget * 0.6 ? head.slice(0, sep) : head;
  return `${cut.replace(/[-_\s/]+$/, "")}…`;
}

/** "<repo> by <owner>: <description clause>", or the fallback when the description gives nothing usable. */
export function skillTitle(repoFullName, repoName, description, fallback = TITLE_FALLBACK) {
  const head = titleHead(repoFullName);
  const remaining = TITLE_MAX_WIDTH - displayWidth(`${head}: `);
  if (remaining >= MIN_CLAUSE_WIDTH) {
    const clause = fitClause(cleanDescription(description, repoName), remaining);
    if (displayWidth(clause) >= MIN_CLAUSE_WIDTH && !(brandedName(repoFullName) && repeatsHead(clause, head))) return `${head}: ${clause}`;
  }
  return fallbackTitle(head, fallback);
}

// Words a description can add to a brand's name without saying anything ("Agent Skills").
const FILLER_WORDS = new Set(["a", "an", "the", "of", "for", "and", "official", "agent", "agents", "skill", "skills",
  "collection", "repository", "repo"]);

/** "Remotion Skills: Agent Skills" says the name twice; the fallback says what the page has. */
function repeatsHead(clause, head) {
  if (/[^\x00-\u024f\s]/.test(clause)) return false; // CJK and other scripts: the check reads Latin words only
  const named = new Set(head.toLowerCase().split(/\s+/));
  const words = clause.toLowerCase().match(/[a-z0-9.]+/g) || [];
  return words.length > 0 && words.every((w) => named.has(w) || FILLER_WORDS.has(w));
}

/** "<head>: what it is & alternatives", or ": alternatives" when that would run past the
 *  results page: 469 skill titles did, with no usable description (scan of 2026-11-19).
 *  Ultra-long repo names drop the suffix and cap at TITLE_MAX_WIDTH. */
export function fallbackTitle(head, fallback = TITLE_FALLBACK) {
  const full = `${head}: ${fallback}`;
  if (displayWidth(full) <= TITLE_MAX_WIDTH) return full;
  const short = `${head}: alternatives`;
  if (displayWidth(short) <= TITLE_MAX_WIDTH) return short;
  return fitName(head, TITLE_MAX_WIDTH);
}

/** The h1 of a repo named only for its kind: "Remotion Skills (remotion-dev/skills)", then
 *  its description unless that only repeats the name. null for every other repo. */
export function brandedHeading(repoFullName, repoName, description) {
  const branded = brandedName(repoFullName);
  if (!branded) return null;
  const head = `${branded} (${repoFullName})`;
  const clause = headingClause(repoName, description);
  return clause && !repeatsHead(clause, branded) ? `${head}: ${clause}` : head;
}

/** The h1 clause from the same description: all of it when it fits, else its first sentence. */
export function headingClause(repoName, description) {
  const clean = cleanDescription(description, repoName);
  const end = clean.search(SENTENCE_END);
  const first = end > 0 ? clean.slice(0, end) : clean;
  const clause = fitClause(displayWidth(clean) <= HEADING_MAX_WIDTH ? clean : first, HEADING_MAX_WIDTH);
  return displayWidth(clause) >= MIN_CLAUSE_WIDTH ? clause : "";
}

/** The first `n` UTF-16 units, one fewer if the cut would split an emoji (it left a "" in snippets). */
function cutUnits(text, n) {
  const last = text.charCodeAt(n - 1);
  return last >= 0xd800 && last <= 0xdbff ? text.slice(0, n - 1) : text.slice(0, n);
}

const fitsDesc = (text, limit = DESCRIPTION_LIMIT) => text.length <= limit && displayWidth(text) <= limit;

/** Trim a description body to `budget` (both chars and display width) on a clean word boundary, emoji-safe. */
function trimDescription(text, budget) {
  if (fitsDesc(text, budget)) return text;
  if (budget <= 1) return "";
  let head = prefixWithin(text, budget - 1);
  if (head.length > budget - 1) head = cutUnits(head, budget - 1);
  if (splitsLatinWord(head, text.slice(head.length))) {
    const atSpace = head.lastIndexOf(" ");
    if (atSpace > 0) head = head.slice(0, atSpace);
  }
  const cleaned = head.replace(TRAILING, "");
  return cleaned ? `${cleaned}…` : "";
}

/**
 * Meta description for a live repo: leads with our independent security audit verdict
 * (`[SAFE · 44-rule audit]`) rather than raw `git clone` / install commands, then what the
 * repo does (plain-text sanitized), then setup & alternatives. Kept within DESCRIPTION_LIMIT
 * (both length and display width) and padded above DESCRIPTION_MIN_WIDTH when short.
 */
export function skillDescription(repoName, description, installs = [], meta = {}) {
  const rawGrade = typeof meta?.grade === "string" ? meta.grade.toLowerCase() : "";
  const grade = VALID_GRADES.has(rawGrade) ? rawGrade.toUpperCase() : "";
  const q = typeof meta?.quality === "number" && Number.isFinite(meta.quality) ? Math.round(meta.quality) : null;
  const hasInstall = typeof meta?.hasInstall === "boolean" ? meta.hasInstall : Array.isArray(installs) && installs.length > 0;

  const name = (repoName || "").trim();
  const baseName = name.includes("/") ? name.slice(name.lastIndexOf("/") + 1) : name;
  const clean = cleanDescription(description, baseName);
  const body = clean
    ? (name ? `${name}: ${clean}.` : `${clean}.`)
    : (name ? `${name}, an open-source agent tool.` : "An open-source agent tool.");
  const minBodyRoom = Math.max(displayWidth(name) + 24, 48);

  let out = "";
  if (grade) {
    const auditPrefix = `[${grade} · ${RULE_COUNT}-rule audit] `;
    const richPrefixes = q !== null
      ? [`[${grade} · ${q}/100 · ${RULE_COUNT}-rule audit] `, auditPrefix]
      : [auditPrefix];
    const compactPrefixes = q !== null ? [`[${grade} · ${q}/100] `, `[${grade}] `] : [`[${grade}] `];
    const suffix = hasInstall ? " Setup & alternatives." : " Alternatives compared.";

    for (const p of richPrefixes) {
      if (fitsDesc(`${p}${body}${suffix}`)) { out = `${p}${body}${suffix}`; break; }
    }
    if (!out) {
      for (const p of richPrefixes) {
        if (fitsDesc(`${p}${body}`)) { out = `${p}${body}`; break; }
      }
    }
    if (!out) {
      const budgetWithSuffix = DESCRIPTION_LIMIT - auditPrefix.length - suffix.length;
      if (budgetWithSuffix >= minBodyRoom) {
        const trimmed = trimDescription(body, budgetWithSuffix);
        if (trimmed) out = `${auditPrefix}${trimmed}${suffix}`;
      }
    }
    if (!out) {
      for (const p of [auditPrefix, ...compactPrefixes]) {
        const budget = DESCRIPTION_LIMIT - p.length;
        if (budget >= Math.max(displayWidth(name) + 12, 36) || p === `[${grade}] `) {
          const trimmed = trimDescription(body, budget);
          out = trimmed ? `${p}${trimmed}` : p.trim();
          break;
        }
      }
    }
  } else {
    const primarySuffix = hasInstall
      ? " Independent security audit, setup & alternatives."
      : " Independent security audit & alternatives.";
    const shortSuffix = hasInstall ? " Setup & alternatives." : " Alternatives compared.";

    if (fitsDesc(`${body}${primarySuffix}`)) out = `${body}${primarySuffix}`;
    else if (fitsDesc(`${body}${shortSuffix}`)) out = `${body}${shortSuffix}`;
    else if (fitsDesc(body)) out = body;
    else {
      const budgetPrimary = DESCRIPTION_LIMIT - primarySuffix.length;
      const budgetShort = DESCRIPTION_LIMIT - shortSuffix.length;
      if (budgetPrimary >= minBodyRoom) out = `${trimDescription(body, budgetPrimary)}${primarySuffix}`;
      else if (budgetShort >= minBodyRoom) out = `${trimDescription(body, budgetShort)}${shortSuffix}`;
      else out = trimDescription(body, DESCRIPTION_LIMIT);
    }
  }

  if (displayWidth(out) < DESCRIPTION_MIN_WIDTH) {
    const pad = " Audited on Agent Skills Hub.";
    if (fitsDesc(`${out}${pad}`)) out += pad;
  }
  return out;
}
