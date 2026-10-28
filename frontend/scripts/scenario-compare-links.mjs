/**
 * Head-to-head comparison links on the /best/ pages (2026-10-28).
 *
 * Ten of the eleven /compare/ URLs had no Google impression in 90 days, and no /best/
 * page linked to any of them: they were reachable only through the /compare/ index and
 * the sitemap. A scenario page now links every comparison that has one of its own
 * projects on either side, so the links only appear where a reader would want them.
 */
import { readFileSync } from "fs";
import { esc } from "./shared-utils.mjs";

const PAIRS = JSON.parse(readFileSync(new URL("./comparison-pairs.json", import.meta.url), "utf8"));

const repoName = (fullName) => fullName.split("/").pop();

// The pair's first keyword is the query its page targets ("claude code vs claude skills");
// the bare repo names can say less ("claude-code vs skills").
const label = (p) => p.keywords?.[0] || `${repoName(p.a)} vs ${repoName(p.b)}`;

/** The comparisons with one of these skills on either side, in comparison-pairs.json order. */
export function comparisonsFor(skills) {
  const names = new Set(skills.map((s) => (s.repo_full_name || "").toLowerCase()));
  return PAIRS.filter((p) => names.has(p.a.toLowerCase()) || names.has(p.b.toLowerCase()));
}

/** The section listing them, or "" when none of the page's projects is compared. */
export function comparisonsHtml(skills) {
  const pairs = comparisonsFor(skills);
  if (!pairs.length) return "";
  const links = pairs
    .map((p) => `<a href="/compare/${esc(p.slug)}/" class="bp-related-tag">${esc(label(p))}</a>`)
    .join("\n        ");
  return `<section style="margin-top:32px">
        <h2 class="bp-section-title" style="font-size:18px" data-zh="正面对比" data-en="Head-to-head comparisons">Head-to-head comparisons</h2>
        <div class="bp-related">
        ${links}
        </div>
      </section>`;
}
