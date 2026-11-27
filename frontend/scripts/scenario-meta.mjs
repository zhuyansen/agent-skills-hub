/**
 * Tested-verdict meta description builder for /best/<slug>/ pages.
 *
 * Replaces the uniform boilerplate prefix ("X tools, independently security-graded: ...")
 * that truncated before naming our hands-on #1 pick. Keeps every emitted description
 * strictly <= META_MAX (155 chars), trimmed cleanly at sentence or word boundaries.
 */
import { displayName } from "../src/lib/repoBrand.mjs";

export const META_MAX = 155;

function normalizeSpaces(text) {
  return String(text || "").replace(/\s+/g, " ").trim();
}

/**
 * Clamps text to <= max chars at a sentence or word boundary — never mid-word.
 */
export function clampMetaDesc(text, max = META_MAX) {
  const clean = normalizeSpaces(text);
  if (clean.length <= max) return clean;

  // Prefer keeping a complete leading sentence when it already uses most of the budget.
  const sentences = clean.split(/(?<=[.!?])\s+/);
  let built = "";
  for (const s of sentences) {
    const next = built ? `${built} ${s}` : s;
    if (next.length <= max) built = next;
    else break;
  }
  if (built && built.length >= Math.floor(max * 0.65)) return built;

  // Otherwise cut cleanly at a word boundary, peel dangling punctuation/open parens, and add ellipsis.
  let cut = clean.slice(0, max - 1);
  const lastSpace = cut.lastIndexOf(" ");
  if (lastSpace > 20) cut = cut.slice(0, lastSpace);
  cut = cut.replace(/[\s,;:(\-\u2013\u2014]+$/, "").trim();
  if (!cut) return clean.slice(0, max);
  if (/[.!?]$/.test(cut)) return cut;
  return `${cut}…`;
}

/** Short display name for a verdict pick repo (e.g. "hugohe3/ppt-master" -> "ppt-master",
 *  "anthropics/skills" -> "Anthropic Skills"). */
function pickLabel(repoFullName) {
  const raw = String(repoFullName || "").trim();
  if (!raw) return "";
  const short = raw.includes("/") ? raw.split("/").pop() : raw;
  return displayName(raw, short);
}

/** Formats a verdict role string for inline parenthetical use, stripping nested parens and trailing dot. */
function formatRole(roleRaw) {
  let r = normalizeSpaces(roleRaw)
    .replace(/\s*\([^)]*\)/g, "")
    .replace(/\.+$/, "")
    .trim();
  if (!r) return "";
  // Lowercase standard English lead-in words inside parentheses ("For ..." -> "for ..."),
  // while preserving proper nouns/acronyms ("Claude", "MCP", "SEO").
  r = r.replace(/^(For|To|If|Install|Developers|Teams|Anyone)\b/, (m) => m.toLowerCase());
  return r;
}

/** Extracts a concise, high-signal finding clause from verdict.answer[0] that fits `budget`. */
function summarizeAnswer(answerRaw, budget, { allowEllipsis = true } = {}) {
  const clean = normalizeSpaces(answerRaw);
  if (!clean || budget < 24) return "";

  const sentences = clean.split(/(?<=[.!?])\s+/).filter(Boolean);
  // Skip redundant "We had N ... / We gave N ..." setup opener when the actual finding follows.
  const primary =
    sentences.length > 1 && /^We\s+(had|gave|tested|ran)\b/i.test(sentences[0])
      ? sentences[1]
      : sentences[0];

  const stripped = primary.replace(/[.!?]+$/, "").trim();
  if (stripped.length <= budget) return stripped;

  // Try complete leading clauses separated by "; " or ", so " or ": " or ", ".
  const clauseSplits = [
    stripped.split(/;\s+/)[0],
    stripped.split(/,\s+so\s+/i)[0],
    stripped.split(/:\s+/)[0],
    stripped.split(/,\s+/)[0],
  ]
    .map((c) => c.trim())
    .filter((c) => c.length >= 24 && c.length <= budget);
  if (clauseSplits.length) {
    // Pick the longest clean clause that fits.
    clauseSplits.sort((a, b) => b.length - a.length);
    return clauseSplits[0];
  }

  return allowEllipsis ? clampMetaDesc(stripped, budget).replace(/\.+$/, "") : "";
}

function splitTopNames(topNames) {
  if (Array.isArray(topNames)) {
    return topNames.map((n) => normalizeSpaces(n)).filter(Boolean);
  }
  return normalizeSpaces(topNames)
    .split(/,\s*/)
    .map((n) => n.trim())
    .filter(Boolean);
}

/**
 * Builds a high-signal, <= 155-character meta description for a /best/<slug>/ page.
 */
export function buildScenarioMetaDesc({
  scenario = {},
  descSubject = "",
  itemCount = 0,
  canClaim = false,
  safeN = 0,
  flaggedN = 0,
  ruleCount = 44,
  topNames = "",
  run = null,
  year = new Date().getFullYear(),
} = {}) {
  // 1. Explicit per-scenario override wins.
  const explicit = normalizeSpaces(scenario?.meta_description);
  if (explicit) return clampMetaDesc(explicit, META_MAX);

  const subject = normalizeSpaces(descSubject || scenario?.serp_subject || scenario?.title || "AI skills");
  const testedCount = run ? Object.keys(run.runs || {}).length : 0;
  const securityFull = canClaim
    ? `${safeN} SAFE${flaggedN ? `, ${flaggedN} flagged` : ""} across ${ruleCount} rules.`
    : "";
  const securityMed = canClaim
    ? `${safeN} SAFE${flaggedN ? `, ${flaggedN} flagged` : ""} (${ruleCount} rules).`
    : "";
  const securityShort = canClaim
    ? `${safeN} SAFE${flaggedN ? `, ${flaggedN} flagged` : ""}.`
    : "";

  // 2. Hands-on tested scenario with an explicit #1 verdict pick.
  const firstPick = run?.verdict?.picks?.[0];
  if (firstPick?.repo && testedCount > 0) {
    const topPick = pickLabel(firstPick.repo);
    const roleShort = formatRole(firstPick.role?.[0]);
    const headOf =
      itemCount > testedCount
        ? `Tested ${testedCount} of ${itemCount} ${subject} (${year}):`
        : `Tested ${testedCount} ${subject} (${year}):`;
    const headCompact = `Tested ${testedCount} ${subject} (${year}):`;

    const candidates = [];
    if (roleShort) {
      if (canClaim) {
        candidates.push(
          `${headOf} #1 ${topPick} (${roleShort}). ${securityFull}`,
          `${headOf} #1 ${topPick} (${roleShort}). ${securityMed}`,
          `${headOf} #1 ${topPick} (${roleShort}). ${securityShort}`,
          `${headCompact} #1 ${topPick} (${roleShort}). ${securityMed}`,
          `${headCompact} #1 ${topPick} (${roleShort}). ${securityShort}`,
        );
      } else {
        candidates.push(
          `${headOf} #1 ${topPick} (${roleShort}).`,
          `${headCompact} #1 ${topPick} (${roleShort}).`,
        );
      }
    }
    if (canClaim) {
      candidates.push(
        `${headOf} #1 ${topPick}. ${securityFull}`,
        `${headOf} #1 ${topPick}. ${securityMed}`,
        `${headOf} #1 ${topPick}. ${securityShort}`,
        `${headCompact} #1 ${topPick}. ${securityMed}`,
        `${headCompact} #1 ${topPick}. ${securityShort}`,
      );
    }
    if (roleShort) {
      candidates.push(
        `${headOf} #1 ${topPick} (${roleShort}).`,
        `${headCompact} #1 ${topPick} (${roleShort}).`,
      );
    }
    candidates.push(`${headOf} #1 ${topPick}.`, `${headCompact} #1 ${topPick}.`);

    const fit = candidates.map(normalizeSpaces).find((c) => c.length <= META_MAX);
    if (fit) return fit;
    return clampMetaDesc(candidates[candidates.length - 1], META_MAX);
  }

  // 3. Hands-on tested scenario with a narrative verdict.answer (e.g. image-generation).
  const answerText = run?.verdict?.answer?.[0];
  if (answerText && testedCount > 0) {
    const prefix = `Hands-on tested ${testedCount} ${subject} (${year}): `;
    const tails = canClaim
      ? [
          ` ${safeN} of ${itemCount} rated SAFE across ${ruleCount} rules.`,
          ` ${safeN} of ${itemCount} rated SAFE (${ruleCount} rules).`,
          ` ${safeN} of ${itemCount} SAFE (${ruleCount} rules).`,
          ` ${safeN}/${itemCount} SAFE.`,
          "",
        ]
      : [""];

    for (const allowEllipsis of [false, true]) {
      for (const tail of tails) {
        const budget = META_MAX - prefix.length - tail.length - 1; // -1 for period after summary
        if (budget < 32) continue;
        const summary = summarizeAnswer(answerText, budget, { allowEllipsis });
        if (!summary) continue;
        const punct = /[.!?…]$/.test(summary) ? "" : ".";
        const full = normalizeSpaces(`${prefix}${summary}${punct}${tail}`);
        if (full.length <= META_MAX) return full;
      }
    }

    return clampMetaDesc(`${prefix}${answerText}`, META_MAX);
  }

  const names = splitTopNames(topNames);

  // 4. Security-graded scenario without hands-on runs.
  if (canClaim) {
    const base = `${itemCount} ${subject} (${year}): ${safeN} SAFE${flaggedN ? `, ${flaggedN} flagged` : ""} (${ruleCount} rules).`;
    const candidates = [];
    if (names.length >= 3) candidates.push(`${base} Top picks: ${names.slice(0, 3).join(", ")}.`);
    if (names.length >= 2) candidates.push(`${base} Top picks: ${names.slice(0, 2).join(", ")}.`);
    if (names.length >= 1) candidates.push(`${base} Top pick: ${names[0]}.`);
    candidates.push(
      `${itemCount} ${subject} (${year}): ${safeN} SAFE${flaggedN ? `, ${flaggedN} flagged` : ""} across ${ruleCount} rules.`,
      base,
    );
    const fit = candidates.map(normalizeSpaces).find((c) => c.length <= META_MAX);
    if (fit) return fit;
    return clampMetaDesc(base, META_MAX);
  }

  // 5. Fallback for ungraded scenarios without runs.
  const candidates = [];
  if (names.length >= 3) {
    candidates.push(
      `${itemCount} open-source ${subject} compared (${year}): ${names.slice(0, 3).join(", ")}. Quality-scored and refreshed every 8h.`,
    );
  }
  if (names.length >= 2) {
    candidates.push(
      `${itemCount} open-source ${subject} compared (${year}): ${names.slice(0, 2).join(", ")}. Quality-scored and refreshed every 8h.`,
    );
  }
  if (names.length >= 1) {
    candidates.push(
      `${itemCount} open-source ${subject} compared (${year}): ${names[0]}. Quality-scored and refreshed every 8h.`,
      `${itemCount} open-source ${subject} compared (${year}): ${names[0]}. Refreshed every 8h.`,
    );
  }
  candidates.push(
    `${itemCount} open-source ${subject} compared (${year}). Quality-scored and refreshed every 8h.`,
    `${itemCount} open-source ${subject} compared (${year}).`,
  );
  const fit = candidates.map(normalizeSpaces).find((c) => c.length <= META_MAX);
  if (fit) return fit;
  return clampMetaDesc(candidates[candidates.length - 1], META_MAX);
}
