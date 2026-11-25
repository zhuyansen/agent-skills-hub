/**
 * Buyer-query aligned <title> builder for /best/<slug>/ pages.
 *
 * Leads with "Best ..." inside Google's 60-character display budget while keeping
 * the year and our unique differentiators (hands-on tested count, security-graded
 * count) whenever they fit.
 */

export const TITLE_MAX = 60;

// Subject nouns that read naturally right after "Best " without appending "Tools".
// Singular "Bot" ("Discord Bot") still wants "Tools"; plural "Bots" does not.
export const SUBJECT_NOUN =
  /\b(tools?|servers?|frameworks?|platforms?|integrations?|skills?|bots|alternatives|agents?)\b/i;

/**
 * Shortens a long raw scenario title to <= 34 chars at a word boundary, peeling
 * trailing conjunctions or stub words. `serp_subject` is kept as written.
 */
export function trimScenarioSubject(scenario) {
  if (scenario.serp_subject) return scenario.serp_subject.trim();
  const full = (scenario.title || "").trim();
  if (full.length <= 34) return full;
  let t = full.slice(0, 34);
  const space = t.lastIndexOf(" ");
  if (space > 0) t = t.slice(0, space);
  for (let i = 0; i < 4; i++) {
    const next = t
      .replace(/\s*[,&:+\-|]\s*$/, "")
      .replace(/\s+(and|or|for|with|the|a|an|ai|to|in|on|of)$/i, "");
    if (next === t) break;
    t = next;
  }
  return t.trim() || full.split(/[,:]/)[0].trim();
}

function clampWord(text, max) {
  if (text.length <= max) return text;
  let cut = text.slice(0, max);
  const space = cut.lastIndexOf(" ");
  if (space > 12) cut = cut.slice(0, space);
  return cut.replace(/\s*[,&:+\-|]\s*$/, "").trim();
}

/**
 * Builds a buyer-query aligned <title> within TITLE_MAX (60 chars).
 *
 * Examples:
 * - "Best Claude Code Skills (2026): 39 Tested, 792 Graded" (53)
 * - "Best PPT Skills for Codex & Claude Code (2026): 32 Tested" (57)
 * - "Best Claude Design Skills for Frontend & UI (2026)" (50)
 * - "Best Web Scraping Tools (2026): 10 Security-Graded" (50)
 */
export function buildScenarioTitle({
  scenario,
  itemCount = 0,
  canClaim = false,
  testedCount = 0,
  year = new Date().getFullYear(),
}) {
  const subject = trimScenarioSubject(scenario);
  const needsTools = !scenario.serp_subject && !SUBJECT_NOUN.test(subject);
  const bestSubject = needsTools ? `${subject} Tools` : subject;
  const bestBase = /^best\b/i.test(bestSubject) ? bestSubject : `Best ${bestSubject}`;

  const candidates = [];
  if (testedCount > 0 && canClaim) {
    candidates.push(
      `${bestBase} (${year}): ${testedCount} Tested, ${itemCount} Graded`,
      `${bestBase} (${year}): ${testedCount} Tested`,
      `${bestBase} (${year}): ${itemCount} Graded`,
      `${bestBase} (${year}): Graded`,
      `${bestBase} (${year})`,
      bestBase,
    );
  } else if (testedCount > 0) {
    candidates.push(
      `${bestBase} (${year}): ${testedCount} Tested`,
      `${bestBase} (${year}): ${itemCount} Compared`,
      `${bestBase} (${year})`,
      bestBase,
    );
  } else if (canClaim) {
    candidates.push(
      `${bestBase} (${year}): ${itemCount} Security-Graded`,
      `${bestBase} (${year}): ${itemCount} Graded`,
      `${bestBase} (${year}): Graded`,
      `${bestBase} (${year})`,
      bestBase,
    );
  } else {
    candidates.push(
      `${bestBase} (${year}): ${itemCount} Compared`,
      `${bestBase} (${year}): Compared`,
      `${bestBase} (${year})`,
      bestBase,
    );
  }

  candidates.push(`${subject} (${year})`, subject);

  const head =
    candidates.find((c) => c.length <= TITLE_MAX) || clampWord(bestBase, TITLE_MAX);
  const branded = `${head} | Agent Skills Hub`;
  return (branded.length <= TITLE_MAX ? branded : head).replace(/  +/g, " ").trim();
}
